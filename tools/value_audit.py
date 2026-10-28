#!/usr/bin/env python3
"""Read-only audit of raw SkillFit judgments; never calls a model or changes runs."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import statistics
import sys

COMMON_WEIGHTS = {"正确性": .55, "完整性": .30, "表达清晰": .15}
LEGACY_WEIGHTS = {"正确性": .40, "完整性": .25, "技能遵循": .20, "表达清晰": .15}
MODES = ("M1", "M2", "M4")
CONTRASTS = {"M2-M1": ("M2", "M1"), "M2-M4": ("M2", "M4")}


def family(model):
    """Keep historical bench.py family grouping; this is a naming heuristic."""
    name = model.lower()
    for prefix in ("glm", "deepseek", "kimi", "minimax", "hy", "step", "space"):
        if name.startswith(prefix):
            return prefix
    return name.split("@")[0].split("-")[0]


def number(value):
    return type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 5


def weighted(judgment, weights, strict=True):
    """Strict common score rejects incomplete/out-of-scale dimensions."""
    if strict and not all(number(judgment.get(key)) for key in weights):
        return None
    valid = [(judgment.get(key), weight) for key, weight in weights.items()
             if number(judgment.get(key))]
    return sum(value * weight for value, weight in valid) / sum(w for _, w in valid) if valid else None


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
    if not match:
        raise ValueError("missing_frontmatter")
    return {line.split(":", 1)[0].strip(): line.split(":", 1)[1].strip()
            for line in match.group(1).splitlines() if ":" in line}


def aggregate(judgments, field, judges):
    votes = defaultdict(list)
    for judge in judges:
        value = judgments[judge][field]
        if value is not None:
            votes[family(judge)].append(value)
    return statistics.median(statistics.mean(values) for values in votes.values()) if votes else None


def resolve_artifact(root, meta):
    """Use the mapped artifact; a relocated checkout may remap its runs/结果 suffix."""
    raw = Path(meta.get("file", ""))
    candidate = raw if raw.is_absolute() else root / raw
    if candidate.is_file() and candidate.resolve().is_relative_to(root):
        return candidate
    parts = raw.parts
    for directory in ("runs", "结果"):
        if directory in parts:
            suffix = parts[parts.index(directory) + 1:]
            for local_directory in (directory, "runs" if directory == "结果" else "结果"):
                candidate = root.joinpath(local_directory, *suffix)
                if candidate.is_file() and candidate.resolve().is_relative_to(root):
                    return candidate
    raise ValueError("artifact_missing_or_outside_root")


def stats(pairs):
    """Tasks get equal weight; trials describe within-task variability only."""
    by_task = defaultdict(list)
    for pair in pairs:
        by_task[pair["task"]].append(pair["delta"])
    tasks = []
    for task, values in sorted(by_task.items()):
        tasks.append({"task": task, "paired_trials": len(values),
                      "mean_delta": round(statistics.mean(values), 6),
                      "trial_sd": round(statistics.stdev(values), 6) if len(values) > 1 else None,
                      "range": [round(min(values), 6), round(max(values), 6)]})
    return {"status": "paired_observations_available" if pairs else "insufficient_evidence",
            "paired_samples": len(pairs), "tasks": len(tasks),
            "task_equal_mean_delta": round(statistics.mean(t["mean_delta"] for t in tasks), 6) if tasks else None,
            "within_task": tasks, "pairs": pairs,
            "confidence_interval": None,
            "uncertainty_note": "trial_sd 仅描述同任务重复运行的配对差波动；单次试验为 null。判官票不是独立试验，跨任务均值不附推断置信区间。"}


def audit(root, skills=None, models=None, min_judge_families=2):
    root = Path(root).resolve()
    if min_judge_families < 1:
        raise ValueError("min_judge_families must be positive")
    mapped, scored = Counter(), Counter()
    issues, cells, ambiguous, mapped_groups = [], {}, set(), set()
    mapping_files = sorted((root / "scoring").glob("*/映射表.json"))
    if skills:
        mapping_files = [p for p in mapping_files if p.parent.name in skills]

    def issue(kind, source):
        issues.append({"kind": kind, "source": str(source)})

    for mapping_file in mapping_files:
        skill = mapping_file.parent.name
        try:
            mapping = json.loads(mapping_file.read_text(encoding="utf-8"))
            if not isinstance(mapping, dict):
                raise ValueError("mapping_not_object")
        except (ValueError, OSError) as exc:
            issue("invalid_mapping", mapping_file.relative_to(root))
            continue
        for code, meta in mapping.items():
            source = f"scoring/{skill}/{code}"
            if not isinstance(meta, dict) or any(not isinstance(meta.get(k), str) or not meta[k]
                                                  for k in ("skill", "task", "model", "mode")):
                issue("invalid_mapping_metadata", source)
                continue
            if models and meta["model"] not in models:
                continue
            mode, model, task = meta["mode"], meta["model"], meta["task"]
            mapped[mode] += 1
            if mode not in MODES:
                continue
            mapped_groups.add((skill, model))
            if meta["skill"] != skill or Path(str(code)).name != code or code in (".", ".."):
                issue("mapping_identity_mismatch", source)
                continue
            try:
                artifact = resolve_artifact(root, meta)
                fm = frontmatter(artifact)
                expected = {"技能": skill, "任务": task, "模型": model, "模式": mode}
                if any(fm.get(k) != v for k, v in expected.items()):
                    raise ValueError("artifact_metadata_mismatch")
                if fm.get("状态") != "ok":
                    raise ValueError("artifact_not_ok")
                trial = int(fm["试验"])
                if trial < 1:
                    raise ValueError("invalid_trial")
            except (ValueError, KeyError, OSError) as exc:
                issue(str(exc) if isinstance(exc, ValueError) else "artifact_missing_trial_or_unreadable", source)
                continue
            judges, duplicate_judges = {}, set()
            for score_file in sorted((mapping_file.parent / code).glob("*.json")):
                if score_file.name == "断言.json" or score_file.name.endswith(".自评.json"):
                    continue
                try:
                    judgment = json.loads(score_file.read_text(encoding="utf-8"))
                    if not isinstance(judgment, dict):
                        raise ValueError("score_not_object")
                    judge = judgment.get("评分者")
                    if not isinstance(judge, str) or not judge:
                        raise ValueError("missing_judge")
                    if judgment.get("自评") or judge.split("@")[0] == model.split("@")[0]:
                        continue
                    common = weighted(judgment, COMMON_WEIGHTS)
                    if common is None or judgment.get("判定") == "INVALID":
                        raise ValueError("invalid_common_score")
                    if judge in judges:
                        duplicate_judges.add(judge)
                        issue("duplicate_judge", score_file.relative_to(root))
                    judges[judge] = {"common": common,
                                     "historical": weighted(judgment, COMMON_WEIGHTS if mode == "M1" else LEGACY_WEIGHTS, strict=False),
                                     "adherence": judgment.get("技能遵循") if number(judgment.get("技能遵循")) else None}
                except (ValueError, OSError):
                    issue("invalid_judgment", score_file.relative_to(root))
            for judge in duplicate_judges:
                judges.pop(judge, None)
            if not judges:
                issue("no_valid_external_judgments", source)
                continue
            scored[mode] += 1
            key = (skill, model, task, trial, mode)
            if key in cells:
                ambiguous.add(key)
                issue("duplicate_task_trial_mode", source)
            cells[key] = judges
    for key in ambiguous:
        cells.pop(key, None)

    groups = {key: {"slots": set(), "artifacts": defaultdict(list)} for key in mapped_groups}
    for (skill, model, task, trial, mode), judges in cells.items():
        groups[skill, model]["slots"].add((task, trial))
        groups[skill, model]["artifacts"][mode].append(judges)
    results = []
    # Include M2-only groups even when their files cannot be scored.
    for (skill, model), group in sorted(groups.items()):
        comparisons = {}
        for name, (left_mode, right_mode) in CONTRASTS.items():
            pairs, missing, small_pool = [], 0, 0
            for task, trial in sorted(group["slots"]):
                left = cells.get((skill, model, task, trial, left_mode))
                right = cells.get((skill, model, task, trial, right_mode))
                if left is None or right is None:
                    missing += 1
                    continue
                judges = sorted(left.keys() & right.keys())
                families = sorted({family(j) for j in judges})
                if len(families) < min_judge_families:
                    small_pool += 1
                    continue
                left_score, right_score = aggregate(left, "common", judges), aggregate(right, "common", judges)
                pairs.append({"task": task, "trial": trial,
                              "delta": round(left_score - right_score, 6),
                              left_mode: round(left_score, 6), right_mode: round(right_score, 6),
                              "common_judges": judges, "judge_families": families})
            comparisons[name] = {**stats(pairs), "candidate_task_trials": len(group["slots"]),
                                 "missing_mode_pairs": missing, "insufficient_judge_pool_pairs": small_pool}
        diagnostics = {}
        for mode in MODES:
            values = group["artifacts"][mode]
            diagnostics[mode] = {"valid_artifacts": len(values),
                                 "historical_absolute_mean": round(statistics.mean(aggregate(j, "historical", j) for j in values), 6) if values else None,
                                 "skill_adherence_mean": round(statistics.mean(v for j in values if (v := aggregate(j, "adherence", j)) is not None), 6)
                                 if any(aggregate(j, "adherence", j) is not None for j in values) else None}
        has_both = all(c["paired_samples"] for c in comparisons.values())
        results.append({"skill": skill, "model": model,
                        "status": "paired_observations_available" if has_both else "insufficient_evidence",
                        "effectiveness_decision": "not_established", "comparisons": comparisons,
                        "diagnostics_not_comparable_between_modes": diagnostics})
    counts = Counter(i["kind"] for i in issues)
    return {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
            "score_scale": [0, 5], "common_weights": COMMON_WEIGHTS,
            "min_common_judge_families": min_judge_families,
            "coverage": {"mapping_files": len(mapping_files), "mapped_modes": dict(sorted(mapped.items())),
                         "valid_scored_modes_before_duplicate_exclusion": dict(sorted(scored.items())),
                         "mapped_skill_model_groups": len(results),
                         "usable_skill_model_groups": sum(any(d["valid_artifacts"] for d in r["diagnostics_not_comparable_between_modes"].values()) for r in results),
                         "groups_with_both_contrasts": sum(r["status"] == "paired_observations_available" for r in results)},
            "issues": {"total": len(issues), "counts": dict(sorted(counts.items())), "examples": issues[:30]},
            "limitations": ["同任务、同模型标识、同试验号配对；旧数据未锁定模型服务端版本、任务/技能哈希和运行环境，不能证明严格因果关系。",
                            "两模式必须共享判官；按家族内均值、家族间中位数聚合。家族是名称启发式，判官票不计作重复运行。",
                            "M2-M4 是对该无关材料对照的差值；未验证等 token 长度或无关性，不称纯内容增益。",
                            "历史绝对分仅供诊断；M1 与 M2/M4 权重不同，技能遵循不进入统一增益分。",
                            "缺少基线、负增益或单次接近零都不构成技能已被模型替代的证据；未作有效/无效/退役判定。"],
            "results": results}


def audit_snapshot(path, skills=None, models=None):
    """Count published aggregate coverage; raw trial/judge pairing is unavailable."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("skills"), dict):
        raise ValueError("site data must contain a skills object")
    modes, candidates, results = Counter(), Counter(), []
    selected_skills, invalid_rows = 0, 0
    for skill, record in sorted(data["skills"].items()):
        if skills and skill not in skills:
            continue
        if not isinstance(record, dict) or not isinstance(record.get("tasks", []), list):
            invalid_rows += 1
            continue
        selected_skills += 1
        groups = defaultdict(lambda: defaultdict(set))
        for row in record.get("tasks", []):
            if not isinstance(row, dict) or any(not isinstance(row.get(k), str) or not row[k] for k in ("模型", "任务", "模式")):
                invalid_rows += 1
                continue
            model, task, mode = row["模型"], row["任务"], row["模式"]
            if models and model not in models:
                continue
            modes[mode] += 1
            groups[model][task].add(mode)
        for model, tasks in sorted(groups.items()):
            comparisons = {}
            for name, (left, right) in CONTRASTS.items():
                n = sum(left in v and right in v for v in tasks.values())
                candidates[name] += n
                comparisons[name] = {"status": "insufficient_evidence", "aggregate_candidate_tasks": n,
                                     "paired_samples": 0, "task_equal_mean_delta": None,
                                     "reason": "snapshot_missing_per_judge_scores_and_trial_ids"}
            results.append({"skill": skill, "model": model, "status": "insufficient_evidence",
                            "effectiveness_decision": "not_established", "comparisons": comparisons})
    return {"schema_version": 1, "source": "published_aggregate_snapshot", "snapshot_generated": data.get("generated"),
            "score_scale": [0, 5], "common_weights": COMMON_WEIGHTS,
            "coverage": {"mapping_files": 0, "snapshot_skills": selected_skills, "mapped_modes": dict(sorted(modes.items())),
                         "aggregate_candidate_task_pairs": dict(candidates), "mapped_skill_model_groups": len(results),
                         "usable_skill_model_groups": 0, "groups_with_both_contrasts": 0},
            "issues": {"total": invalid_rows, "counts": {"invalid_snapshot_rows": invalid_rows} if invalid_rows else {}, "examples": []},
            "limitations": ["快照 tasks 仅含聚合维度和历史总分；候选任务对仅说明模式字段同时出现，不是已验证的独立配对样本。",
                            "缺少逐判官评分、试验号、原始运行状态和版本指纹，不能恢复同判官池增益；所有结果为 insufficient_evidence。",
                            "本模式不计算历史总分或维度中位数之差；请取得 scoring/ 和原始产物后使用 --root 进行公共维度重算。",
                            "历史 SkillScore 以及旧 gains 不能作为技能有效、无效或被模型替代的证据。"],
            "results": results}


