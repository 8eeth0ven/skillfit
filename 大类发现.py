#!/usr/bin/env python3
# 大类发现：1252 技能 → 语义大类图谱（技能级归并，穿透"仓库系列"组）
# 素材：库.json（skill/repo/描述/功能组）+ 技能释义.json（中文一句话）
# 口径：功能形态优先于领域（"金融数据分析"归 数据，不归 商业金融）
# 产出：报告/技能大类图谱.md + 本地库/大类映射.json
import json, collections, pathlib, re

PROJ = pathlib.Path("~/Desktop/Skills&Model-Benchmark").expanduser()
db = json.loads((PROJ / "本地库/库.json").read_text())
gl = json.loads((PROJ / "本地库/技能释义.json").read_text())

# 大类体系：特异性优先（先匹配的先赢；顺序即优先级）
CATS = [
    ("网络安全", ["安全审计","渗透","漏洞","注入","越权","逆向","反编译","ctf","red.?team","红队","攻防","fuzz","漏洞挖掘","cyber","security","恶意","威胁","勒索","waf","exp","提权","后门","src 挖","风险评估","密码破解","steganograph","隐写","应急响应","取证","威胁情报","0day","cve"]),
    ("数据获取与分析", ["爬虫","采集","抓取","scrape","crawl","spider","数据获取","数据分析","可视化","dashboard","报表","数据清洗","etl","pandas","时序","行情","指标分析","资讯","趋势排行","用量统计"]),
    ("设计与演示", ["设计","design","配色","字体","排版","图标","icon","logo","插画","绘图","diagram","ppt","演示","slide","幻灯","海报","poster","原型","figma","ui/ux","界面","样式","css","视觉","brand"]),
    ("办公与文档处理", ["pdf","word","docx","excel","xlsx","spreadsheet","表格处理","办公","office","格式转换","合同","发票","简历","求职","resume","cv","面试","招聘"]),
    ("金融与投资", ["金融","投资","理财","股票","基金","crypto","加密货币","btc","defi","交易策略","风控","会计","记账","税务","财报","估值","k线","持仓","quant"]),
    ("科研学术", ["论文","文献","学术","latex","引用","综述","期刊","arxiv","实验设计","假说","科学计算","定理","证明","sci.?hub","学术写作","scientific"]),
    ("内容创作与写作", ["写作","文案","博客","blog","润色","翻译","translate","humaniz","去ai味","故事","小说","copywrit","邮件","newsletter","社媒","发帖","标题","改写","摘要","内容创作","稿件","写作风格"]),
    ("知识与记忆管理", ["记忆","memory","知识库","知识管理","笔记","obsidian","rag","向量","检索增强","语义搜索","embedding","第二大脑","zettel","归档整理","知识图谱"]),
    ("部署与运维", ["部署","deploy","docker","k8s","kubernetes","terraform","ansible","devops","运维","监控","nginx","服务器","日志分析","systemd","端口","进程","域名","dns","ssl 证书","反向代理","uptime"]),
    ("商业与增长", ["seo","增长","growth","营销","marketing","获客","转化","漏斗","广告","投放","电商","选品","listing","定价","商业模式","竞争分析","行业研究","市场分析","品牌","舆情","客服","销售"]),
    ("开发与代码质量", ["代码评审","code review","测试","tdd","单测","重构","lint","静态分析","调试","debug","报错","代码规范","commit","git","分支","编译","构建","类型","代码生成","脚手架","api 设计","架构","依赖","包管理","代码搜索","代码理解","pull request","性能分析","typescript","rust","代码规范","开发流程","相似重复","binary size","排查","诊断"]),
    ("生活与娱乐", ["游戏","game","娱乐","音乐","播客","podcast","视频","字幕","旅行","菜谱","健身","习惯","冥想","占卜","星座","宠物","礼物"]),
    ("Agent与自动化", ["agent","编排","orchestr","workflow","自动化","automat","智能体","mcp","工具构建","插件","plugin","技能创建","skill","prompt","提示词","subagent","任务拆解","planning","router","命令行","cli","shell","终端","批处理","定时","发散思维","可行性","产品规划","方法论","流程规范","链式执行"]),
]

def text_of(e):
    sk = e.get("skill", "")
    key = f"{sk}__{e.get('repo','').split('/')[0]}" if "__" not in sk else sk
    parts = [sk, e.get("repo", ""), e.get("描述", ""), e.get("功能组", ""), gl.get(key, ""), gl.get(sk, "")]
    return " ".join(p for p in parts if p).lower()

mapping, unmatched = {}, []
for e in db["条目"]:
    t = text_of(e)
    hit = None
    for cat, kws in CATS:
        for kw in kws:
            if re.search(kw, t):
                hit = cat; break
        if hit: break
    owner = e.get("repo", "").split("/")[0]
    key = e.get("skill", "")
    ukey = f"{key}__{owner}"
    if hit: mapping[ukey] = hit
    else: unmatched.append(ukey)

# 统计
cnt = collections.Counter(mapping.values())
for k in unmatched: mapping[k] = "待归类"
# 短名别名（供网站/管线按 skill 短名查询）
cnt2 = collections.Counter(mapping.values())

# 每大类代表技能（按释义取前5）
rep = collections.defaultdict(list)
for e in db["条目"]:
    sk = e.get("skill", ""); owner = e.get("repo", "").split("/")[0]
    cat = mapping.get(f"{sk}__{owner}", "待归类")
    desc = gl.get(f"{sk}__{owner}", e.get("描述", "")[:40])
    if len(rep[cat]) < 6 and desc: rep[cat].append(f"{sk}：{desc}")

# 功能组覆盖（该大类收编了哪些组）
grp = collections.defaultdict(collections.Counter)
for e in db["条目"]:
    sk = e.get("skill", ""); owner = e.get("repo", "").split("/")[0]
    grp[mapping.get(f"{sk}__{owner}", "待归类")][e.get("功能组","")] += 1

lines = ["# 技能大类图谱（1169 个唯一技能 → 13 大类）", "",
         "> 生成：大类发现.py（技能级语义归并，穿透仓库系列组）；口径：功能形态优先于领域。", ""]
lines.append("| 大类 | 技能数 | 占比 | 收编的主要功能组 |")
lines.append("|---|---|---|---|")
for cat, n in cnt2.most_common():
    tops = "、".join(f"{g}({c})" for g, c in grp[cat].most_common(4))
    lines.append(f"| **{cat}** | {n} | {n*100//len(db['条目'])}% | {tops} |")
lines += ["", "## 各大类代表技能", ""]
for cat, n in cnt2.most_common():
    lines.append(f"### {cat}（{n}）")
    lines += [f"- {x}" for x in rep[cat][:5]]
    lines.append("")
if unmatched:
    lines += [f"## 待归类（{len(unmatched)}，补规则素材）", "", " / ".join(unmatched[:40]) + (" …" if len(unmatched) > 40 else "")]
(PROJ / "报告").mkdir(exist_ok=True)
(PROJ / "报告/技能大类图谱.md").write_text("\n".join(lines))
(PROJ / "本地库/大类映射.json").write_text(json.dumps(mapping, ensure_ascii=False, indent=1))
print(f"13大类+待归类 | 覆盖 {len(mapping)-len(unmatched)}/{len(mapping)} | 待归类 {len(unmatched)}")
for cat, n in cnt2.most_common(): print(f"  {n:4d}  {cat}")
