#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""隔离工具泄漏/超短坏产物（迭代经验#11 处置）：台账标 superseded + 文件挪 结果/隔离-toolleak/ + 清受影响技能评分目录。
重跑：python3 隔离toolleak.py（幂等；kimi 新格跑完后可再执行一遍覆盖 kimi）"""
import csv, re, shutil
from pathlib import Path

PROJ = Path(__file__).resolve().parent
RDIR = PROJ / "结果"
SDIR = PROJ / "评分"
LEAK_RE = re.compile(r"<tool_call>|｜｜DSM|\]<\]minimax|<\|tool\||multi_tool_use")
CLI_MODELS = {"deepseek-v4.1-flash", "space-bunny", "kimi-k2.7"}  # @api 走纯文本通道不查

led = RDIR / "台账.csv"
rows = list(csv.DictReader(open(led)))
qdir = RDIR / "隔离-toolleak"
bad_skills, n_file = set(), 0
for r in rows:
    if r.get("模式") != "M2" or r.get("技能") == "humanizer" or r.get("试验") not in ("1", ""):
        continue
    if r.get("模型") not in CLI_MODELS or r.get("状态") != "ok":
        continue
    p = Path(r["路径"])
    if not p.exists():
        continue
    body = p.read_text(errors="ignore").split("---", 2)[-1]
    if len(body.strip()) < 100 or LEAK_RE.search(body):
        dst = qdir / p.relative_to(RDIR)
        dst.parent.mkdir(parents=True, exist_ok=True)
        p.rename(dst)
        n_file += 1
        r["状态"] = "superseded:toolleak"
        bad_skills.add(r["技能"])
with open(led, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
for s in bad_skills:
    d = SDIR / s
    if d.exists():
        shutil.rmtree(d)
print(f"隔离 {n_file} 个坏产物，涉及 {len(bad_skills)} 个技能（评分目录已清，测试循环下轮自动重跑+重评）")
