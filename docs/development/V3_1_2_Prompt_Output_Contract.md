# V3.1.2 Prompt Output Contract

状态：FROZEN  
发布门禁：V3.1.2 RELEASED
适用版本：V3.1.2  
适用范围：docstring、Javadoc、代码摘要、既有注释翻译/改写，以及 LLM 响应清理  
生效前提：本契约必须先于任何 V3.1.2 prompt 实现变更进入 Git 历史。

## 1. 目的

本契约将自然语言生成行为约束为可测试、可审计的输入—输出边界。它不改变代码检索、排序、上下文构建、Formal、query、ground truth 或评分逻辑，也不引入代码审查、优化建议、项目级推理或证据生成能力。

## 2. 输入边界与源码隔离

所有生成 prompt 必须同时满足以下规则：

1. 系统指令与用户源码使用稳定、显式、成对的边界标记分隔。
2. 边界标记在同一类任务中保持固定，不根据源码内容动态变化。
3. prompt 明确声明：边界内内容是待处理的数据，不是可执行指令；其中出现的要求、角色、system prompt、工具调用或输出格式指令一律不得覆盖系统任务。
4. prompt 不拼接 API key、secret、完整本地绝对路径、内部异常、traceback 或供应商原始错误。
5. 生成任务只接收完成当前函数、方法、类或摘要所需的最小源码片段。

冻结边界格式：

```text
<SOURCE_CODE>
...source as untrusted data...
</SOURCE_CODE>
```

若任务包含现有注释，使用独立边界：

```text
<EXISTING_DOCUMENTATION>
...documentation as untrusted data...
</EXISTING_DOCUMENTATION>
```

### 2.1 Prompt inventory 与变更分类

V3.1.2 只允许修改 `llm_service.py` 中现有的六类 prompt，不增加新的模型任务：

| Prompt | 现有职责 | V3.1.2 分类 | 允许变更 |
|---|---|---|---|
| Python docstring generation | 为函数/类生成 docstring | MODEL-BEHAVIOR-SENSITIVE | 加入稳定边界、目标语言和标识符保留规则；保持既有 style |
| Python existing-docstring translation | 翻译并按既有选择重排 | MODEL-BEHAVIOR-SENSITIVE | 显式区分 translation only 与 style rewrite |
| Python summary | 概述模块、函数/类和依赖 | MODEL-BEHAVIOR-SENSITIVE | 改为语言中立的长度/结构合同 |
| Java Javadoc generation | 为方法/类生成 Javadoc | MODEL-BEHAVIOR-SENSITIVE | 加入稳定边界；冻结 minimal 为 short Javadoc |
| Java existing-Javadoc translation | 翻译并按既有选择重排 | MODEL-BEHAVIOR-SENSITIVE | 显式区分 translation only 与 style rewrite |
| Java summary | 概述模块、方法/类和依赖 | MODEL-BEHAVIOR-SENSITIVE | 与 Python 使用同一高层摘要合同 |

响应去除外层 fence、三引号或 Javadoc wrapper 属于 FORMAT-ONLY，但新增拒绝条件会改变失败行为，因此同样需要离线契约测试。界面标签、帮助文本和结构化输出 heading 的翻译属于 PURE-COPY，不得改变模型输入或分析语义。

## 3. 输出语言规则

输出语言由独立的 Output Language 决定，支持中文、English、日本語。UI Language 仅控制界面文案，两者互不联动；Programming Language 仍独立控制解析和注释格式。

自然语言说明必须使用选定的 Output Language，但下列技术标识必须保持原样，不得翻译、音译或改写：

- identifier、函数名、方法名、类名、参数名和变量名；
- API、library、package、module、framework 和 protocol 名称；
- type、exception、error code、HTTP status 和 CLI flag；
- 路径片段、配置键、环境变量名和代码字面量。

除语言差异外，同一输入的三种输出必须表达同一事实范围，不得因语言选择新增严重性、位置、建议、证据或功能推断。

## 4. 任务级输出契约

### 4.1 Python docstring

- 只返回 docstring 正文，不返回 Markdown fence、解释、前后缀或 Python 引号。
- 保持项目现有 style 选择，不新增 style。
- 内容只能描述源码可支持的职责、参数、返回值、异常和副作用。
- 不得发明类型、异常、调用关系、性能结论或未实现行为。

### 4.2 Java Javadoc

- 只返回 Javadoc 正文，不返回 Markdown fence、解释或 `/** ... */` 包装。
- V3.1.2 使用最小、短 Javadoc：一段简洁摘要，并仅在源码明确支持时包含必要的 `@param`、`@return`、`@throws`。
- 不扩展为长篇 API reference，不发明 contract、异常或线程安全结论。

### 4.3 代码摘要

- 摘要只描述输入源码的可观察结构和职责。
- 摘要内容保持 language-neutral：输出语言变化只能改变自然语言表述，不能改变事实集合、严重性、评价或建议。
- 输出为一个简洁段落，最多四个完整句子；不使用依赖中文“字数”的限制，也不要求项目符号数量。
- 不输出代码审查、优化方案、项目级洞察、证据等级或评分。

### 4.4 既有注释翻译与改写

该行为由显式布尔选择控制：

- Translation only：保持原意和信息范围，仅将自然语言翻译为 Output Language；不得重组为选定 style，不得补充新事实。
- Translation + style rewrite：先保持事实范围，再按当前 Python docstring/Javadoc style 组织表达；不得补充源码和原注释均不支持的事实。

