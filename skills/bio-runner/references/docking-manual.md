# 分子对接执行手册（WSL Vina 管线）

## 环境

- WSL conda env **dock**：vina(Python API)/rdkit/openmm/pdbfixer/prody/meeko/openbabel（位于 `~/miniconda3/envs/dock`，2026-09 重建版；旧的 `docking` env 已随 VM 崩溃丢失）。
- PyMOL 渲染：conda env **pymol**，`pymol -cq` 无头模式可用。
- ⚠️ 包名坑：对接引擎包名是 `vina`（`autodock-vina` 不存在）；openmm 默认构建带 CUDA 依赖数 GB，CPU 机器只能接受或改 ADFR。

## 现成脚本（复制改造）

- `<对接矩阵脚本.py（参考思路，自备）>`（36 组矩阵架构）
- `<你的项目目录>/wsl/run_phn_dock.py`
- 制备流水线 01-06（`<制备流水线脚本目录>/` Windows 备份）：选链去杂 → pdbfixer 加氢 → meeko PDBQT → vina Python API 对接 → 相互作用分析 → PyMOL 出图

## 受体制备铁律

- **彻底去 HETATM（水/共晶配体/离子）再制备**：
  - meeko mk_prepare_receptor 遇 HETATM 会以 altloc 等借口失败；
  - 残留共晶配体会把配体挤错位点（6GSS 的 GSH 残留 → −7.6 错位；去杂后 −8.3 正确位点）。
- PDBFixer 新版 API：`replaceNonstandardResidues()`（旧 removeX 已删）。
- pdbqt 的 AD4 芳香碳类型 "A" 会被 [76:78] 切片当元素读入 → PyMOL 按未知元素配色；解析时 A→C。

## 对接参数

- 种子 42（可复现）。
- 盒子 22 Å 起步；大口袋（NLRP3 类）26 Å 会拖到 378s/次，权衡缩盒。
- 大配体（>600 Da 糖苷）单次 600–1200s，属正常，写好日志耐心轮询。
- vina `write_poses` 拒绝覆盖已存在文件：重跑前 os.remove。
- **WSL 并行度 ≤4 workers**（8 会诱发 VM 崩溃）。
- **阳性对照必做**：已知共晶配体或获批药（DEX×GRα −12.22 / 西乐葆×PTGS2 −8.11 / 依托泊苷×TOP2A −11.81）；体积排斥阴性对照（如示例大分子糖苷×GRα +12.60）验证口袋特异性。

## PyMOL 出图

- 取景顺序必须 orient() 先、zoom() 后。
- byres 口袋选集会吞掉 HEM，上色顺序把 HEM 放最后。

## 完成判断与产物

- ⚠️ VM 崩溃会留**空白填充垃圾文件**（全空格 pdb、0 字节 pdbqt）→ 幂等判断用内容级校验（数 ATOM 记录数），不能只看文件存在/大小。
- 产物规范：`<项目>/docking/{summary.csv, contacts.json, centers.json, poses/}`；summary 含 kcal/mol 矩阵 + 关键残基接触。
- 报告写法（防过度解读）：强结合列"待验证假设"而非结论（绿原酸×GRα 与 DEX 接触残基重合案例）；NLRP3 类无区分力靶点写进局限。
