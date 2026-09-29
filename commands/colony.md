---
description: 克隆形成（集落）计数 — 平板图自动计数+尺寸分布
argument-hint: <平板图像路径，如：plate.png 六孔板第二孔计数>
---

克隆计数：$ARGUMENTS

用 bench-quant skill 的 `scripts/colony_count.py`：
```
python scripts/colony_count.py --img plate.png [--min-area 40] [--invert] --out-dir out
```
- 单孔图直接跑；多孔板大图先用 figure-forge 的 `figops.py crop --box` 裁出单孔再计数；
- 输出 colonies.csv（编号/坐标/面积/等效直径）、summary、overlay.png（红线标注，Read 自查）；
- 已知限制：**重叠集落会合并成一个**（合成验证 42→39）；密集板调 min-area 或人工补数；亮底暗斑默认，暗底亮斑加 --invert。
