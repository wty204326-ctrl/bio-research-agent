---
description: 生信任务 — 转录组/单细胞/富集/机器学习（WSL 执行）
argument-hint: <任务描述，如：对 <你的数据集> 做差异分析>
---

执行生信任务：$ARGUMENTS

按 bio-research-agent 插件的 bio-runner skill 执行。**动手前必读**其 references：

1. `wsl-ops.md` —— 任何 WSL 命令前（base64 传脚本、setsid nohup、VM 崩溃排查）；
2. `r-analysis-pitfalls.md` —— 写 R 代码前（topTable/FetchData/编码/白底图等坑）。

要求：计算直接 Bash 顺序执行不用子代理；长任务脱离会话+轮询日志；结果目录 `<项目>/{data,figures,report,wsl}`；所有图 `bg="white"`；方法学红线（嵌套 CV、训练集 z-score、BH 饱和双轨披露）不越线。
