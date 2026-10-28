# 静态站维护

前端由 site/index.html、site/app.js、site/style.css 和 site/assets/ 组成，不依赖构建步骤或外部 CDN。页面读取同目录 data.json，搜索与筛选在浏览器本地执行。

```bash
python3 -m http.server 8000 --directory site
```

公开界面区分 M2 绝对表现、历史评分与对照覆盖。存在 M1/M4 聚合字段仅表示存在对照记录；原始评分、trial 和模型版本未核验前，仍不能据此断言增益。

有完整本地运行数据时，可以生成新快照：

```bash
python3 tools/bench.py agg --skills YOUR_SKILL
python3 tools/bench.py site
```

site 命令会更新 data.json 并复制外置前端资产；不会恢复旧的内嵌网页模板。使用 BENCH_ROOT 导出到另一目录时，前端资产取自仓库，数据取自该运行根目录。没有原始评分时直接使用已有快照，不要用空目录覆盖它。

部署时上传整个 site/，包括 assets、app.js、style.css 和 data.json。可使用 GitHub Pages 或其他静态托管；执行 Git push 本身不代表托管已启用。提交前排除凭据、运行数据、身份映射、本机路径和浏览器调试产物。

crawl_loop.sh、test_loop.sh、web_refresh.sh 是可选循环脚本。先完成单次命令验证，再按自己的模型额度和任务覆盖配置运行；这些脚本的存在不代表服务在线或已经重新评测。
