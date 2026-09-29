---
name: bench-quant
description: 湿实验定量分析全家桶。Western Blot 灰度定量、qPCR ΔΔCt、ELISA 4PL 标准曲线、IHC(DAB)/IF 图像定量、克隆形成计数、PCR 引物设计(primer3)、样本量/效能计算、GraphPad .pzfx 生成。当用户要：WB 定量/qPCR/ΔΔCt/ELISA 标准曲线/浓度计算/IHC 定量/阳性面积/细胞计数/克隆计数/集落/引物设计/样本量/检验效能/GraphPad/pzfx 时使用。
---

# 湿实验定量 bench-quant

三个脚本都在本 skill 的 `scripts/` 目录（Windows Python 3.12，PIL/numpy/scipy 已装）。所有输出图纯白底。

## 1. WB 灰度定量（wb_quant.py，两步走）

```
# 第一步：自动检测泳道+条带
python scripts/wb_quant.py detect --img 膜图.png --lanes 6 --out-dir out
# → out/preview.png（红框+编号）+ out/rois.csv
# 第二步：校验后定量
python scripts/wb_quant.py quant --img 膜图.png --rois out/rois.csv \
    --samples samples.csv --ref-band 2 --ctrl Con --out-dir out
# → densities.csv / results.csv / figure.png
```

关键规则：
- **detect 后必须用 Read 工具看 preview.png**：条带框错/漏/多 → 直接改 rois.csv 坐标（表头 lane,band,x0,y0,x1,y1）再 quant，不用重跑 detect。
- band 序号 = 泳道内**自上而下**；`--ref-band` = 内参条带（actin/GAPDH 通常最低）。
- samples.csv：`lane,group,replicate` 三列；生物学重复 = 不同 lane。
- 同排条带自动统一 ROI 高度（ImageJ 惯例）。
- **饱和条带不可定量**：图上大片纯黑 → 告诉用户换非饱和曝光重扫，这不是软件能救的。
- 背景 = ROI 外扩环中位数；扣除后 ≤0 的 ROI 会在 densities.csv 标出（多半框到空位）。
- 统计：两组 Welch t；≥3 组 ANOVA + 组间 Welch + Holm 校正。
- 化学发光若 16-bit TIFF 更好，8-bit PNG/JPG 也能跑。
- 已验证：合成膜回收误差 <3%（检测→定量全自动链）。

## 2. qPCR ΔΔCt（qpcr_ddct.py）

```
python scripts/qpcr_ddct.py --data ct.csv --ref GAPDH --ctrl Con --out-dir out
```

- 长表（Sample,Group,Gene,Ct）/宽表（首列样本，列=基因）自动识别；CSV/XLSX 皆可。
- 技术重复同名 Sample+Gene 自动取均值；SD>0.3 或 Ct≥35 写 warnings.txt。
- **统计在 ΔCt 层做**（规范做法），不在 fold change 上 t 检验；图误差棒 = ΔCt 95%CI 变换。
- 输出 per_sample.csv / summary.csv / figure.png。

## 3. GraphPad 输出（make_pzfx.py）

```
python scripts/make_pzfx.py --data values.csv --title "WB fold change" --out wb.pzfx
```

- 输入长表 `category,group,value`（行=基因/蛋白，列=组，重复值=多行）或宽表（首列类别，重复列同组名）。
- 生成 Grouped 数据表（重复子列）；**双击在 Prism 10 打开 → 选中表 → Insert new graph 即可出图**。
- ⚠️ v0.2.0 生成的是数据表（无内嵌图）；首次使用请用户打开验证一次兼容性，打不开把文件退回调试。
- 同时保留脚本自出的 figure.png 作即时预览；要出版级样式在 Prism 里完成（用户偏好 GraphPad 风格）。

## 4. ELISA（elisa_4pl.py，合成验证回收误差 ≤5%）

```
python scripts/elisa_4pl.py --std std.csv --samples smp.csv --out-dir out
```
- std：`conc,od` 复孔重复行（含 0 孔）；samples：`sample,od[,dilution]`；闭式浓度反算；
- R²<0.99 告警；复孔 CV>15% 告警；OD 出曲线范围标记外推不可靠。

## 5. IHC/IF 定量（ihc_quant.py，合成验证面积误差<1pct、核检出 89/90）

- DAB：Ruifrok 去卷积（注意矩阵转置 od@(M⁻¹)ᵀ，直 cast uint8 会全 0）→ Otsu；IF：通道模式；
- `--count-cells` watershed 核分割 + 阳性核比例；`--roi` 先裁后算；
- 阳性判定全局 Otsu 偏保守（弱染色算阴），可按 cells.csv 的 marker_mean_u8 人工定阈。

## 6. 克隆计数（colony_count.py，42 合成→39，重叠合并为已知限制）

- 单孔图直接跑；多孔板先 figops.py crop；暗底亮斑 `--invert`。

## 7. 引物设计（primer_design.py，primer3-py）

- `--qpcr` 模式 70-200bp；Tm 目标默认 60±3；输出 CSV；跨外显子由用户确认。

## 8. 样本量（samplesize_calc.py，statsmodels）

- means/paired/props/anova/corr 五类；`--n` 反算效能；基准已验证（d=1→17/组）。

## 9. 药代动力学 PK（pk_nca.py，合成 IV/口服验证误差 ≤4%）

```
python scripts/pk_nca.py --data ct.csv --dose 100 --dose-unit mg --route ev --f 0.8 --fit-1cmt --out-dir out
```
- ct.csv：`time,conc[,subject][,group]`（时间 h）；route iv=静脉 / ev=血管外（输出 CL/F、Vz/F；给 --f≠1 另出真值列）
- 输出：Cmax/Tmax/AUC₀₋ₜ（linear-up/log-down 梯形）/λz（终末段自动选点 adj R² 最大，R² 与点数入表）/t½/AUC₀₋∞/AUMC/MRT
- **AUC 外推 >20% 自动警告**（末点不足，只报 AUC₀₋ₜ）
- `--fit-1cmt` 附加一房室拟合（IV bolus / 一级吸收，出 ke/ka/R²）
- curves.png：线性+半对数双面板（个体淡线+均值±SD，白底）

## 通用边界

- 数据先看再算：样本数、分组、缺失情况先报告给用户确认。
- n<3 的组只做描述不做检验；p 值报告到 3 位有效数字。
- 图内文字一律英文（字体渲染规范），标题可中文写在图外/回复里。
- **绘图分工**：脚本自出的 figure.png 是快速预览；出版图三条路——① r-plot skill（156 模板+莫兰迪配色，`/plot`）② Prism（pzfx 打开后编辑）③ 用户点名的方式。
