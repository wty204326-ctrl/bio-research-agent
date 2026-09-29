---
name: lit-scout
description: 生物医药文献侦察兵。PubMed/OpenAlex 检索、按纳入标准批量筛选（>20篇自动扇出轻量模型）、结构化中文摘要表、主题调研综述、单篇精读与全文 PDF 获取、Zotero 入库。当用户要查文献/文献检索/文献调研/做综述/找参考文献/了解某主题研究进展/追踪文献/精读一篇/literature/papers 时使用。
---

# 文献侦察兵 lit-scout

生物医药文献的 检索 → 筛选 → 摘要 → 精读 流水线。
数据源以 `biomed` MCP 工具为主（结构化、可溯源），WebSearch 只作指南/新闻/灰产补充。

## 0. 任务分流（先判断，再行动）

| 用户意图 | 模式 | 动作 |
|---|---|---|
| "XX 有没有证据""查一下 XX" | 快速查证 | pubmed_search + openalex_search 各 10-15 条 → 直接给结论+引文，不用完整流程 |
| "帮我调研 XX""XX 研究进展" | 系统检索 | 走 §1-§4 完整流程 |
| "精读这篇 X（DOI/PMID/标题）" | 单篇精读 | 取全文（references/pdf-acquisition.md）→ 中英对照精读笔记 |
| "每日文献/今天的文献" | 每日追踪 | 见 references/daily-tracker.md（已有 9 点定时任务，勿重建） |

## 1. 构建检索式

- 一律英文检索。主题拆成概念组：组内 OR 同义词（含 MeSH 习惯词、缩写、全称），组间 AND。
- PubMed 语法（pubmed_search）：`quercetin AND "acute lung injury"[Title/Abstract]`、年限 `AND 2023:2026[dp]`（或直接用工具的 from_year/to_year 参数）。
- OpenAlex（openalex_search）：自然语言 search 参数即可，被引排序用它。
- 两库并行检索、DOI 优先去重、标题模糊匹配合并。
- **检索式必须写进最终输出**（可复现性）。

## 2. 检索执行

- 首选 `mcp__biomed__pubmed_search`（biomedical 权威）+ `mcp__biomed__openalex_search`（覆盖面+被引数）。
- `europepmc_search` 为备用（服务近期不稳，503 时直接换前两者）。
- 需要预印本时补 WebSearch（bioRxiv/medRxiv）。

## 3. 批量筛选 —— 模型调度策略（核心）

按规模分档，成本与质量平衡：

- **≤20 篇**：当前会话模型直接读摘要筛选，不分发。
- **>20 篇**（系统检索/大窗口）：用 CreateWorkflow 扇出——
  - 每个子代理分 20-30 篇，只传 标题+摘要+DOI 列表；
  - `subagent_model` 指定 `account:bigmodel-individual-coding-plan/GLM-5.3-Flash`（轻量快档，筛选任务够用）；
  - 子代理提示词必须包含：研究问题、纳入标准、排除标准、输出格式（每篇一行：`DOI | 0-2分 | 一句话结论`）；
  - **主模型（本会话）负责**：汇总、终表、边界裁决、证据综合。
- **深度精读、综述写作、机制推理**：始终主模型，不下放。

## 4. 输出规范（系统检索）

结构化表格，每篇一行：

| # | 标题（原文） | 年份 | 期刊 | 类型 | 被引 | 核心发现（中文 1-2 句） | DOI |

- 类型分：研究/综述/META/预印本（预印本必须标注，不可与同行评审混排不加说明）。
- 表后附三段：① 证据概览（领域共识/争议/空白，3-5 句）② 检索式与检索日期 ③ 所用数据库。
- 正文中文，标题保留英文原文。

## 5. 全文获取

按 references/pdf-acquisition.md 三条路径（OA 三连查 → PMC PoW → 浏览器 fetch），仅走合法渠道。

## 6. Zotero 入库（用户要求时）

凭据与格式要求见 references/daily-tracker.md；bioRxiv 分号作者串必须包 `{"creatorType":"author","name":...}`。

## 边界

- 不编造文献：每一条必须来自工具返回，DOI/PMID 原样透传。
- 摘要翻译忠于原文，不确定的地方标注"摘要未明确"。
- 涉及临床结论时区分证据等级（体内/临床/机制/生物信息学预测）。
