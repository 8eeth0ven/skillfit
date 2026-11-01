---
name: finance-explainer
description: 「小Lin说」式财经/科技解说视频工作室：选题打分 → 带出处的事实清单（Exa/Tavily/Serper/Firecrawl）→ 按危机型/收购战型/悖论型骨架写有活人感的口播剧本（拍表 episode.json）→ 主播自录音频对齐跳切（或 MiMo 占位）→ 原创数字人出镜（Renoise：Wan 3.0 音频驱动口型 / Grok 1.5 原生说话+后换音色）→ 空镜与梗图（Renoise 便宜模型 + Unsplash/Pexels/Wikimedia）→ Remotion 引擎合成：主播全屏↔缩小↔圆形小窗的「放大缩小」、两代舞台主题（v1 紫色几何 / v2 深色玻璃）、日期贴纸、大数字滚动、术语卡、原文标黄、问题云、竞猜、卡通贴纸独白、章节卡、字幕、BGM 避让与音效。触发：做一期小Lin说那样的视频、财经解说、一口气了解 X、讲讲某个金融事件/收购案/国家经济、数字人口播财经、把这个新闻做成解说视频、复刻财经频道形式。不用于：单支品牌宣传片（用 promo-video）、系列课（用 ai-teardown）、冒充真实主播。
---

# 财经解说工作室（小Lin说式）

把一个财经/科技话题做成 2–25 分钟的横屏解说片：一个有活人感的主播坐在书房里聊，配图表、文件、空镜和梗，镜头在「主播全屏」和「主播缩成小窗、旁边上图」之间来回切。

完整的频道拆解（160 支元数据、97 支字幕统计、6 支逐帧分类）在 references/channel-teardown.md，网页版报告：https://claude.ai/artifact/EzcUvSJmVqgFJBGpfn3G3Y

## 红线（每次都适用）

- **不冒充真人。**数字人只用原创形象：纯文字生成，或者用户本人 / 明确同意的人的照片。不用真实创作者（包括小Lin本人）的脸、改过发型眼镜的同一张脸、或从他们视频里克隆的声音——截图式「授权」、加水印加声明都不改变这一点。用户坚持时，说明理由并给原创方案。
- **不搬内容。**文案、布景、画面全部原创；只学结构和手法。不用影视剧片段、新闻台画面；真实人物用自由协议照片或文字名牌。
- **每个数字有出处。**事实清单 facts.md 里每条都带日期 + 来源 URL；剧本里的数字必须能在清单里找到；查不到的写 ⚠ 且不进剧本。拿不准的地方让主播直说「这个我没查到」——这本身就是活人感手法。
- **生成要花用户的 credits。**Renoise 任何 create_tasks 之前，先给出模型、提示词、参数、数量、estimate_cost 总价和余额，等用户在对话里明确同意。口型视频依赖最终音频：音频没定稿前，不要把整片口型都做掉（会付两次钱）。

## 流程

### 0. 准备
- 检索 key 在 `~/.config/xiaolin-explainer/keys.env`（EXA / TAVILY / SERPER / FIRECRAWL / UNSPLASH / 可选 PEXELS、PIXABAY）。只读这个文件，不要扫描系统找密钥。
- 引擎：`bash scripts/setup_engine.sh <项目目录>`（复制 templates/engine，node_modules 优先从本机已有 Remotion 项目 `cp -c` 克隆，失败再 npm install）。

### 1. 选题（references/topic-and-titles.md）
五项打分卡 ≥3 才做；给 3 个标题候选（「一口气了解 + 大对象」「【硬核】」「带数字」「疑问句 + 竖线钩子」）。确认时长：完整版 15–25 分钟表现最好，演示/跑通先做 2 分钟。

### 2. 事实清单
`python3 scripts/research.py multi "<查询>"` 找线索 → 打开原文核对（`research.py scrape <url>`）→ 写 facts.md：分组、每条「事实（精确数字）— 日期 — 来源 + URL」，最后写「容易讲错的地方」。可派子智能体并行查，但交回后自己抽查关键数字。

