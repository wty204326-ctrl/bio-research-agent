---
description: 本地 PDF 库问答 — 建索引+检索+原文引用作答
argument-hint: <PDF文件夹+问题，如：Research/pdfs 里 铁死亡与多胺的关系>
---

PDF 库问答：$ARGUMENTS

按 pdf-qa skill 执行：
1. 无索引先建：`scripts/pdf_index.py --dir <文件夹> --out <文件夹>/pdf_index.json`（大库后台跑）；
2. 检索（英文关键词）：`scripts/pdf_query.py --index ... --q "..." --k 6`；
3. 主模型读块作答，**每条论断标（文件名 p页码）**；需要更多上下文用 Read 打开对应 PDF 深挖；
4. 检索无命中 → 换关键词一次，仍无 → 明说库里没有，不脑补。
