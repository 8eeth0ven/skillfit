#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每日收集 GitHub 高 star agent skills → 本地库/（本地数据库）+ 可选自动建快扫任务集
用法:
  python3 collect.py --min-stars 1000                 # 高星线：≥1k（用户定标）
  python3 collect.py --trending                        # 趋势线：近 60 天新建、星速快（stars≥200）
  python3 collect.py --update --min-stars 1000 --trending   # 日常：刷新 stars + 捞新增（两线都跑）
  python3 collect.py --seed 1000                       # 给 ≥1k 与 trending 条目建 任务集/<skill>__<owner>/（快扫层）
  参数: --max-repos 30 --max-skills-per-repo 20 --max-new 60
依赖: gh 已登录；GitHub 走代理 127.0.0.1:7897；搜索限速已内置 sleep
产出: 本地库/库.json + 本地库/<owner>__<repo>/<skill>/SKILL.md；--seed 时生成 任务集/
条目状态: 待评 / 评估中 / 已评 / 不评
"""
import argparse, base64, json, os, re, subprocess, sys, time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote

PROJ = Path("~/Desktop/Skills&Model-Benchmark").expanduser()
DB = PROJ / "本地库" / "库.json"
TDIR = PROJ / "任务集"
PROXY = {"https_proxy": "http://127.0.0.1:7897", "http_proxy": "http://127.0.0.1:7897"}
# 高星线查询词（2026-10-09 用户定标 ≥5k + 扩范围：3→8 路）
QUERIES_HI = ["topic:claude-skills", "topic:agent-skills", "topic:claude-code",
              "SKILL.md agent skills", "awesome claude skills", "claude skills collection",
              "agent skills marketplace", "anthropic skills"]
QUERIES_TR = ["agent skills created:>{since} stars:>=200", "claude skills created:>{since} stars:>=200",
              "SKILL.md created:>{since} stars:>=100"]

SWEEP_TASK = """---
ID: T01
技能: {skill}
难度: L2
考点: 快扫/文档理解与执行
---
## 用户Prompt

你刚拿到下面这份技能文档，准备开始用它。请完成三件事：
1) 用不超过 5 条要点概括该技能的核心规则（用自己的话，禁止照抄原文句子）；
2) 挑其中最重要的一条规则，自选一个最小输入，按这条规则完整执行一遍，给出执行过程与结果；
3) 指出该技能最容易被使用者误解或误用的一点，并说明为什么。

（通道约束：技能文档全文已在任务上方完整给出；禁止读取任何文件、禁止调用任何工具、禁止执行任何命令，直接纯文本作答。）

## 评分参考
- 概括与文档一致、无编造规则、不是原文复读
- 示例严格按所选规则执行（过程能对照文档核对），输入是最小可说明的
- 误用点真实源自文档（能指到对应条目/规则），不是泛泛而谈
- 判 PASS：三件事齐 + 概括无编造
- 硬条款：冗长不加分；照抄文档原文当概括 = 完整性最多 2 分

