---
name: download-anything
description: 面向个人与 AI Agent 的全能下载与结构化归档工具。当用户要求下载、提取、转换或归档社交视频与图文（B站及分P合集、抖音、小红书、YouTube、X、微博、Instagram、TikTok、m3u8）、播客与音频（小宇宙、Apple Podcasts、网易云音乐、Spotify、Apple Music、本地 NCM 解密与 FLAC 转 MP3）、文章与知识库（微信公众号、知乎/掘金/CSDN/Medium 等技术社区、Obsidian 同步）、学术论文与公开课课件（arXiv、DOI 论文、MIT OCW 开放讲义 PDF、ISBN/MD5 电子书）、开源商用字体（霞鹜文楷、思源黑体/宋体、阿里普惠体、JetBrains Mono、Inter 等）、百度/夸克网盘分享、GitHub 单文件与发行包或微软商店/安卓 APK 安装包时触发；也可在用户要求总结视频、公开课、播客或文章链接时调用，以提取本地字幕（.srt）、Shownotes 或 Markdown 正文供 Agent 分析。
---

# Download Anything (DA)

调用 `da`（或 `dl`）将分享口令文本、链接、DOI、ISBN、MD5、包名或本地音频文件下载并结构化归档到本地。全量核心下载、解密、格式转换与完整性校验均 **开箱即用、免配置本地运行**。各平台详细输入输出规范见 [references/platforms.md](references/platforms.md)，开源字体实测梯队与直链见 [references/fonts.md](references/fonts.md)，公开课归档与 `not_for` 边界见 [references/education.md](references/education.md)，完整 CLI 参数与 JSON 字段定义见 [references/cli.md](references/cli.md)。

## 1. 支持的能力与产物速查（按平台合并，单入口自动识别）

- **视频、图文与社交**（B站 / 抖音 / 小红书 / YouTube / X / 微博 / Instagram / TikTok / `.m3u8`）：自动识别视频（输出 `.mp4`，抖音支持免水印最高 4K；加 `-a` 提取纯音轨 `.m4a`/`.mp3`）或多图（`image_01.jpg` + `companion_files`）；自动生成 `cover.jpg` 原画封面、`content.md`、`content.info.json`；**B站支持 `?p=N` 分 P 精准选集与 `.srt` 字幕提取**，**抖音提取 `audio.mp3` 原声**，**小红书实况图提取配套 `.mov`**。
- **播客、音乐与音频**（小宇宙 / Apple Podcasts / 网易云音乐 / Spotify / Apple Music / 本地 `.ncm` 与 `.flac`）：输出 `.m4a` 或 `.mp3`（本地转换统一输出 `320kbps .mp3`）；配套生成播客 `content.md`（完整 Shownotes 与时间轴）、音乐 `.lrc` 歌词、高清专辑封面。
- **文章与知识库**（微信公众号 / 知乎 / 掘金 / CSDN / 博客园 / Medium / Substack / 少数派 / 简书 / SegmentFault / 开源中国 / V2EX）：输出干净 Markdown `article.md`，防盗链配图全部本地化（`img_01.png`...）并重写相对路径；加 `--vault` 自动注入 YAML frontmatter 同步至 Obsidian。
- **学术论文、公开课课件与电子书**（arXiv 链接或编号 / DOI / MIT OCW `ocw.mit.edu` 课程讲义与 `.edu` 开放课件 PDF / 10或13位 ISBN / 32位 MD5）：输出经 `pypdf` 页数校验的论文/讲义 `.pdf` 或电子书 `.epub` / `.pdf`；论文与公开课讲义自动生成标准 `citation.bib` 引用文件与包含作者/摘要的 `content.md`（商业付费/DRM 网课边界见 [references/education.md](references/education.md)）。
- **网盘分享**（百度网盘 / 夸克网盘）：自动识别内嵌提取码，支持子目录递归查找与云端临时目录自动清理；ZIP/TAR 默认安全解压并记录于 `extracted_files`。
- **代码、开源字体与安装包**（GitHub `blob` 单文件与 `releases` 发行包 / 开源商用字体 `.ttf`/`.otf`/`.woff2`/`.zip` / 微软商店链接或 12 位 Product ID / Android APK 包名或链接）：输出原代码文件、经 `font-magic` 魔数校验的字体文件（ZIP 字体包自动安全解压，实测梯队见 [references/fonts.md](references/fonts.md)）、`.msixbundle`（限免费 MSIX/Appx 应用）或 `.apk`（基于 F-Droid/Aptoide 镜像），配套 `content.md` 提供安装说明。

