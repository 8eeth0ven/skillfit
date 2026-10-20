# 参测模型（2026-10-09 盘点，开新批前重盘）

来源：`codebuddy --help` 的 `--model` 行 + BigModel API 直连（密钥.env）。同家族 = 报告分组 + 交叉评分披露同源。

## 首批深评 3×3（已开跑 2026-10-09）

| 勾 | 模型 id | 家族 | 通道 |
|---|---|---|---|
| [x] | deepseek-v4.1-flash | DeepSeek | CLI |
| [x] | glm-5.3-flash | GLM | CLI（@api 通道已验证，key 在 密钥.env，随时可切） |
| [x] | space-bunny | SpaceBunny | CLI |

## 快扫四件套（采集 skill 批量初筛）

| 勾 | 模型 id | 家族 | 通道 |
|---|---|---|---|
| [x] | glm-5.3-flash@api | GLM | API（密钥.env 双 key 轮换） |
| [x] | glm-5.3@api | GLM | API |
| [x] | deepseek-v4.1-flash | DeepSeek | CLI |
| [x] | space-bunny | SpaceBunny | CLI |

## 扩展池（第二批 / 备用）

| 勾 | 模型 id | 家族 | 备注 |
|---|---|---|---|
| [ ] | glm-5.3-flashx | GLM | 增强快速版 |
| [ ] | glm-5.2 / glm-5.1 | GLM | 旧代差 |
| [ ] | kimi-k2.8-preview / k2.7 / k2.6 | Kimi | 旧代差 |
| [ ] | minimax-m2.7 | MiniMax | 旧代 |
| [ ] | hy3 / hy3-x | Hy | 旧代 |
| [ ] | space-bunny | ? | 定性不明，doctor 过再说 |
| — | glm-5v-turbo | GLM | 视觉模型，纯文本任务**不参测** |

## 判官池（score 的 --scorers）

- 判官 = 参测模型全集中挑 ≥3 个跨家族；每产物评分者 = 判官池 − 生产者（同 base 名互斥，含 @api 变体）
- 判官跟生产者重叠没问题，只排除自己

## API 直连（codebuddy 清单外的模型）

- 写法：`--models <别名>@api`；配 `api路由.json`（base + models 映射）+ `export BENCH_API_KEY=...`
- 限制：无工具链，M3 记 fail:api-no-tools；密钥禁落盘

## 通道B（ZCode workflow，仅 GLM 思考档位对比时启用）

- GLM-5.3 / GLM-5.3-Flash × low/high/max（ListModels 的 provider/model$level）
- 用法见 skill-bench wiki 执行矩阵.md §跑法B
