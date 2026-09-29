---
description: GEO 数据集检索 — GSE/样本数/平台/摘要/补充文件链接
argument-hint: <检索需求，如：小鼠 LPS 急性肺损伤的 scRNA 数据集>
---

GEO 检索：$ARGUMENTS

1. 构建英文检索式：`mcp__biomed__geo_search`（物种 [orgn]、限 Series 加 AND gse[ETYP]、单细胞可加 "single cell"[All Fields]）；
2. 结果列表：GSE | 样本数 | 平台 | 标题摘要 | 补充文件 FTP；
3. 按需求排序点评（样本量/分组设计/平台适配），推荐 2-3 个并说明取舍理由；
4. 要下载时按 bio-runner 的 wsl-ops.md 分段下载规范执行（GEO 大文件直连必坏）。
