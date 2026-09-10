# 什么是结构化的 Prompt

不同 AI 厂商（如 OpenAI、Anthropic、Google等）虽然都支持自然语言输入，但在结构化 Prompt（提示词）的文本格式、偏好标签和使用方式上各有千秋。以下是主流 AI 厂商的结构化 Prompt 格式与使用方式对比

---

## 核心对比一览

| **厂商 / 模型系列** | **推荐的结构化格式** | **核心特色与常用标签** | **最佳使用方式** |
| ------------------ | ------------------ | --------------------- | --------------- |
| Anthropic (Claude) | XML 标签格式 | `<role>`, `<context>`, `<instruction>`, `<example>` | 严格区分数据与指令，强烈推荐少样本（Few-shot）示例。 |
| OpenAI (GPT-4o/o1) | Markdown / JSON | # H1, ## H2, - 列表, [System/User/Assistant] | 依赖清晰的层级结构。强模型更看重逻辑和约束条件的清晰度。 |
| Google (Gemini) | Markdown / 模块化 | Role:, Task:, Constraints:, Output Format: | 喜欢清晰的段落划分。适合处理长文本和多模态上下文输入。 |

---

## 各厂商详细格式与示例

### 1. Anthropic (Claude 系列) —— XML 标签标准

Anthropic 官方极力推荐使用 XML 标签 来构建 Prompt。Claude 对 XML 标签（如 `<tag></tag>`）非常敏感，能够精准识别复杂指令、背景资料和示例的边界。文本格式示例：

```xml
<system>
你是一个资深的金融数据分析师。
</system>

<instruction>
请分析以下用户提供的财报数据，并输出分析报告。
</instruction>

<constraints>
- 只能根据提供的 <data> 标签内的数据进行分析。
- 如果数据不足，请回答“无法分析”。
</constraints>

<examples>
  <example>
    <input>2025年营收增长10%，净利润下降5%。</input>
    <output>该公司陷入了“增收不增利”的困境，需要关注成本控制。</output>
  </example>
</examples>

<data>
{{用户输入的财报文本}}
</data>
```

- 使用方式：将结构化标签直接写在 Prompt 中。在处理长文本（Long Context）时，将参考资料用 `<docs>` 标签包裹起来，能显著降低模型“幻觉”。

### 2. OpenAI (GPT 系列) —— Markdown 层级与角色分离

OpenAI 的模型对 Markdown 语法（# 标题、- 列表、加粗）支持极好。同时，OpenAI 最早引入了 API 层面上的 ChatML（System/User/Assistant 角色分离） 结构。文本格式示例：

```markdown
# Role
你是一位精通跨国法律的合规官。

## Task
审查用户提交的合同草案，找出潜在的合规风险。

## Constraints
- 必须基于最新的 GDPR 规范。
- 风险点请按“高/中/低”进行分级。

## Output Format
请使用以下 JSON 格式输出：
{
  "risk_level": "高/中/低",
  "description": "风险描述",
  "suggestion": "整改建议"
}
```

- 使用方式：在 API 中，将“# Role”和“## Constraints”写入 System Prompt（系统提示词），将具体任务和待处理文本写入 User Prompt（用户提示词）。对于 GPT-4o 等模型，配合 response_format: { "type": "json_object" } 使用效果最佳。

---

## 结构化 Prompt 编写的核心技巧

尽管各厂商格式不同，但优秀结构化 Prompt 的底层逻辑是通用的：

- 角色定义 (Role)：赋予 AI 一个具体的身份（“你是谁”）。
- 上下文与任务 (Context & Task)：交代背景，明确核心任务（“要做什么”）。
- 负向提示与约束 (Constraints/Rules)：圈定边界，明确禁止事项（“不能做什么”）。
- 输出规范 (Output Format)：指定结构（如 Markdown 表格、JSON、指定字数）。
