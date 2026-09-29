---
description: 孟德尔随机化 — 药物靶点MR设计/数据源/实跑/共定位/功效门槛
argument-hint: <MR任务，如：XX靶点pQTL对YY结局做两样本MR>
---

MR 分析：$ARGUMENTS

按 mr-analyzer skill 执行（**先读 references/mr-manual.md**）：
1. 数据源只从手册可用表选（FinnGen R12/BBJ/eQTLGen 开放；UKB-PPP FTP 空、eQTL Catalogue 410、deCODE 申请制）；
2. WSL 实跑复用 `<你的 MR 脚本目录>/` 脚本架构；下载用 dl.sh 分段（禁流式管道）；coloc 用 rcoloc env（--override-channels）；
3. harmonize 按位置对齐（37/38 坐标坑）；敏感性三件套；功效门槛 se∝1/√cases；
4. 森林图纯英文、白底；阴性如实写；方向反先验的显著默认噪声。