## 2. AI Agent 执行工作流（重要）

### 第一步：环境检查与安装确认（首次调用必检）
在执行下载前，**先确认本机是否已安装 `da` 及其运行依赖，未安装时必须先询问用户确认，不要静默修改系统环境**：

1. **定位可执行文件**：优先查找 `PATH` 中的 `da`（或 `dl`），若无则检查默认独立虚拟环境 `~/.download-anything/venv/bin/da`（Windows 为 `%USERPROFILE%\.download-anything\venv\Scripts\da.exe`）。
2. **未安装 `da` 或缺少 Python 3.10+ 时（先询问用户）**：
   - 若上述路径均不存在，先检查本机是否有 `python3`（需 `3.10` 及以上版本；注意 macOS 系统自带 `python3` 常为 `3.9`）。
   - **主动向用户询问确认**：告知用户本机尚未初始化 `da` 运行环境（或缺少 Python 3.10+），询问是否允许运行本 Skill 目录下的安装脚本 `python3 <Skill目录>/scripts/install.py`（若无 Python 3.10+，脚本可通过 `uv` 下载独立的 Python 3.12 并创建 `~/.download-anything/venv` 隔离环境，不污染系统 Python）。**待用户同意后**，再执行 `python3 <Skill目录>/scripts/install.py --yes`。
3. **运行环境自检（`da doctor --json`）**：
   - 首次安装后或遇到环境报错时，运行 `da doctor --json` 检查 `all_required_ok` 与 `media_ready`。
   - **缺少 Python 依赖包**：若 `all_required_ok` 为 `false`，询问用户后运行 `da doctor --fix --json` 自动补齐（官方 PyPI 超时会自动切换清华/阿里云镜像）。
   - **音视频任务缺少 `ffmpeg` / `ffprobe`**：若当前任务涉及视频或音频，而 `media_ready` 为 `false`（未安装 FFmpeg），请明确告知用户“文档、图片、论文、电子书与网盘功能不受影响，但音视频合并、转码与双轨校验需要 FFmpeg”，并**询问用户是否需要代为执行安装命令**（macOS：`brew install ffmpeg`；Windows：`winget install -e --id Gyan.FFmpeg`；Linux：`sudo apt install ffmpeg`）。
4. **无头环境（Headless）登录态配置**：
   - 在远程服务器、CI/CD 或 Docker 容器等无桌面/无浏览器环境中，交互式 `da login <平台>` 无法调用本地桌面浏览器或系统钥匙串。
   - **环境变量注入（推荐容器/CI）**：通过安全方式配置 `DA_<PLATFORM>_COOKIE` 或 `<PLATFORM>_COOKIE`（如 `DA_BAIDU_COOKIE`、`QUARK_COOKIE`）。Instagram 多图使用 `DA_INSTAGRAM_COOKIE_FILE` 指向授权 Cookie 文件，不使用上述 Cookie 字符串变量。
   - **挂载或预置 credentials.yaml**：在用户目录配置 `~/.download-anything/credentials.yaml`（权限设为 `0600`，如 `chmod 600 ~/.download-anything/credentials.yaml`），按平台填入 Cookie。
   - **安全红线**：严禁在 Agent 的终端输出或聊天对话中打印明文登录凭据、会话 Cookie 或密码。

