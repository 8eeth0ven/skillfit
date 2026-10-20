# 网站运维（项目侧资产，不属 llm-wiki / skill-bench）

定位：**skill × 模型兼容性榜单**——"这个 skill 哪个模型用效果最好"的唯一中文出处。人流 + 评测覆盖量 = 护城河。

## 数据流水线

```
bench.py run → score → agg（报告/*-聚合.json）→ bench.py site → 网站/{index.html,data.json,skills/}
→ 扔 GitHub Pages / Cloudflare Pages / Vercel（纯静态，零成本）
```

每次重评后重跑 `agg + site` 再 push 即可，data.json 是唯一数据源。

## 护城河动作（按优先级）

1. **投稿通道**（核心）：skill 作者提交 SKILL.md + 3 个任务 → 你跑 N×N → 上榜。覆盖量随投稿滚雪球，评测库存别人抄不走
2. **可嵌入徽章**：给作者一段 `<img src=".../badge/<skill>.svg">`（"skill-bench 认证：最佳搭配 kimi-k3-2 · SkillScore 87"），作者挂自己 README = 免费反链
3. **固定重评节奏**：新模型发布 48h 内出横评（蹭模型发布流量）；每月全量重跑保新鲜
4. **明暗两榜**：明榜=SkillScore；暗数据=N×N 方阵 + 判官偏差表（方法论页公开口径，建立可信度）
5. **API/RSS**：静态 data.json 天然可被别人拉取，先占「评测数据源」心智

## 与现成体系的差异位（外部对比详见对话结论）

- SkillsBench / agent-skills-eval 等现成框架：单判官/自评居多、英文生态、**自认未做长度匹配对照**
- 本站差异：**N×N 跨厂商交叉盲评 + 中文 skill 生态 + 按模型推荐 skill**（不是评模型，是评「skill×模型配对」）
- 方法论护城河（别人抄不走的口径）：**M4 等长对照拆掉长度安慰剂**（SkillsBench 论文自认的坑，我们做了）、**家族去重票**（同家族判官只计一票）、**触发正负例准确率**（不只命中率）、断言层+判官双层互证、发布榜 `--trials 3`

## 红线

- 映射表/未匿名数据禁上站；判官 prompt 口径全公开（可信度即品牌）
- 受控/非受控通道、同源判官，一律在方法论页披露
