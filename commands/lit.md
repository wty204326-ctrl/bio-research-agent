---
description: 文献侦察兵 — 检索/批量筛选/结构化摘要/调研综述
argument-hint: <检索问题或主题，中英文均可>
---

处理文献任务：$ARGUMENTS

按 bio-research-agent 插件的 lit-scout skill 执行（用 Skill 工具加载；不可用则直接按其流程执行）：

1. 先判断任务类型：快速查证 / 系统检索 / 调研综述 / 单篇精读 / 每日追踪（分流到已有定时任务）；
2. 检索：`mcp__biomed__pubmed_search` + `mcp__biomed__openalex_search` 并行，DOI 去重；
3. >20 篇用 CreateWorkflow 扇出筛选，子代理模型 `account:bigmodel-individual-coding-plan/GLM-5.3-Flash`，主模型合成；
4. 输出：结构化中文表格（标题原文/年份/期刊/类型/被引/核心发现/DOI）+ 证据概览 + 检索式与检索日期；
5. 需要全文按 lit-scout 的 references/pdf-acquisition.md 走合法渠道。
