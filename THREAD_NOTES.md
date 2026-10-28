# SkillFit 维护说明

项目提供技能 × 模型的文本扫描、交叉评分和配对证据审计。先读 README；方法边界见 docs/measurement-audit.md。

- 执行器：tools/bench.py。根目录默认取脚本所在仓库，可用 BENCH_ROOT 覆盖。
- 前端：site/index.html、app.js、style.css；data.json 是静态展示数据。
- 不把 M2 绝对分数、快扫数量或快照生成时间解释为技能增益或重新评测时间。
- 共享维度重算使用 tools/value_audit.py；原始运行和判分保留在本地。
- 路径清单支持相对清单所在目录的路径；公开数据库使用 library/ 相对路径。
- 凭据、原始身份映射、运行日志和浏览器调试快照不提交。
- 模型版本、工具执行轨、成本数据和可复现批次清单仍需完善，见 README 路线图。
