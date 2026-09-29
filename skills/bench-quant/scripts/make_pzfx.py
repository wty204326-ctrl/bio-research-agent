#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 GraphPad Prism 原生 .pzfx 文件（Grouped 数据表，重复值子列）。
用法: python make_pzfx.py --data values.csv --title "WB fold change" --out wb.pzfx
输入 values.csv（CSV/XLSX 自动识别）：
  长表: category,group,value   → 行=category，列=group，子列=重复值
  宽表: 首列=类别，其余列=组名（同组重复列自动合并为一组）
生成后双击即在 Prism 中打开为原生数据表（可一键 Insert new graph 出图）。
"""
import argparse, datetime, xml.etree.ElementTree as ET
import pandas as pd

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def fmt(v):
    try:
        f = float(v)
        return "" if pd.isna(f) else f"{f:.6g}"
    except Exception:
        return ""

def build(data, title, transpose):
    if transpose:
        data = data.T.reset_index().rename(columns={"index": "category"})
        cols = list(data.columns)
        data = data.rename(columns={cols[1]: "group", cols[2]: "value"})[["category", "group", "value"]]
        data["value"] = pd.to_numeric(data["value"], errors="coerce")
    # 长表/宽表识别
    cl = [str(c).strip().lower() for c in data.columns]
    if set(["category", "group", "value"]).issubset(cl):
        data = data.rename(columns={c: k for c, k in zip(data.columns, cl)})
        cats = list(dict.fromkeys(data["category"].astype(str)))
        grps = list(dict.fromkeys(data["group"].astype(str)))
        cells = {(c, g): [fmt(v) for v in data[(data.category.astype(str) == c) &
                                               (data.group.astype(str) == g)]["value"]] for c in cats for g in grps}
    else:  # 宽表
        cols = list(data.columns)
        cat_c = cols[0]
        cats = [str(x) for x in data[cat_c]]
        grps_raw = cols[1:]
        grps = list(dict.fromkeys(grps_raw))
        cells = {}
        for i, c in enumerate(cats):
            for g in grps:
                vals = []
                for gc in [x for x in grps_raw if x == g]:
                    vals.append(fmt(data.iloc[i][gc]))
                cells[(c, g)] = vals
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    x = [f'<?xml version="1.0" encoding="UTF-8"?>',
         f'<GraphPadPrismFile PrismVersion="10.3.0.0" Version="10.30.0000" LastUsage="{now}">',
         f'<Created By="bio-research-agent" DateTime="{now}"/>',
         '<RefNumbers>0</RefNumbers>', '<ErrorMessages/>',
         '<Sequence DataYFormat="replicates" DataXFormat="none">',
         '<SequenceItem RefNumber="0" ObjectType="Table"/>',
         '<SequenceItem RefNumber="0" ObjectType="Info"/>',
         '</Sequence>',
         '<Info ID="info0"><Title>Info</Title><Constants>'
         f'<Constant Name="Experiment Date" Value="{datetime.date.today().isoformat()}" Type="DateTime"/>'
         '</Constants></Info>',
         f'<Table ID="table0" XFormat="none" YFormat="replicates" TableType="TwoWay" EVMapping="A">',
         f'<Title>{esc(title)}</Title>',
         '<RowTitlesColumn Width="160"><Subcolumn Width="160"><Title> </Title></Subcolumn></RowTitlesColumn>']
    nsub = max((len(v) for v in cells.values()), default=1)
    for g in grps:
        x.append(f'<YColumn Width="110" Decimals="4" Subcolumns="{nsub}"><Title>{esc(g)}</Title>')
        # 每个重复一个 Subcolumn；Subcolumn 内每个类别一行 <d>
        for j in range(nsub):
            x.append("<Subcolumn>")
            for i in range(len(cats)):
                vals = cells.get((cats[i], g), [])
                v = vals[j] if j < len(vals) else ""
                x.append(f"<d>{v}</d>" if v != "" else "<d/>")
            x.append("</Subcolumn>")
        x.append("</YColumn>")
    x += ["</Table>", "<Graphs/>", "<Layouts/>", "<MasterLinks/>", "<Analyses/>",
          "<ManualTransforms/>", "</GraphPadPrismFile>"]
    return "\n".join(x), len(cats), grps, nsub

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", required=True)
    ap.add_argument("--title", default="Data")
    ap.add_argument("--out", required=True)
    ap.add_argument("--transpose", action="store_true", help="对宽表转置后再组表")
    a = ap.parse_args()
    data = pd.read_excel(a.data) if a.data.lower().endswith((".xlsx", ".xls")) else pd.read_csv(a.data)
    xml, nrow, grps, nsub = build(data, a.title, a.transpose)
    ET.fromstring(xml)  # well-formed 自检
    open(a.out, "w", encoding="utf-8", newline="\n").write(xml)
    print(f"[ok] {a.out}: {nrow} 行 × {len(grps)} 组 × {nsub} 重复子列（XML 校验通过）")
    print(f"     组: {', '.join(str(g) for g in grps)}")
