#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成《技能总览.md》：按功能组分章，每技能一行 = 释义 | star | 最佳搭配 | SkillScore（可直视目录）"""
import json, re
from pathlib import Path

PROJ = Path(__file__).resolve().parent
db = json.loads((PROJ / "library/库.json").read_text())
gloss = json.loads((PROJ / "library/技能释义.json").read_text())
def sname(e): return re.sub(r"[^\w\-]", "-", e["skill"] + "__" + e["repo"].split("/")[0])[:60]
agg = {}
for f in (PROJ / "reports").glob("*-聚合.json"):
    a = json.loads(f.read_text())
    agg[a["skill"]] = a

groups = {}
for e in db["条目"]:
    g = e.get("功能组") or "未分组"
    if g == "未分组": g = "其他"
    groups.setdefault(g, []).append(e)

lines = [f"# 技能总览（{len(db['条目'])} 个 · 按功能组 · 自动生成）", "",
         "> 每行：技能 = 一句话功能 | ★star | 最佳搭配模型(SkillScore)。按组内 star 降序。", ""]
for g in sorted(groups, key=lambda x: -len(groups[x])):
    es = sorted(groups[g], key=lambda e: -e["stars"])
    lines += [f"## {g}（{len(es)}）", ""]
    for e in es:
        s = sname(e)
        a = agg.get(s, {})
        best = a.get("best")
        sc = a.get("skill_score", {}).get(best, "-") if best else "-"
        lines.append(f"- **{e['skill']}** = {gloss.get(s, '（释义待补）')} | ★{e['stars']} | "
                     f"{('🏆' + best.split('@')[0] + f'({sc})') if best else '待评分'}")
    lines.append("")
(PROJ / "reports" / "技能总览.md").write_text("\n".join(lines), encoding="utf-8")
print(f"总览已生成：reports/技能总览.md（{len(groups)} 组）")
