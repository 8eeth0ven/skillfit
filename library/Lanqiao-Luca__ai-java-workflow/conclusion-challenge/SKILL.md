---
name: conclusion-challenge
description: 复核已形成的高影响技术根因或修复判断，组织竞争解释、共同证据矩阵、主动反证和敏感性分析；不因普通格式质疑触发，不自动取证或改业务。
---
**目的**：把重要技术判断适配成可追溯的反证报告，交回限定结论与最小补证。

**适用于**：责任 Agent 已接收原判断、当前候选、取证范围与预算的结论复核。

# 结论反证

消费 [CH01–CH04](../../standards/conclusion-challenge.md)，复用[诊断](../../standards/diagnosis.md)的原观察；需新增材料时只提出范围和区分问题，由当前取证职责取得。方法阈值不以凑解释或证据数量代替场景判断。

1. 绑定候选及原命题，标事实、推断、来源范围和已知缺口。
2. 使用同一证据集评估合理竞争解释，逐格填写关系与理由，保同源组及可靠性限制。
3. 实际尝试推翻最初首选，记录期待反例、动作与观察；未执行保 NOT_RUN，缺来源保 UNAVAILABLE，不把预期当结果。
4. 对决定性证据作移除分析，输出限定结论、尚存解释与下一责任。候选变化按原子回到失效点。
5. 若采用 JSON 合同，用[结构工具](../../tools/conclusion_challenge.py)的 `check(report, candidate_sha256)`；第二参数须由调用方核当前候选实际字节取得。返回 STRUCTURE_VALID 只表示表内结构完整，semantic_acceptance 始终 NOT_ASSESSED，pending_checks 明确保缺证。

可按调用方提供的报告空表保存；最小 JSON 字段与实际执行见[离线案例](../../workflows/examples/conclusion-challenge/README.md)。纯自然语言审查不强制序列化为 JSON。保存文档继续沿当前文档维护职责，不安装角色、不发请求或启动后台流程。

返回：[Skills](../README.md)。
