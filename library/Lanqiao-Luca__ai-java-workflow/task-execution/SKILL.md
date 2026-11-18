---
name: task-execution
description: 为责任 Agent 适配执行计划、已有运行器与证据返回；用于已选择的 Workflow、Loop 或 Graph，不负责 Brain 路由或自动安装。
---
**目的**：把责任 Agent 已选的合同与实例计划适配到现有执行工具，返回真实结果和恢复点。

**适用于**：已经选定 Workflow、Loop 或 Graph 且授权、环境和输入明确的执行适配。

# 执行计划与工具适配

## 输入与规则来源

接收责任 Agent 已选择的合同、模板、当前工程/候选、写集、验收及预算。按[分层合同](../../standards/layering.md)、[接续规划](../../standards/delivery-planning.md)和[异常恢复](../../standards/recovery.md)核前提。Standards 与 [Tools](../../tools/README.md)平级：前者提供规则与验收方法，后者提供代码和执行接口，由本 Skill 组合适配。

执行文件创建和更新时消费[执行记录](../../standards/execution-records.md)；必要上下文过大时消费[执行单元拆解](../../standards/context-budget.md)。文档落盘交相应文档职责，不在这里复制写入规则。

## 适配步骤

1. 核所选执行文件的真实来源、格式与运行器支持范围。Markdown 计划由 Agent 按合同执行，不因填好模板就变成可直接运行的 JSON。
2. 将当前候选、授权、工具环境、剩余预算和输出位置交给明确支持的后端；输入/前提未满足不发起动作。
3. 按需定位[工作区与沙箱工具](../../tools/execution/README.md)、[Loop 判定](../../tools/loop_policy.py)、[巡检控制](../../tools/inspection_loop.py)、[缺陷控制](../../tools/defect_loop.py)或[目标图执行器](../../tools/goal_graph_run.py)。也可按[统一命令合同](../../docs/cli.md)使用[受限入口工具](../../tools/workflow_entry.py)运行五个固定案例，核请求/实现身份和安全检查点；不支持任意工作流定义。只使用合同支持的接口，不自行替换其候选、门禁或停止策略。
4. 交回实际命令/接口、退出状态、产物身份和未决。UNKNOWN 先核受理状态；不清零预算或用新运行身份重放未知动作。

## 输出与停止

输出当前实例、真实执行证据、失败/未运行范围、最早恢复点。程序返回、模型结论与业务验收分别记录；新模板没有自动运行保证。宿主调用权限检查仍由宿主落实，本 Skill 不提供身份拦截或后台进程。

返回：[Skills](../README.md)。