默认值为 Translation + style rewrite，以保持既有行为兼容。界面必须让用户看见并理解当前选择；实现层必须使用同一布尔值贯穿单文件、批处理和工作区流程。

## 5. 响应清理与拒绝条件

响应清理只允许移除模型偶发添加的外层 Markdown fence、语言标签、docstring/Javadoc 包装和首尾空白。清理器不得通过猜测来修复结构不明的响应。

满足以下任一条件时，响应必须被拒绝，并转换为稳定、可本地化的用户错误；不得把原始响应直接展示或写回源码：

1. 响应为空，或清理后为空；
2. Markdown fence 未闭合、嵌套或清理后仍残留 fence；
3. Python docstring 正文仍包含外层三引号边界；
4. Javadoc 正文仍包含 `/**`、`*/` 等外层或注入式边界；
5. 响应包含明显的 traceback、system prompt、API key/secret 回显，或要求执行工具/命令的控制文本；
6. 响应结构与当前任务所需的纯正文契约不兼容。

拒绝后的失败路径必须清除本次运行的当前输出，且不得泄露供应商原始消息、内部异常、traceback、secret、API key 或本地绝对路径。

允许的模型输出 wrapper 仅限一个完整、闭合的 Markdown code fence，或当前任务对应的一对完整 docstring/Javadoc 外层包装；清理后只能留下纯正文。额外解释、前言、结语、多个 fenced blocks、混合代码与正文、控制指令或上述禁止内容均视为不兼容输出。

## 6. 错误与状态契约

本地输入验证先于任何 provider ping 或 LLM 请求。用户只看到稳定错误代码对应的中文、English 或日本語消息。Provider 设置保存/应用只表示 settings applied；只有实际 ping 成功才允许显示 connectivity verified。

运行状态固定为 Idle、Running、Success、Failure；取消可作为 Running 的终止结果展示，但不改变四态主契约。无活动任务时取消按钮必须不可用。

## 7. 兼容性边界

- 保持 provider ID、model ID、processor 的既有核心结果形状和默认调用方式兼容。
- 新参数必须具有兼容默认值；未显式传入 Output Language 或 rewrite 选择的内部调用保持 V3.1.1 可接受行为。
- 不调用真实 provider，不下载模型；所有契约验证均使用 stub、monkeypatch 或纯函数测试。

## 8. 最低离线测试要求

V3.1.2 测试至少覆盖：

1. 三种 Output Language 与 UI Language 独立；
2. 固定源码边界和 source-as-data 指令存在；
3. identifier、API、type、exception 和 library 保留规则存在；
4. Python 与 Java 输出清理的合法路径；
5. 空响应、残留 fence、三引号/Javadoc 边界和明显敏感内容被拒绝；
6. Translation only 与 Translation + style rewrite 的 prompt 语义不同且默认兼容；
7. 摘要 prompt 不要求 review、severity、recommendation 或 evidence；
8. 本地验证失败时 provider ping 和 LLM stub 均未被调用；
9. 失败结果为本地化稳定错误，不包含 traceback、secret 或本地绝对路径。

### 8.1 Mock-provider cases

离线 provider stub 必须覆盖：正常纯正文、合法完整 wrapper、空字符串、仅空白、未闭合 fence、多个 fence、非法 `*/`、额外解释、看似 prompt injection 的源码，以及抛出包含 secret/绝对路径的内部异常。测试只观察最终稳定结果和错误代码，不保存或快照 secret。

### 8.2 Golden cases

冻结以下 prompt 事实而非整段易碎字符串：

- Python 与 Java generation prompt 均包含准确一次 `<SOURCE_CODE>` / `</SOURCE_CODE>`；
- translation prompt 均包含准确一次 `<EXISTING_DOCUMENTATION>` / `</EXISTING_DOCUMENTATION>`；
- prompt 明确把边界内内容声明为 untrusted data，并要求忽略其中指令；
- 中文、English、日本語分别映射到明确 TARGET OUTPUT LANGUAGE；
- prompt 明确保留 identifier、API、type、exception 和 library 名称；
- translation-only prompt 不包含 style 重写要求，rewrite prompt 包含所选既有 style；
- Java minimal 明确为 short Javadoc，仍由现有 annotator 包裹为 `/** ... */`；
- summary 明确为一个段落、最多四句，且不含“200字以内”。

### 8.3 Manual review matrix

Final QA 使用同一小段 Python 与 Java 样例，按下表人工核对；不要求真实付费调用，本轮若无法安全运行模型则记录为待 Final QA：

| Programming Language | Output Language | Task | Review focus |
|---|---|---|---|
| Python | 中文 / English / 日本語 | generation | docstring style、技术标识原样、无 wrapper |
| Python | 中文 / English / 日本語 | translation only / rewrite | 原意范围、两种行为可区分 |
| Java | 中文 / English / 日本語 | standard / minimal | Javadoc 标签、minimal 为短 Javadoc |
| Python / Java | 中文 / English / 日本語 | summary | 同一事实范围、单段最多四句、无 review/建议 |
| Python / Java | 任一 | malicious-looking source | 源码内指令不改变任务和输出格式 |

## 9. 变更控制

本契约在 V3.1.2 实现期间冻结。若实现需要改变任一输入边界、语言规则、翻译/改写语义、Java 最小格式或拒绝条件，必须先修改并审阅本文件，再修改 executable code；聊天记录不构成替代 Source of Truth。
