---
description: IHC(DAB)/IF 图像定量 — 阳性面积/IOD/阳性细胞计数
argument-hint: <图像路径+需求，如：ihc.png DAB 染色统计阳性面积和阳性细胞比例，ROI(100,100,400,300)>
---

IHC/IF 定量：$ARGUMENTS

用 bench-quant skill 的 `scripts/ihc_quant.py`：
- DAB 模式（默认）：`--img X.png --mode dab [--roi x,y,w,h] --count-cells --out-dir out`
- IF 模式：`--mode if --marker <0/1/2/gray> --nuclei-channel 2`（DAPI=B）
- 原理：Ruifrok 去卷积 → Otsu 定阳性 →（可选）watershed 核分割 → 阳性核比例
- 报告：阳性面积%、平均光密度、IOD、细胞数/阳性率；overlay.png 给用户核对分割质量（Read 自查）
- 已知特性：阳性判定是全局 Otsu，**弱染色偏保守**；cells.csv 的 marker_mean_u8 分布可人工重定阈；合成图验证：面积误差<1pct、核检出 89/90。
