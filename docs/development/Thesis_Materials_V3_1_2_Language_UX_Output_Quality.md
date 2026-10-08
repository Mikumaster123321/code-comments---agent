# V3.1.2 Language / UX / Output Quality 论文工程素材

V3.1.2 RELEASE_CANDIDATE

## 1. 文档定位

本文整理 V3.1.2 的语言职责、交互信息架构、错误安全与模型输出合同，可用于毕业论文工程章节、HCI/UX 讨论和维护版本案例分析。它不是新的 retrieval 实验结果，不改变 V3.1.0 RQ1–RQ4、Query、Ground Truth、Grade、ranking semantics 或 Formal artifact。

- 版本：`3.1.2`
- 状态：IMPLEMENTATION COMPLETE / AWAITING FINAL QA
- 开发分支：`v3.1.2-dev`
- authoritative main branch point：`2036cb6c82860b9bf8229ecac0f4d4add420855d`
- Scope Freeze commit：`139833f`
- Prompt Contract commits：`2192293`、`d12d800`
- tag / push：均未执行
- V3.2：NOT STARTED

## 2. 问题背景与研究意义

原界面把 UI Language 同时用于界面文案与生成结果，Provider 设置成功容易被理解为连通性已验证，空输入也可能先触发网络预检。输出 heading、Diff、API 文档和分析报告混合中英文，失败运行还可能保留上一轮结果。Prompt 直接拼接源码且翻译与 style rewrite 语义混合，模型空响应或异常 wrapper 可能被清理器静默接受。

这些问题不改变检索算法，却影响用户对系统状态、语言意图和输出可信边界的理解。V3.1.2 将其作为 maintenance release 的工程与 HCI 质量问题处理。

## 3. 冻结范围与实现

| Item | 工程处理 | 状态 |
| --- | --- | --- |
| V312-UX-01 | Task-first UI、Provider advanced 折叠、相关 style 单显、四态运行状态、空状态与无任务 Cancel disabled | COMPLETE |
| V312-LANG-02 | UI / Output / Programming Language 三者独立；首次默认相同，此后 UI 切换不改 Output | COMPLETE |
| V312-PROVIDER-03 | Settings applied 与 connectivity verified 分离；说明 key/env/Base URL/Azure/Custom 约束 | COMPLETE |
| V312-ERR-04 | local validation before ping、三语稳定错误码、无原始异常/secret/绝对路径、失败清空旧输出 | COMPLETE |
| V312-OUT-05 | 现有 API docs、Diff、analysis、status、empty state 本地化；恢复 Copy | COMPLETE |
| V312-PROMPT-06 | 固定 data delimiter、标识符保留、摘要合同、翻译/改写分流、响应 fail closed | COMPLETE |
| V312-TEST-07 | 新增 29 项离线合同测试，覆盖 mock prompt/cleanup/formatter/UI source contract | COMPLETE |

## 4. 语言职责模型

UI Language 只控制组件 label、help 和状态 copy。Output Language 控制 Python docstring、Java Javadoc、摘要、API documentation presentation 和分析报告。Programming Language 只控制 Python/Java parser、style 控件与代码 fence。三个选择互不替代。

首次打开时 Output Language 与默认 UI Language 同为中文。之后 UI Language 的 change callback 只更新 Output Language 的 label/help，不设置其 value，因此不会仅因界面切换而翻译或重写源码既有注释。Workspace 保存/恢复独立保存 Output Language 与 rewrite 开关。

## 5. UX/HCI 工程贡献

Provider 设置被置于默认关闭的 advanced accordion，降低首屏配置负担。Python 与 Java style 控件依据 Programming Language 单显。单文件 Cancel 在 Idle 时禁用，只在 Running 时启用；结果区提供明确 empty state。当前运行若在本地验证或 Provider 预检失败，会显示 Failure / CURRENT RUN FAILED 并清空代码、文档、Diff 和大纲，避免旧成功结果被误认成本轮结果。

Provider client 构造只产生“设置已应用、连接未验证”；只有实际 preflight ping 成功才显示 connectivity verified。Canonical Provider/Model ID 未翻译或修改。

## 6. Prompt 与输出安全合同

源码放在固定 `<SOURCE_CODE>` 边界中，既有注释放在 `<EXISTING_DOCUMENTATION>` 边界中；Prompt 明确边界内是 untrusted data 而不是待执行指令。目标语言只作用于自然语言，identifier、API、type、exception 与 library 名保持原样。

既有注释提供 translation only 与 translation + style rewrite 两种行为；后者默认开启以兼容历史行为。Java minimal 被冻结为 short Javadoc，因为 annotator 的真实管线始终以 `/** ... */` 包裹正文，改为 `//` 会破坏现有插入合同。摘要固定为一个简洁段落、最多四个完整句子，不再使用依赖中文计数的“200字以内”。

cleanup 只接受纯正文、一个完整 fence 或一对完整 docstring/Javadoc wrapper。空响应、未闭合/多个 fence、残留三引号、非法 `*/`、额外前言、traceback、secret-looking 内容或本地绝对路径均 fail closed，并映射为稳定用户错误。

## 7. 输出格式与兼容性

Python 与 Java API formatter 接受 presentation language，本地化标题、目录、Class/Function/Method display label、class note 和 empty state，同时保留 anchor、signature、identity 和正确 code fence。Diff 本地化统计和 Before/After copy；Python analysis 本地化既有复杂度、深度、长度、参数与类型注解事实，不新增 severity、recommendation 或 evidence schema。

Processor 公共五元组不变；新增 `rewrite_existing` 仅为末尾可选参数，默认 `True`。Provider/Model ID、BYOK、下载、batch、session persistence、ZIP naming、Python/Java 支持均保留。

## 8. 测试证据

| Validation | Result |
| --- | ---: |
| V3.1.2 targeted + existing LLM contract | 35 passed |
| Processor / Provider directed regression | 27 passed |
| Production profile | 198 passed |
| Experiments profile | 240 passed |
| Full profile | 951 passed |

测试全部离线，不调用真实 Provider、不使用真实 API key、不下载模型。当前 Anaconda Python 3.13.5 在 import Gradio 时经 IPython / rlcompleter 触发宿主 SIGSEGV；因此 create_ui smoke 标记为 HOST LIMITATION，未伪造 PASS。Python syntax compile 与不导入 Gradio 的 UI source contract 均通过。

## 9. Formal immutability

- execution revision：`2749969cd3a2d4d6e1e8d81160eebd5fb360879b`
- artifact identity：`acd8f464793cd7d5b15e3ffbd4d13207a0ce8edac7235d306f6d8711529559a3`
- artifact SHA-256：`2ac32989ad17407ac03948758d7ce9b6dd9615a7bfbb31beaf812cc30915ed41`
- retrieval ranking impact：NO
- Formal result impact：NO

## 10. 限制与后续门禁

本版本没有新增 Code Review、Optimization/Refactoring、Project Intelligence/Evidence surface，也没有创建新的 severity/location/recommendation/evidence 语义。Final QA 仍需独立复核三语人工矩阵、推荐 CPython 3.10 环境的 Gradio build smoke、文档一致性和候选 release gate。完成前不得标记 RELEASED，不得创建 tag 或 push。

## 11. 素材来源

- [Scope Freeze](V3_1_2_Language_UX_Output_Quality_Scope.md)
- [Prompt Output Contract](V3_1_2_Prompt_Output_Contract.md)
- [Development Report](Development_Report_V3_1_2.md)
- [Release Notes](../release/Release_Notes_V3_1_2.md)
- [README](../../README.md)