### 第二步：前置转换与工具边界判断
当用户只提供名称而非直接链接/ID 时，**Agent 应先自行检索出精确标识符，再传给 `da`**：
- **电子书**：若用户只给书名（如“帮我下《傲慢与偏见》英文原版”），不要直接传书名模糊搜索；请先查出该书目标版本的 **10/13 位 ISBN**（如 `9780141439518`）或 **32 位 MD5**，再执行 `da "<ISBN或MD5>" --json`。
- **学术论文**：若用户只给论文标题，先查出对应的 **arXiv 编号**（如 `2310.06825`）或 **开放获取 DOI**，再执行 `da "<arXiv编号或DOI>" --json`。
- **开源商用字体**：若用户只给字体名称（如“帮我下载霞鹜文楷”、“思源黑体”、“阿里巴巴普惠体”或“JetBrains Mono”），请先查阅 [references/fonts.md](references/fonts.md) 中的实测梯队速查表，优先匹配 **Tier 1 首选源直链**（注意：`> 20 MB` 的全量中文字体严禁走 jsDelivr，必须使用 GitHub Releases 或 `gh-proxy.com`；猫啃网/`100font` 详情页非直链），再调用 `da "<字体直链>" --json` 下载并自动解压。
- **公开课课件与教学视频（含 `not_for` 边界）**：详见 [references/education.md](references/education.md)。B站体系课支持直接传入带 `?p=N` 的分 P 链接精准提取单集视频、`-a` 纯音轨与 `.srt` 字幕；MIT OCW（`ocw.mit.edu`）与高校 `.edu` 开放课件支持提取讲义 `.pdf` 并自动生成 `citation.bib`。**严守 `not_for` 边界**：严禁向用户承诺或尝试抓取 Coursera、edX、Udemy、中国大学MOOC（`icourse163.org`）、学堂在线及 B站付费课堂（`bilibili.com/cheese`）等受登录墙或 DRM 加密保护的商业网课。
- **应用安装包**：若用户只给应用名称，先查出对应的 **Android 包名**（如 `org.videolan.vlc`）或 **Microsoft Store 12 位 Product ID**（如 `9N0DX20HK701`），再交给 `da`。
- **GitHub 仓库与目录**：若用户需要克隆整个仓库或拉取多文件目录，优先使用环境中已有的 `gh` CLI、`git` 或 GitHub MCP；仅单文件（`github.com/.../blob/...`）或 Release 发行包直链（`github.com/.../releases/download/...`）使用 `da`。

### 第三步：大文件预检与 Agent 命令超时保护（防卡死必读）
长视频（如 4K 视频）、网盘大合集、安装包体积可能达到数百 MB 至数 GB，下载传输耗时极易超过 Agent 终端命令的默认等待超时（如 60s 或 120s）导致进程被强杀：
1. **优先使用 `--check` 预检**：面对网盘分享、高清视频或未知大小的资源，先执行 `da "<目标>" --check --json` 探测元数据与 `expected_size`（百度/夸克预检不触发云端转存）。
2. **动态调整超时与单文件上限**：
   - 若预检体积（`expected_size`）或实际文件超过默认 500 MB，主动追加 `--max-mb <容量>`（如 `--max-mb 2048`）。
   - 面对大文件下载时，Agent 调用终端工具应将超时阈值（如 `timeout` 或 `WaitMsBeforeAsync`）调大至充足时间，避免过早超时中断。
3. **异步/后台执行模式**：在支持后台任务（Daemon / Background Task）的 Agent 框架中，GB 级大文件任务建议置于后台执行，稍后轮询退出状态与交付结果。

### 第四步：执行下载命令
**自动化调用始终附加 `--json`**，从 `stdout` 解析结构化 JSON：

```bash
# 通用下载（直接传入分享口令、URL、DOI、ISBN、MD5、包名/Product ID 或本地音频路径）
da "<目标输入>" --json

# 仅提取纯音轨（.m4a / .mp3）
da "<视频或播客链接>" -a --json

# 归档至本地 Obsidian 知识库
da "<公众号或文章链接>" --vault "/path/to/vault" --json

# 仅预检目标标题、大小与元数据（网盘预检不会触发云端转存或创建目录）
da "<目标链接>" --check --json

# 捕获或导入本机浏览器/客户端的目标平台登录 Cookie
da login <平台名称> --json
```

