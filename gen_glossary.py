#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""技能中文释义批量生成（glm-5.3-flash@api，thinking关，每批40个）→ library/skill_glossary.json + reports/技能总览.md
幂等：已有释义跳过。"""
import json, os, re, sys
from pathlib import Path

PROJ = Path(__file__).resolve().parent
sys.path.insert(0, os.path.expanduser("~/.zcode/skills/skill-bench/tools"))
os.environ.setdefault("BENCH_API_DIRECT", "1")
from bench import call

db = json.loads((PROJ / "library/db.json").read_text())
OUT = PROJ / "library/skill_glossary.json"
gloss = json.loads(OUT.read_text()) if OUT.exists() else {}

def sname(e): return re.sub(r"[^\w\-]", "-", e["skill"] + "__" + e["repo"].split("/0" if False else "/")[0])[:60]

todo = [e for e in db["条目"] if sname(e) not in gloss]
print(f"待释义 {len(todo)} / 总 {len(db['条目'])}")
BATCH = 40
for i in range(0, len(todo), BATCH):
    chunk = todo[i:i + BATCH]
    lines = [f"{n+1}. {e['skill']} | 仓库:{e['repo']} | 描述:{(e.get('描述') or '无')[:100]} | 组:{e.get('功能组','')}"
             for n, e in enumerate(chunk)]
    prompt = ("给下列每个 AI 技能写一句不超过22字的中文功能说明（它帮用户做什么），格式 JSON 数组，"
              "数组第 n 项对应第 n 个技能，只含字符串，不要其他文字：\n" + "\n".join(lines))
    out, err = call("glm-5.3-flash@api", prompt, tools="", timeout=180)
    m = re.search(r"\[.*\]", out or "", re.S)
    if not m:
        print(f"批次 {i//BATCH+1} 失败: {err[:60]}，跳过")
        continue
    try:
        arr = json.loads(m.group(0))
    except Exception:
        continue
    for e, g in zip(chunk, arr[:len(chunk)]):
        if isinstance(g, str) and g.strip():
            gloss[sname(e)] = g.strip()[:30]
    if (i // BATCH) % 8 == 0:
        OUT.write_text(json.dumps(gloss, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  进度 {i+len(chunk)}/{len(todo)}")
OUT.write_text(json.dumps(gloss, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"完成：共 {len(gloss)} 条释义 → {OUT}")
