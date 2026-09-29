---
description: 标准报告生成 — 按用户惯例出 docx（封面/目录/图表注/可转PDF）
argument-hint: <报告主题与素材位置，如：把本次网药结果整理成调研报告>
---

生成报告：$ARGUMENTS

用 documents skill（docx）生成，遵循用户惯例：
1. 结构：封面（标题/作者/日期占位）→ 目录 → 正文（编号图表，图注下置）→ 局限性小节；
2. 图：来自本次分析的产物，白底；如需新图先走 r-plot（/plot，morandi 配色）；
3. 文献引用必须真实可溯源（用 lit-scout 工具核 DOI）；
4. postcheck：页脚页码、无 U+FFFD 乱码、图题对应；
5. 转 PDF 用 LibreOffice（或 Word COM——中文文件名先复制成 ASCII 临时名）；
6. 中文正文；报告语言与既往交付一致（正式书面体）。
