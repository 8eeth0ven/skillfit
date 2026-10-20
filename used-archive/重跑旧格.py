#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""作废所有旧 prompt（无通道约束/文档头带绝对路径诱因）产的 CLI 模型 M2/M4 格（迭代经验#11 处置扩大版）。
- @api 格与 M1/M3 保留（prompt 未变或无文档）
- 坏格文件挪 结果/隔离-旧prompt/，台账标 superseded:oldprompt
- 评分目录全清（统一重评纪元，含自评）
- 库.json 里被作废技能的 已评 回退为 待评(已建题)
幂等可重跑。"""
import csv, json, shutil
from pathlib import Path

PROJ = Path(__file__).resolve().parent
RDIR, SDIR, DB = PROJ / "结果", PROJ / "评分", PROJ / "本地库/库.json"
CLI = {"deepseek-v4.1-flash", "space-bunny", "kimi-k2.7", "glm-5.3-flash"}  # glm-5.3-flash 精确匹配，不含 @api

led = RDIR / "台账.csv"
rows = list(csv.DictReader(open(led)))
qdir = RDIR / "隔离-旧prompt"
touched, n_file = set(), 0
for r in rows:
    if r.get("模式") not in ("M2", "M4") or r.get("模型") not in CLI or r.get("状态") != "ok":
        continue
    p = Path(r["路径"])
    if p.exists():
        dst = qdir / p.relative_to(RDIR)
        dst.parent.mkdir(parents=True, exist_ok=True)
        p.rename(dst)
        n_file += 1
    r["状态"] = "superseded:oldprompt"
    touched.add(r["技能"])
with open(led, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)

n_wipe = 0
for d in SDIR.iterdir():
    if d.is_dir():
        shutil.rmtree(d); n_wipe += 1

db = json.loads(DB.read_text())
n_back = 0
for e in db["条目"]:
    sname = e["skill"] + "__" + e["repo"].split("/")[0]
    if sname in touched and e["状态"] == "已评":
        e["状态"] = "待评(已建题)"; n_back += 1
if n_back:
    DB.write_text(json.dumps(db, ensure_ascii=False, indent=1))
print(f"作废旧prompt格 {n_file} 个（{len(touched)} 个技能）；清评分目录 {n_wipe} 个；已评回退 {n_back} 个")
print("测试循环将自动用新硬化 prompt 重跑全部作废格并 4 判官含自评重评")
