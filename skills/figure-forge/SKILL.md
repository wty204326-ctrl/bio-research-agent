---
name: figure-forge
description: 论文/汇报图像裁切、拼接、标注工具箱。裁图（坐标/自动去白边）、多图网格拼接+面板字母 A/B/C、比例尺、箭头/方框/文字标注、透明铺白。当用户要：裁图/裁切/拼图/组图/拼接/面板字母/比例尺/白底/标注箭头/画框/figure panel/crop/stitch/montage 时使用。
---

# 图像裁拼工具 figure-forge

脚本：本 skill `scripts/figops.py`（Windows Python，PIL）。**输出一律纯白背景**（用户红线）。

## 子命令速查

| 命令 | 作用 | 关键参数 |
|---|---|---|
| `info IMG` | 看尺寸/模式 | — |
| `autocrop IMG OUT` | 自动去白边 | `--pad 20 --thr 245` |
| `crop IMG OUT` | 坐标裁切 | `--box x0,y0,x1,y1` |
| `stitch OUT --imgs ...` | 网格拼接+面板字母 | `--cols 2 --gap 12 --pad 12 --labels A,B,C --label-size 48 --uniform-height` |
| `scalebar IMG OUT` | 加比例尺 | `--px 100 --um 50 --color white --th 6`（右下角） |
| `whitebg IMG OUT` | 透明→纯白铺平 | — |
| `annotate IMG OUT` | 方框/圆圈/箭头/文字 | `--box x,y,w,h --arrow x1,y1,x2,y2 --text x,y,STR --box-color red --box-width 4` |

坐标原点=左上，单位像素。

## 工作方法（重要）

1. **先 `info` 拿尺寸**再定坐标；裁切/标注后**用 Read 工具看结果自查**，不对就迭代坐标——不要一次猜到位。
2. 自动化裁切定位（如"把条带区域裁出来"）：可先用 autocrop 全局去边，再按 info 尺寸估算 box；精确目标（如第 3 泳道）用 crop 分步逼近。
3. 拼接流程惯例：每张先 `autocrop` → `stitch --cols N --labels A,B,C...` → 需要时 `annotate` 标注 → 需要时 `scalebar`。
4. 比例尺换算：px/µm = 图宽px ÷ 视野宽µm（让用户给物镜视野或已有标尺像素长度；显微图常见 40× 一个视野约 250-300µm，勿凭空假设）。
5. 大图拼接注意总尺寸（期刊一般 <3000px 宽可用 `--uniform-height` 统一）。

## 输出规范

- PNG 优先（无损）；JPG 加 `quality=95`。
- 面板字母加粗黑体、左上角；间距 `--gap 12` 起，组图留白要能放下字母。
- 完成后报告：最终尺寸、行列布局、字母对应内容。
- **分工**：本工具管位图裁拼/标注/比例尺；统计图表（柱/箱/火山/热图等）优先 r-plot skill（156 模板+莫兰迪配色），见 `/plot`。