## 断言
（快扫层无确定性断言，判官全责；深评层进 任务集规范.md 流程）
"""


def ts(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(m): print(f"[{ts()}] {m}", flush=True)


def gh(path):
    try:
        r = subprocess.run(["gh", "api", path], capture_output=True, text=True,
                           timeout=30, env={**os.environ, **PROXY})  # 30s 快败；代理抖动时 60s 等不起
    except subprocess.TimeoutExpired:
        return None
    except Exception:
        return None
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except Exception:
        return None


def collect_line(queries, min_stars, max_repos):
    seen = {}
    for q in queries:
        for page in (1, 2, 3):  # 翻页：每路 100×3 页，破「只取前 30」的截断
            res = gh(f"/search/repositories?q={quote(q)}&sort=stars&order=desc"
                     f"&per_page=100&page={page}")
            items = res.get("items", []) if isinstance(res, dict) else []  # 间歇返回数组会炸整轮（迭代经验#13）
            for it in items:
                if not isinstance(it, dict):
                    continue
                if it["stargazers_count"] < min_stars:
                    continue
                seen[it["full_name"]] = {"repo": it["full_name"], "stars": it["stargazers_count"],
                                         "pushed_at": it["pushed_at"][:10],
                                         "描述": (it.get("description") or "")[:200]}
            if len(items) < 100:
                break
            time.sleep(2)
        time.sleep(3)
    return sorted(seen.values(), key=lambda x: -x["stars"])[:max_repos]


def awesome_explore(min_stars, max_repos):
    """awesome 清单反向展开：抓 awesome 列表 README 里的 GitHub 链接逐个核 star。
    补关键词搜索的盲区——高星仓库描述里不写 skills/claude 的永远搜不到。"""
    cand = {}
    for q in ["awesome claude skills", "awesome agent skills", "awesome claude code"]:
        res = gh(f"/search/repositories?q={quote(q)}&sort=stars&per_page=5")
        for it in (res.get("items", []) if isinstance(res, dict) else [])[:3]:
            if not isinstance(it, dict):
                continue
            r = gh(f"/repos/{it['full_name']}/readme")
            if not isinstance(r, dict) or r.get("encoding") != "base64":
                continue
            try:
                txt = base64.b64decode(r["content"]).decode("utf-8", "ignore")
            except Exception:
                continue
            for m in re.findall(r"github\.com/([A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+)", txt):
                cand[m.rstrip(".")] = 1
            time.sleep(1)
        time.sleep(2)
    out = []
    for full in list(cand)[:500]:
        info = gh(f"/repos/{full}")
        if isinstance(info, dict) and not info.get("fork") and info.get("stargazers_count", 0) >= min_stars:
            out.append({"repo": info["full_name"], "stars": info["stargazers_count"],
                        "pushed_at": info.get("pushed_at", "")[:10],
                        "描述": (info.get("description") or "")[:200]})
        time.sleep(0.5)
    log(f"awesome 展开：候选 {len(cand)} 链接，达标(≥{min_stars}★) {len(out)} 个")
    return sorted(out, key=lambda x: -x["stars"])[:max_repos]


def search_repos(a):
    lines = []
    if not a.trending_only:
        lines += collect_line(QUERIES_HI, a.min_stars, a.max_repos)
    if a.trending:
        since = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        tr = collect_line([q.format(since=since) for q in QUERIES_TR], 100, a.max_repos)
        for r in tr:
            r["trending"] = True
        lines += tr
    if not a.trending_only:
        lines += awesome_explore(a.min_stars, a.max_repos)  # 补关键词盲区（10k+ 也搜不全的根因）
    merged = {}
    for r in lines:
        if r["repo"] in merged:
            merged[r["repo"]].update({k: v for k, v in r.items() if k != "repo"})
        else:
            merged[r["repo"]] = r
    return sorted(merged.values(), key=lambda x: -x["stars"])


def fetch_skills(repo, max_per):
    tree = gh(f"/repos/{repo}/git/trees/HEAD?recursive=1")
    if not isinstance(tree, dict):
        return []
    paths = [t["path"] for t in tree.get("tree", [])
             if t["path"].endswith("/SKILL.md") or t["path"] == "SKILL.md"][:max_per]
    out = []
    for p in paths:
        c = gh(f"/repos/{repo}/contents/{quote(p)}")
        if not c or c.get("encoding") != "base64" or int(c.get("size", 0)) > 200_000:
            continue
        name = Path(p).parent.name or repo.split("/")[-1]
        dst = PROJ / "本地库" / repo.replace("/", "__") / name
        dst.mkdir(parents=True, exist_ok=True)
        (dst / "SKILL.md").write_bytes(base64.b64decode(c["content"]))
        out.append({"skill": name, "路径": str(dst / "SKILL.md"), "repo内路径": p})
        time.sleep(1)
    return out


def load_db():
    return json.loads(DB.read_text()) if DB.exists() else {"更新": "", "条目": []}


def save_db(db):
    DB.parent.mkdir(parents=True, exist_ok=True)
    DB.write_text(json.dumps(db, ensure_ascii=False, indent=1))


def seed_tasks(db, threshold):
    """≥threshold 星 或 trending 的条目 → 建 任务集/<skill>__<owner>/（已存在则跳过）"""
    made = []
    for e in db["条目"]:
        if not (e["stars"] >= threshold or e.get("trending")):
            continue
        if e.get("状态") in ("已评", "评估中"):
            continue
        owner = e["repo"].split("/")[0]
        sname = re.sub(r"[^\w\-]", "-", f"{e['skill']}__{owner}")[:60]
        d = TDIR / sname
        if d.exists():
            continue
        d.mkdir(parents=True, exist_ok=True)
        (d / "T01-快扫.md").write_text(SWEEP_TASK.format(skill=sname))
        (d / "技能文件.txt").write_text(e["路径"] + "\n")
        (d / "任务清单.md").write_text(
            f"# 任务清单：{sname}（快扫层，采集自 ★{e['stars']} {e['repo']}）\n\n"
            f"| ID | 难度 | 考点 | 状态 |\n|---|---|---|---|\n| T01 | L2 | 快扫/文档理解与执行 | ready |\n\n"
            f"> 快扫层只有通用题；进深评层需按 wiki 任务集规范.md 造专属题（Oracle 门禁）。\n")
        e["状态"] = "待评(已建题)"
        made.append(sname)
    return made


def single_instance():
    lock = PROJ / "本地库" / ".collect.lock"
    if lock.exists():
        try:
            old = int(lock.read_text().strip())
            os.kill(old, 0)
            sys.exit(f"另一个 collect.py 在跑 pid={old}（防并发写 库.json 互相覆盖），稍后再试")
        except ValueError:
            pass
        except ProcessLookupError:
            pass
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text(str(os.getpid()))


def main():
    single_instance()
    ap = argparse.ArgumentParser()
    ap.add_argument("--update", action="store_true")
    ap.add_argument("--min-stars", type=int, default=5000, help="高星线（默认 5k，用户 2026-10-09 定标）")
    ap.add_argument("--trending", action="store_true", help="追加趋势线：近60天新建 stars>=200")
    ap.add_argument("--trending-only", action="store_true")
    ap.add_argument("--seed", type=int, default=0, metavar="N", help="给 stars>=N 与 trending 条目建快扫任务集")
    ap.add_argument("--max-repos", type=int, default=500)
    ap.add_argument("--max-skills-per-repo", type=int, default=20)
    ap.add_argument("--max-new", type=int, default=10000, help="不设上限（用户 2026-10-09 裁定：一直测）")
    a = ap.parse_args()
    db = load_db()
    known = {(e["repo"], e["skill"]): e for e in db["条目"]}
    repos = search_repos(a)
    log(f"搜到 {len(repos)} 个仓库（高星线 ≥{a.min_stars}{' + 趋势线' if a.trending else ''}）")
    new_cnt = 0
    import traceback
    try:
        for r in repos:
            repo_skills = [e for e in db["条目"] if e["repo"] == r["repo"]]
            if repo_skills and a.update:
                for e in repo_skills:
                    e["stars"] = r["stars"]; e["pushed_at"] = r["pushed_at"]
                    if r.get("trending"): e["trending"] = True
                continue
            if repo_skills and not a.update:
                continue
            if new_cnt >= a.max_new:
                continue
            skills = fetch_skills(r["repo"], a.max_skills_per_repo)
            if not skills:
                continue
            for s in skills:
                key = (r["repo"], s["skill"])
                if key in known:
                    known[key]["stars"] = r["stars"]
                    continue
                if new_cnt >= a.max_new:
                    continue
                db["条目"].append({"repo": r["repo"], "stars": r["stars"], "pushed_at": r["pushed_at"],
                                   "描述": r["描述"], "skill": s["skill"], "路径": s["路径"],
                                   "repo内路径": s["repo内路径"], "功能组": "未分组", "状态": "待评",
                                   "trending": bool(r.get("trending")), "收集日": ts()[:10]})
                new_cnt += 1
                if new_cnt % 10 == 0:
                    db["更新"] = ts(); save_db(db)  # 增量落盘：后段崩溃不再丢整轮（迭代经验#13）
            log(f"+{len(skills)} {r['repo']} ★{r['stars']}{' 🔥trending' if r.get('trending') else ''}")
    except Exception:
        traceback.print_exc()
        log(f"采集主循环异常，已抓 {new_cnt} 条，保存后提前收尾（下一轮增量补齐）")
    db["更新"] = ts()
    if a.seed:
        made = seed_tasks(db, a.seed)
        log(f"快扫任务集已建 {len(made)} 个：{', '.join(made[:10])}{'…' if len(made) > 10 else ''}")
    save_db(db)
    top = sorted(db["条目"], key=lambda e: -e["stars"])[:8]
    log(f"本地库：总 {len(db['条目'])} 条，本次新增 {new_cnt}；star 榜首：")
    for e in top:
        print(f"  ★{e['stars']:<6} {e['repo']} / {e['skill']}  [{e['状态']}]{' 🔥' if e.get('trending') else ''}")


if __name__ == "__main__":
    main()