### 3. 剧本 = 拍表 episode.json（references/narrative-playbook.md + episode-schema.md）
- 选骨架：A 危机/暴雷型（怎么死的）、B 收购/博弈型（怎么打的）、C 悖论型（为什么反常）。
- 每拍一段口播 + 一个主画面（host: full/side/pip/off，或 stage 图表、bg 空镜）+ 若干叠加卡片，口播里用 `[[cue]]` 标卡点。
- 文案指标：成片约 6 字/秒（录音约 4.8）、每分钟 1–2 个设问、3–4 个带参照物的数字、1 个英文术语；至少放 3 个活人感手法（开场个人状态 / 替观众说质疑 / 拟人独白 / 生活比喻 / 坦白没查到 / 竞猜停顿 / 先说答案 / 结尾回扣）。
- 同时导出录音稿（每拍一段，去掉 cue 标记，写清读法：英文缩写、数字年份）。

### 4. 声音
- **首选：主播自录。**`python3 scripts/align_recording.py 录音.m4a episode.json voice/` → 逐句对齐、口误重来只留最后一遍、拍内长停顿压到 0.16 秒，输出 timings.json。报告里 ⚠（对齐 <80%）的拍要人工听。
- **占位：**`python3 scripts/narrate_mimo.py narration.json voice --gap 0.22 --lead 0.3`（MiMo 预设音色，语气说明写进 voice.style）。占位就是占位，正式版换真人音频后整条流水线不变。

### 5. 数字人（references/production.md）
- 定妆照：Seedream 5.0 Pro 16:9 2k（≈6），书房中景、两侧留白放图表、有专属道具（霓虹名字灯、玩偶）。用户给了原创脸就作参考图，否则纯文字生成。
- **方案 W（Wan 3.0，音频驱动，便宜）：**参考图 + 该拍音频 → 口型跟着声音走；480p ≈ 6 credits/秒。输出里音频比画面晚 0.23 秒，host.json 的 offset 填 0.23。缺点：眼神偏呆、细节一般。
- **方案 G（Grok Video 1.5，原生说话，更生动）：**一张图 + 台词写进提示词 → 自带说话声和口型；720p 15 秒 255。之后用 Seed Audio 做「保留节奏换音色」替换成主播声音。适合全屏特写镜头。
- 小窗（pip）用 3 段 10 秒通用说话循环轮换即可，省掉约 40% 口型费用。
- 先做 10 秒测试：抽帧看停顿处嘴是否闭合、人物是否走样，再批量。

### 6. 空镜 / 梗 / 贴纸
- 空镜：Renoise Wan 3.0 480p 5–10 秒（audioGeneration=false），提示词写「无文字无 logo」；或 `scripts/fetch_stock.py <id> "<关键词>" engine/public/assets --kind photo|video`（自动记 credits.json，片尾署名）。
- 梗图：原创短片（如「小机器人一群围住大机器人」），不用影视片段。
- 卡通贴纸：grok-image 纯绿底 → 抠绿成透明 PNG（脚本见 production.md）。

### 7. 合成
`python3 scripts/build_timeline.py episode.json voice/timings.json <engine>/public --assets assets.json --host host.json --bgm music/bgm.mp3 --badge "…"` → `npx remotion still Episode out/x.jpg --frame=N` 抽帧检查（含过渡中间帧）→ `npx remotion render Episode out/raw.mp4 --concurrency=6` → ffmpeg `loudnorm=I=-16` + CRF 21 出片。

### 8. 质检清单
字幕按原文标点断句且 ≤13 字；卡片不压字幕、不出画；主播缩放过渡中间帧无残影；口型片段对齐（offset）；数字与 facts.md 一致；角标/声明在；响度 -16 LUFS；片尾列出素材与数据出处。

## 目录
- references/channel-teardown.md — 频道数据与结论
- references/topic-and-titles.md — 选题打分卡、标题公式
- references/narrative-playbook.md — 三种骨架、活人感手法、语言习惯、文案指标
- references/visual-grammar.md — 16 种画面语法 ↔ 引擎组件 ↔ 拍表字段
- references/episode-schema.md — episode.json / host.json / assets.json 字段
- references/production.md — 数字人两方案、Renoise 提示词与价格、素材来源与授权、抠图、渲染与坑
- scripts/ — research.py、fetch_stock.py、narrate_mimo.py、align_recording.py、build_timeline.py、setup_engine.sh；频道分析工具 classify.py / sheet.py / copy_stats.py / vtt2txt.py（拆别的频道时用）
- templates/engine — Remotion 引擎（Episode 合成、Host、Stage、Overlays、Misc 组件，两代主题）
- examples/ai-chips — 「中国买不到顶级显卡，为什么还是世界第二 AI 大国」：facts.md、10 分钟拍表、2 分钟拍表、录音稿；examples/svb — 硅谷银行 3.5 分钟拍表