可选参数：`-o <目录>` 指定输出目录，`-p <密码>` 指定提取码或解压密码，`-f` 忽略缓存强制重下，`--max-mb N` 调整单文件大小上限（默认 500 MB），`--no-unzip` 保留原压缩包不自动解压，`--no-sidecar` 不生成额外配套文件。

### 第五步：消费结构化归档产物（赋能下游分析）
下载完成后，**不要直接读取 `.mp4` / `.m4a` 等二进制媒体文件**，应直接利用 JSON 返回的结构化文本文件完成用户的总结、提炼或问答需求：
- **总结视频 / 播客**：直接读取 JSON 中 `sidecars.subtitle`（`.srt` 字幕）或 `sidecars.markdown`（节目 Shownotes、视频简介、时间戳与互动数据）。
- **精读公众号 / 技术文章**：直接读取 `primary_asset`（`article.md`），正文内插图已转为同目录下的本地图片文件。
- **整理学术文献**：读取 `primary_asset`（`.pdf`）的同时，可直接读取 `companion_files` 中的 `citation.bib` 获取标准 BibTeX 引用，以及 `sidecars.markdown` 获取摘要与作者元数据。

## 3. 状态判定与异常自愈 SOP

解析 `--json` 输出的 `status` 与退出码，如实反馈并按规则自愈：

- **`status: "success"`（退出码 `0`）**：主文件已通过格式/媒体结构校验（见 `verification.details.level`），所有配套文件与同步步骤均已完成。
- **`status: "cached"`（退出码 `0`）**：命中本地 SQLite 缓存（`~/.download-anything/index.db`）且本地文件完整，直接使用返回的 `primary_asset` 与 `sidecars` 路径，无需重复下载（除非用户要求强制刷新才加 `-f`）。
- **`status: "partial"`（退出码 `2`）**：**主文件已成功下载并通过校验**，仅部分附属文件（如某张配图、字幕 429）或后处理步骤（如 Obsidian 同步、临时目录清理）未完成。
  - **处理准则**：**切勿将 `partial` 当作失败去盲目重下主文件！** 直接使用已落盘的 `primary_asset`，并读取 `warnings` 与 `operations` 字段向用户说明哪项附属步骤未完成及其原因。
- **`status: "dry_run"`（退出码 `0`）**：仅完成 `--check` 预检，未实际落盘文件。
- **`status: "error"`（退出码 `1`）**：根据 `error_type` 执行有限自愈，严禁把失败或预检汇报为下载成功：
  - `AuthenticationRequiredError`：目标平台（如百度网盘、夸克网盘、小红书视频、Instagram 多图）需要登录凭据。
    - **本地桌面环境**：运行 `da login <平台> --json` 自动提取本机浏览器已登录会话，或提示用户在浏览器中先登录该站点。
    - **无头（Headless）环境 / 容器 / 远程服务器**：百度和夸克可注入 `DA_<平台>_COOKIE` 或 `<平台>_COOKIE`，或配置权限为 `0600` 的 `~/.download-anything/credentials.yaml`；Instagram 多图需使用 `DA_INSTAGRAM_COOKIE_FILE` 指向授权 Cookie 文件。
    - **安全红线**：严禁在输出或对话中打印会话 Cookie、登录凭据或密码明文。
  - `FileTooLargeError`：超过默认 500 MB 上限。若用户明确需要下载该大文件，调高 `--max-mb N` 重试一次。
  - `ExtractionError`（含压缩包格式限制）：自动解压仅支持受限的 `ZIP` / `TAR`；若因 `7z`、`RAR` 或特殊加密方式报错而用户只需保存原压缩包，加上 `--no-unzip` 重试一次。
