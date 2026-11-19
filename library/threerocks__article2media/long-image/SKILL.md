---
name: long-image
description: 长图：两种输入，两种长图。改写稿 content.json → 1–4 张总结长图（手机宽度单栏，每节配图表和数据面板，附执行清单；--wide 出 1200 宽双栏杂志版；12 套主推主题）；文章 article.md（原文、译文、逐字稿）→ 一字不改的原文长图（逐块读回校验，超长自动分张）。可以单独用（已有 content.json 或文章），也可以接在抓取、改写、翻译后面。Use when the user wants a 长图, 总结图, 杂志长图, infographic pages, or 原文长图 / 全文长图 / 原文排版 / 一字不改 / -f from an article or an existing content.json; also to re-render a content.json in another theme (换主题、换风格).
argument-hint: <content.json|article.md|目录> [--theme 主题名|a,b|all] [--wide] [--page 1,3] [--out 目录]
allowed-tools: Bash(node ${CLAUDE_SKILL_DIR}/scripts/*)
version: "2.3.1"
---

# 长图（long-image）

> 路径约定：文中的 `${CLAUDE_SKILL_DIR}` 指本 SKILL.md 所在的目录。宿主没有替换这个变量时（命令里原样出现 `${CLAUDE_SKILL_DIR}`），把它换成这个目录的绝对路径再运行；`../<名字>/` 指同级的另一个 skill 目录。

| 输入 | 产出 |
|---|---|
| `content.json`（改写稿） | 总结长图：默认手机版，单栏、1080 宽，手机上不用放大就能读；`--wide` 出 1200 宽的双栏杂志版（适合电脑上看、打印、做展示图）。`<目录>/<主题>/page-01.png …` |
| `article.md`（原文、译文、逐字稿、`rewrite.md`） | 原文长图：一字不改，1080 宽，`<目录>/full/full.png`（过长时 `full-01.png …`） |

参数：`$ARGUMENTS`

## 0. 先确定输入
- 已有 `content.json` → 总结长图；用户只给了文章、又说"原文 / 全文 / 一字不改 / -f" → 原文长图。
- 给的是链接、文件、粘贴的正文或视频 → 先用 `article-fetch` / `video-transcript` 取原文。
- 只有文章、用户没说原文还是总结 → 长图默认**改写**：先用 `article-rewrite` 写 content.json。原文是外文、又要原文长图 → 先用 `article-translate`。
- 判断规则、工作目录和调用其他能力的方式：`../article2media/references/pipeline.md`。

第一次使用先跑 `node ${CLAUDE_SKILL_DIR}/scripts/doctor.mjs`（Node 22+、Chrome）。

## 1. 总结长图（content.json）
```bash
node ${CLAUDE_SKILL_DIR}/scripts/long.mjs <目录>/content.json                    # 主题取 content.json 的 theme
node ${CLAUDE_SKILL_DIR}/scripts/long.mjs <目录>/content.json --theme midnight   # 用户指定主题
node ${CLAUDE_SKILL_DIR}/scripts/long.mjs <目录>/content.json --wide             # 1200 宽双栏杂志版（文字在左、图在右）
node ${CLAUDE_SKILL_DIR}/scripts/long.mjs <目录>/content.json --theme all        # 全部主推主题，分目录输出
node ${CLAUDE_SKILL_DIR}/scripts/long.mjs --list                                 # 列出主题
```
- 每页输出 PNG 和同名 `.html`、`qa.json`，一页大约 4 秒。其他参数：`--page 1,3`、`--scale 2`、`--format jpeg --quality 90`、`--max-height 7600`（手机版默认 7600，宽版 4400）、`--brand brand.json`、`--out 目录`。
- 默认出手机版：用户在微信、朋友圈、微博里看长图，双栏的字在手机上太小。用户说"杂志版 / 宽版 / 双栏 / 电脑上看 / 要打印"时加 `--wide`。手机版一页很高（常见 9000–13000 px）；超过 16000 px 时会自动降低输出倍数并提示，这时把这一页拆成两页。
- content.json 没写主题、用户也没指定时，按 `../article2media/references/styles.md` 选一个，写进 content.json。
- 有 AI 插画还没生成时会出占位框并提示：用 `article-rewrite` 的 `illustrate.mjs` 生成，生成不了就去掉插画字段。

**检查与修正（最多 2 轮：出图 → 发现问题 → 改 content.json 或参数 → 再出图，算一轮；只跑 check.mjs 不算）**
1. 版面检查：✗（图内溢出、文字截断、元素重叠、图片加载失败）必须修——缩短图内文字、减少项目，或换一种图；⚠「末行只剩一个字」给那句话增减两三个字；⚠「页面过高」删减内容或拆成两页。
2. **亲眼看图**：用 Read 打开每张 PNG，看图能不能一眼看懂、图和图注是不是一回事、有没有哪节太空或太挤。
3. 只改 `content.json`（字段写法见 `../article-rewrite/references/content-schema.md`、`figures.md`），然后重新渲染。不要手改 HTML。

## 2. 原文长图（article.md）
```bash
node ${CLAUDE_SKILL_DIR}/scripts/long.mjs <目录>/article.md                  # 白底阅读面
node ${CLAUDE_SKILL_DIR}/scripts/long.mjs <目录>/article.md --theme quiet    # 用主题的颜色与字体
```
读 `references/original-long.md`（阅读面规格）和 `../article2media/references/verbatim.md`（允许与禁止、逐块校验）。全文校验未通过（改字、调序、漏块、重复）就是错误，按提示修，不能靠目测放行。看 `full/review/` 里的重叠切片，逐张看完再交付。

## 3. 交付
- 每张图的绝对路径（原文长图加像素尺寸）；
- 总结长图：一行大纲（每页的 part）、用的主题（你选的就一句话说明理由）、怎么换：`--theme 名称`、`--theme all` 都不需要重写内容；要卡片用 `image-cards`，要公众号用 `wechat-layout`；
- 原文长图：原文块数与全文校验结果（"45 / 45 块逐字一致"）、实际字体、分成了几张、生成图 0 张；
- 需要用户留意的地方（未核对的数字、抓取不全的段落）。
