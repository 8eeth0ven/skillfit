# 线程必读（Skills&Model-Benchmark）

> 每次进线程先读本文 + `~/.zcode/skills/skill-bench/知识库/必读短表.md`。全流程纪律认 skill-bench wiki，本文件只管状态。

## 当前状态（2026-10-09 晚）

- 阶段：**首个 3×3 矩阵在跑 + 首次采集建库在跑**
- 3×3 深评：humanizer × {deepseek-v4.1-flash(CLI), glm-5.3-flash(CLI), space-bunny(CLI)} × M1/M2/M3/M4；跑完自动 score+agg
- 采集：`collect.py --update --min-stars 1000 --trending --seed 1000`（高星线 1k + 趋势线，自动建快扫题）
- 每日 cron 已挂：automation-97745d94（09:00 采集+快扫，密钥走 密钥.env）
- API 通道已验证：glm-5.3-flash@api 直连 OK（双 key 轮换）

## covered

- [x] skill-bench 全套（wiki 7 篇 + bench.py v3/doctor·check·run·score·agg·cross·site + collect.py）
- [x] humanizer T01-T04 种子（含触发负例 + 断言层，自测通过）
- [x] 三维 cross 命令 + 网站渲染（N×N×A，第一个为基准）
- [x] 密钥.env（600，BENCH_API_KEYS 双 key）

## 队列（按序）

1. [ ] 收割 3×3 报告（结果在 报告/*-humanizer.md）
2. [ ] 采集完成后：快扫首批（4 生产者 M2：glm-5.3-flash@api / glm-5.3@api / deepseek-v4.1-flash / space-bunny）
3. [ ] 快扫榜出来 → 挑 top 技能归功能组 → 造深评题（Oracle 门禁）→ cross 对基准
4. [ ] 首批深评过审 → bench.py site → 网站上线
5. [ ] 每日 cron 观察 3 天，调阈值（趋势线 200 星/60 天）

## 纪律提醒

- 快扫层 = 通用题初筛；深评层才进 SkillScore 榜单口径
- 映射表禁外传；密钥.env 禁上传；改 rubric 两侧同步
