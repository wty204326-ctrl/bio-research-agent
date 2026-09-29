# WSL2 运维手册（生信/对接任务执行前必读）

## 环境

- Ubuntu 26.04（WSL2），用户 <user>；`C:\Users\<you>\.wslconfig`：memory=12GB, processors=12（物理 16GB）。
- ⚠️ **双 conda 陷阱**：交互 shell 钩的是 `~/miniconda3` base，但项目环境（rna/seurat/ml）在 **`~/miniforge3`**；`dock` env 在 `~/miniconda3/envs/dock`。
  - 激活：`source ~/miniforge3/bin/activate rna`；装包前先确认目标 env 归属哪个 conda 安装。
- env 清单：
  - `rna`：hisat2/samtools/featureCounts/fastp/multiqc + R 4.5.3（DESeq2/edgeR/limma/clusterProfiler/org.Hs.eg.db/glmnet/randomForest/caret/xgboost/pROC/tidyverse/data.table/pheatmap，13/13 验证）
  - `seurat`：Seurat 5.5.1 + R 4.5.3（专供 scRNA）
  - `dock`：对接全家桶（见 docking-manual.md）
  - `ml`：GPU torch 2.14.0+cu126（RTX 3050 可用）
- conda channels 必须同时列 conda-forge + bioconda（strict），走清华 TUNA。
- 内存红线：禁 STAR（用 HISAT2/Salmon）；scRNA 大数据用两阶段法；Windows R 读 1GB Seurat 对象需 ~5GB 峰值内存（OOM 两种形态："cannot allocate vector" 或 readRDS "error reading from connection"——后者常非文件损坏，gzip 流校验可证清白）。

## 跨界传参规则（最重要，违反必返工）

1. wsl.exe 跨界会吞双引号内的 `$` → **含变量/中文/复杂引号的脚本一律**：Write 写本地文件 → Git Bash `base64 -w0 f` → WSL `base64 -d > dst` 落地 → `wc -c` 回读校验 → 执行。`/mnt/c` 经 9p 读文件**间歇性返回 0 字节**（cp 静默失败），同样走 base64+stdin。
2. Write 工具写 `.sh` 是 CRLF → WSL 内 `sed -i 's/\r$//'` 再执行。
3. 内联命令避免一切 `$`；`Rscript -e '...'` 含 $/引号/转义必损坏 → 写脚本文件。
4. PowerShell 内联会被 Git Bash 吞 `$`；ps1 文件用 Write 写、文件名全 ASCII、注意 PS5.1 无 BOM UTF-8 中文乱码坑。

## 长任务与稳定性

- wsl.exe 附着会话 **~2 分钟被回收**（exit 127/2）→ 长任务 `setsid nohup ... < /dev/null > 日志 2>&1 &` 完全脱离；日志写 `~/xxx/logs/` 持久路径（`/tmp` 是 tmpfs，VM 重启清空；`/var/tmp` 持久）。
- wsl.exe 启动后台任务：**推送与启动分两条命令**（一条命令里 & 会把整链丢后台被杀）。
- **WSL2 VM 会不定时崩溃重启**：任务"静默死亡"先查 `uptime`（up 0 min = 刚崩）+ `dmesg | tail` + `ps -eo etime,cmd`；历史上多次误判为 harness 杀进程。**降并行度（≤4）显著降低崩溃率**。
- VM 崩溃留空白填充垃圾文件 → 幂等判断用内容级校验（数 ATOM 记录），非 os.path.exists/大小。
- pip 输出过管道跨界**静默丢死**（进度条 \r）→ `pip install x > 日志 2>&1; echo $?; tail 日志`。
- pkill -f 会匹配自己命令行（自杀 exit 9）→ `pkill -9 -f "mamb[a] create"` 写法，且杀进程与重启分两条。
- wsl.exe 报 WSL/Service/CreateInstance/0x800705b4 超时 → 重试即可。
- **pypi torch 2.7.x 在本机 WSL import 即 SIGBUS（exit 135）**，别装；要 GPU torch 就 `conda create -n new --clone ml`。

## 网络

- GitHub 直连超时 → 清华 TUNA github-release 镜像；git 走 <proxy-port> 代理必须 `-c http.sslBackend=openssl`，gh 需 HTTPS_PROXY 环境变量。
- conda 单连接僵死 → MAMBA_DOWNLOAD_THREADS/REMOTE_* 参数，或 dry-run --json 导出 url 清单后 curl 断点续传循环。
- Bioconductor 大包（org.Hs.eg.db ~105MB）post-link 从 bioconductor.org 下载必僵死 → **16 段并行 curl -r 范围请求**（直连重定向后的 xsede 最终 URL），`R CMD INSTALL -l` 装进 env。
- GEO 大文件（>2MB）直连续传必坏字节/截断 → 分段并行 curl -r + 逐段**精确字节数 ==** 校验（勿用 >=）+ `gzip -t`/zipfile 终检；⚠️ 验证工具本身可能缺失或内嵌 python 漏 except 造成"文件坏了"假象；⚠️ 同一文件多个后台下载任务互相覆盖，启动前确认旧任务已死。

## 文件系统

- `/mnt/c` 上 1GB `.rds` 读取报 "error reading from connection" → 先 cp 进 WSL 原生 fs（~/）再 readRDS。
- h5ad 经 UNC（//wsl.localhost）读写必报 HDF5 文件锁错误 → cp 到 Windows 本地处理、本地写完再 cp 回（cp 单向 ~55s/6.9GB 可接受）。
- Windows 侧 h5py 读不动全量矩阵时：两遍流式抽取（pass1 算每细胞总量+panel nnz 精确预分配，pass2 只留目标基因）可把内存压到 1GB 内。
- NumPy：重复索引 `arr[idx] += v` **不累加**（只留最后一次）→ 累计必须 `np.add.at`。
