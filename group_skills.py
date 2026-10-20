#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自动功能分组（N×N×A 的 A 轴）→ db.json 功能组字段 + 分组报告。
规则：先按同仓库系列（天然同功能变体），再按名称/描述关键词补跨仓库同类。
基准约定：组内 star 最高者为基准（cross 时列表第一个）。幂等可重跑。"""
import json, re
from pathlib import Path

PROJ = Path(__file__).resolve().parent
DB = PROJ / "library/db.json"

# 跨仓库功能关键词（匹配 skill 名，小写）
KW = [
    ("代码评审", r"code-review|review-pr|review-changes|pr-review|code-reviewer"),
    ("测试/TDD", r"^tdd|test-driven|testing|e2e|qa-test|smoke-test|webapp-testing|unit-test"),
    ("PPT/演示", r"pptx|ppt|slide|presentation|deck|pitch"),
    ("文档/写作", r"^docs?-|documentation|technical-writing|blog|article-writ|writing-"),
    ("翻译", r"translat|i18n|localiz"),
    ("安全审计", r"security|audit-|-audit$|owasp|hardening|forensic|privesc|malware|incident"),
    ("爬虫/数据获取", r"scrape|crawl|web-fetch|search|research-paper|arxiv|fetcher"),
    ("深度研究", r"deep-research|research|investigat|due-diligence|analys"),
    ("SEO/增长", r"\bseo\b|growth|marketing|copywrit|email-|cold-|ads\b|churn|attribution"),
    ("设计/UI", r"design|ui-|frontend|figma|theme|brand|logo|illustrat|infographic|art"),
    ("数据可视化", r"dashboard|dataviz|chart|graph-|visualization"),
    ("部署/运维", r"deploy|ci-cd|ci\b|release|devops|infra|docker|k8s|kubernetes|observab"),
    ("简历/求职", r"resume|job-|interview|career|hiring"),
    ("PDF/办公", r"\bpdf\b|xlsx|docx|word|excel|office"),
    ("MCP/工具构建", r"mcp|skill-creator|plugin|tool-builder|builder"),
    ("记忆/知识管理", r"memory|mem-search|knowledge|wiki|rag\b|notes"),
    ("Agent编排", r"orchestrat|swarm|multi-agent|subagent|workflow|agent-"),
    ("金融/投资", r"finance|investment|valuation|earning|stock|trading|crypto|web3|defi"),
    ("医疗/生物", r"clinical|medical|bio|gene|protein|cell|chem|medical"),
    ("教学/课程", r"lesson|quiz|teach|tutor|course|educat"),
]

db = json.loads(DB.read_text())
groups = {}
for e in db["条目"]:
    s, repo = e["skill"].lower(), e["repo"]
    g = None
    # 1) 同仓库系列：同 repo 且 ≥4 个 skill → 以 repo 系列名为组
    groups.setdefault(f"@{repo}", []).append(e)
    # 2) 关键词
    for name, pat in KW:
        if re.search(pat, s):
            g = name
            break
    e["_kw"] = g or ""

# 落功能组：关键词优先（跨仓库同功能=「方面」轴），无关键词命中才归仓库系列
repo_series = {k: v for k, v in groups.items() if len(v) >= 4}
out = {}
for e in db["条目"]:
    if e.get("_kw"):
        e["功能组"] = e["_kw"]
    elif f"@{e['repo']}" in repo_series:
        e["功能组"] = f"{e['repo'].split('/')[1]}系列"
    else:
        e["功能组"] = "未分组"
    e.pop("_kw", None)
    out.setdefault(e["功能组"], []).append(e)

DB.write_text(json.dumps(db, ensure_ascii=False, indent=1))
# 报告
rank = sorted(out.items(), key=lambda x: -len(x[1]))
print(f"分组完成：{len(rank)} 组 / {len(db['条目'])} 技能")
for g, es in rank[:20]:
    top = sorted(es, key=lambda e: -e["stars"])[0]
    print(f"  {g:<24} {len(es):>3} 个 | 基准(★最高): {top['skill']} ★{top['stars']}")
(Path(PROJ / "reports") / "功能分组.txt").write_text(
    "\n".join(f"{g}\t{len(es)}\t" + ",".join(sorted(x['skill']+'__'+x['repo'].split('/')[0] for x in es))
              for g, es in rank))