def markdown(report):
    cov = report["coverage"]
    lines = ["# SkillFit 技能增益审计", "", "离线只读；原始评分重算使用 0–5 分与正确性/完整性/表达清晰权重 0.55/0.30/0.15。", "",
             f"映射文件：{cov['mapping_files']}；模式条目：`{json.dumps(cov['mapped_modes'], ensure_ascii=False)}`。",
             f"可审计 skill×model：{cov['usable_skill_model_groups']}；同时有两种对照观测：{cov['groups_with_both_contrasts']}。", "",
             "| 技能 | 模型 | M2−M1：任务等权均值 / 配对数 | M2−M4：任务等权均值 / 配对数 | 证据状态 |",
             "|---|---|---|---|---|"]
    if report.get("source") == "published_aggregate_snapshot":
        lines[2] = "公开聚合快照：仅审计模式覆盖，不计算增益；需要原始逐判官评分和试验号才能重算。"
        lines.insert(6, "聚合候选任务对（未经配对验证）：`" + json.dumps(cov["aggregate_candidate_task_pairs"], ensure_ascii=False) + "`。")
    for result in report["results"]:
        columns = []
        for contrast in CONTRASTS:
            item = result["comparisons"][contrast]
            columns.append(f"{item['task_equal_mean_delta'] if item['task_equal_mean_delta'] is not None else '—'} / {item['paired_samples']}")
        clean = lambda text: str(text).replace("|", "\\|").replace("\n", " ")
        lines.append("| " + " | ".join(map(clean, [result["skill"], result["model"], *columns, result["status"]])) + " |")
    lines += ["", "## 限制", ""] + ["- " + item for item in report["limitations"]]
    lines += ["- 重复运行波动见 JSON 的 within_task.trial_sd；单次试验为 null，不把判官票当独立重复。", "",
              "## 数据问题", "", f"共 {report['issues']['total']} 项：`{json.dumps(report['issues']['counts'], ensure_ascii=False)}`。", ""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="仓库根目录（默认由脚本位置推断）")
    parser.add_argument("--site-data", type=Path, help="仅审计公开 site/data.json 的聚合覆盖；不计算增益，无需 scoring/")
    parser.add_argument("--skills", help="逗号分隔技能 ID；默认全部映射")
    parser.add_argument("--models", help="逗号分隔模型 ID；严格匹配，含 @api 路由")
    parser.add_argument("--min-judge-families", type=int, default=2, help="每对共有外部判官最少家族数（默认 2）")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--output", type=Path, help="显式指定输出文件；默认 stdout，不写任何文件")
    args = parser.parse_args(argv)
    if args.min_judge_families < 1:
        parser.error("--min-judge-families must be positive")
    if not args.site_data and not (args.root / "scoring").is_dir():
        parser.error("root must contain a scoring directory")
    select = lambda value: {x.strip() for x in value.split(",") if x.strip()} if value else None
    try:
        report = (audit_snapshot(args.site_data, select(args.skills), select(args.models)) if args.site_data else
                  audit(args.root, select(args.skills), select(args.models), args.min_judge_families))
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    content = markdown(report) if args.format == "markdown" else json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.write_text(content, encoding="utf-8")
    else:
        sys.stdout.write(content)


if __name__ == "__main__":
    try:
        main()
        sys.stdout.flush()
    except BrokenPipeError:
        # Let callers inspect a large report with `head` without a traceback.
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
