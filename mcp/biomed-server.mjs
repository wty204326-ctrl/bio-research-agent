#!/usr/bin/env node
// biomed MCP server —— 零依赖生物医药数据库工具集（stdio, newline-delimited JSON-RPC）
// 数据源（全部免费、无需 API key）：
//   PubChem / ChEMBL / STRING / UniProt / OpenAlex / EuropePMC / OpenTargets
// 运行要求：Node >= 18（用全局 fetch）。日志走 stderr，stdout 只输出协议消息。
import readline from "node:readline";

const SERVER_NAME = "biomed";
const VERSION = "1.0.0";
const TIMEOUT_MS = 45000;

const log = (...a) => process.stderr.write(a.join(" ") + "\n");

async function fetchWithRetry(url, opts = {}) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), opts.timeout || TIMEOUT_MS);
  try {
    let lastErr;
    for (let attempt = 0; attempt < 2; attempt++) {
      try {
        const res = await fetch(url, {
          signal: ctrl.signal,
          method: opts.method || "GET",
          headers: {
            "User-Agent": "biomed-mcp/1.0 (personal research assistant)",
            Accept: "application/json",
            ...(opts.headers || {}),
          },
          body: opts.body,
        });
        if (!res.ok) {
          const detail = await res.text().catch(() => "");
          throw new Error(
            `HTTP ${res.status} ${res.statusText} <- ${url.slice(0, 200)} ${detail.slice(0, 200)}`
          );
        }
        return opts.raw ? await res.text() : await res.json();
      } catch (e) {
        lastErr = e;
        if (attempt === 0) await new Promise((r) => setTimeout(r, 2000));
      }
    }
    throw lastErr;
  } finally {
    clearTimeout(timer);
  }
}

function parseTSV(tsv) {
  const lines = tsv.trim().split("\n");
  if (lines.length < 2) return [];
  const head = lines[0].split("\t");
  return lines.slice(1).map((l) => {
    const c = l.split("\t");
    const o = {};
    head.forEach((h, i) => (o[h] = c[i]));
    return o;
  });
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// efetch(rettype=abstract, retmode=text) 记录顺序 == 传入 id 顺序
// 格式：块0=期刊行 块1=标题 块2=作者 [Author information:+单位块...] 摘要块... 尾部元数据块(DOI:/PMID:等)
function parseEfetchAbstracts(text) {
  if (!text) return [];
  const chunks = text.split(/(?=^\d+\.\s)/m).filter((c) => c.trim());
  return chunks.map((c) => {
    const blocks = c
      .split(/\n\s*\n/)
      .map((b) => b.replace(/\s+/g, " ").trim())
      .filter(Boolean);
    let i = 3; // 跳过 期刊/标题/作者
    if (blocks[i] && /^Author information:/i.test(blocks[i])) {
      i++;
      while (blocks[i] && /^\(\d+\)/.test(blocks[i])) i++;
    }
    const stopRe =
      /^(DOI:|PMCID:|PMID:|Conflict of interest|Publisher|Comment in|Related|Review|Erratum|Note:|Data|Free article|Update)/i;
    const abs = [];
    while (i < blocks.length && !stopRe.test(blocks[i])) {
      abs.push(blocks[i]);
      i++;
    }
    const s = abs.join(" ");
    return s ? s.slice(0, 1500) : null;
  });
}

function abstractFromInverted(ix) {
  if (!ix) return null;
  const pos = [];
  for (const [word, idxs] of Object.entries(ix)) for (const i of idxs) pos[i] = word;
  const s = pos.join(" ");
  return s ? s.slice(0, 1500) : null;
}

async function otGraphQL(query, variables) {
  return fetchWithRetry("https://api.platform.opentargets.org/api/v4/graphql", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, variables }),
  });
}

function pickChEMBLMol(m) {
  return {
    molecule_chembl_id: m.molecule_chembl_id,
    pref_name: m.pref_name || null,
    max_phase: m.max_phase ?? null,
    molecule_type: m.molecule_type || null,
    first_approval: m.first_approval || null,
    smiles: m.molecule_structures?.canonical_smiles || null,
    inchikey: m.molecule_structures?.standard_inchi_key || null,
  };
}

// ---------------------------------------------------------------- tools ----

const TOOLS = [
  {
    name: "pubchem_compound",
    description:
      "PubChem 化合物查询：返回 CID、分子式、分子量、XLogP、TPSA、HBD/HBA、旋转键、canonical SMILES、InChIKey、同义词。输入名称/SMILES/CID。注意：部分天然产物俗名名称检索会 404（常见于糖苷类），改用 SMILES 或 CID。",
    schema: {
      type: "object",
      properties: {
        query: { type: "string", description: "化合物名称、SMILES 或 CID" },
        query_type: {
          type: "string",
          enum: ["auto", "name", "smiles", "cid"],
          description: "默认 auto：纯数字按 CID，其余先按名称、再按 SMILES 兜底",
        },
      },
      required: ["query"],
    },
    run: async ({ query, query_type = "auto" }) => {
      const PUG = "https://pubchem.ncbi.nlm.nih.gov/rest/pug";
      const tryCids = async (kind, q) => {
        const j = await fetchWithRetry(
          `${PUG}/compound/${kind}/${encodeURIComponent(q)}/cids/JSON`
        );
        const list = j?.IdentifierList?.CID || [];
        return Array.isArray(list) ? list[0] : null;
      };
      let qt = query_type;
      if (qt === "auto") qt = /^\d{2,}$/.test(query) ? "cid" : "name";
      let cid = null;
      if (qt === "cid") cid = parseInt(query, 10);
      if (!cid && qt === "name") cid = await tryCids("name", query).catch(() => null);
      if (!cid) cid = await tryCids("smiles", query).catch(() => null);
      if (!cid)
        throw new Error(
          `PubChem 未找到: ${query}（已尝试 ${qt} 与 SMILES 兜底）。天然产物俗名常 404，请提供 SMILES 或 CID`
        );
      const props = await fetchWithRetry(
        `${PUG}/compound/cid/${cid}/property/MolecularFormula,MolecularWeight,CanonicalSMILES,InChIKey,XLogP,TPSA,HBondDonorCount,HBondAcceptorCount,RotatableBondCount,ExactMass,Charge/JSON`
      );
      let synonyms = [];
      try {
        const syn = await fetchWithRetry(`${PUG}/compound/cid/${cid}/synonyms/JSON`);
        synonyms = (syn?.InformationList?.Information?.[0]?.Synonym || []).slice(0, 20);
      } catch {}
      const p = props?.PropertyTable?.Properties?.[0] || {};
      return { cid, ...p, synonyms };
    },
  },

  {
    name: "chembl_molecule",
    description:
      "ChEMBL 分子查询：名称或 CHEMBL ID → CHEMBL ID、首选名、最高临床阶段、类型、首次批准年份、canonical SMILES、标准 InChIKey。糖苷类立体异构体用 TCMSP 版 InChIKey 查（PubChem 键可能查不到）。",
    schema: {
      type: "object",
      properties: {
        query: { type: "string", description: "化合物名称或 CHEMBL ID（如 CHEMBL284616）" },
      },
      required: ["query"],
    },
    run: async ({ query }) => {
      const BASE = "https://www.ebi.ac.uk/chembl/api/data";
      if (/^CHEMBL\d+$/i.test(query)) {
        const m = await fetchWithRetry(`${BASE}/molecule/${query.toUpperCase()}.json`);
        return pickChEMBLMol(m);
      }
      // 首选精确名（ChEMBL pref_name 全大写习惯）；失败再全文模糊
      let j = await fetchWithRetry(
        `${BASE}/molecule.json?pref_name__iexact=${encodeURIComponent(query.toUpperCase())}&limit=1`
      ).catch(() => null);
      if (j?.molecules?.length) {
        return { query, match_type: "exact", ...pickChEMBLMol(j.molecules[0]) };
      }
      j = await fetchWithRetry(
        `${BASE}/molecule.json?q=${encodeURIComponent(query)}&limit=5`
      );
      const mols = j?.molecules || [];
      if (!mols.length)
        throw new Error(
          `ChEMBL 无匹配: ${query}（天然产物可能未收录，改用相似性垂钓 chembl_similarity）`
        );
      return {
        query,
        match_type: "fuzzy",
        warning:
          "模糊匹配结果请核对分子量/结构（pref_name 为 null 的命中往往不是目标物）；精确名应为 ChEMBL 大写惯用名，如 CHLOROGENIC ACID",
        matches: mols.map((m) => ({
          ...pickChEMBLMol(m),
          full_mwt: m.molecule_properties?.full_mwt || null,
        })),
      };
    },
  },

  {
    name: "chembl_activities",
    description:
      "ChEMBL 活性数据：给定分子（名称或 CHEMBL ID）返回按靶点汇总的活性记录（双通道：pChEMBL≥5 或 nM 值≤10000，自动按靶点去重汇总，默认只留人源靶点）。网络药理学成分靶点挖掘第一步。",
    schema: {
      type: "object",
      properties: {
        query: { type: "string", description: "化合物名称或 CHEMBL ID" },
        human_only: { type: "boolean", description: "默认 true：只保留 Homo sapiens 靶点" },
      },
      required: ["query"],
    },
    run: async ({ query, human_only = true }) => {
      const BASE = "https://www.ebi.ac.uk/chembl/api/data";
      let id = query;
      if (!/^CHEMBL\d+$/i.test(query)) {
        const mol = await fetchWithRetry(
          `${BASE}/molecule.json?q=${encodeURIComponent(query)}&limit=1`
        );
        const m = mol?.molecules?.[0];
        if (!m) throw new Error(`ChEMBL 无该分子: ${query}`);
        id = m.molecule_chembl_id;
      }
      const fetchActs = (extra) =>
        fetchWithRetry(
          `${BASE}/activity.json?molecule_chembl_id=${id}&${extra}&limit=300`
        ).then((j) => j.activities || []);
      const [a1, a2] = await Promise.all([
        fetchActs("pchembl_value__gte=5"),
        fetchActs("standard_units=nM&standard_value__lte=10000"),
      ]);
      const map = new Map();
      for (const a of [...a1, ...a2]) map.set(a.activity_id, a);
      let acts = [...map.values()];
      // target_organism 字段常为空：批量解析靶点元数据（逗号批量优于 & 拼接）
      const tids = [...new Set(acts.map((a) => a.target_chembl_id).filter(Boolean))];
      const targetInfo = {};
      for (let i = 0; i < tids.length; i += 50) {
        const batch = tids.slice(i, i + 50).join(",");
        const tj = await fetchWithRetry(
          `${BASE}/target.json?target_chembl_id__in=${batch}&limit=200`
        ).catch(() => null);
        for (const t of tj?.targets || []) {
          const geneSyn =
            t.target_components?.[0]?.target_component_synonyms?.find(
              (s) => s.syn_type === "GENE_SYMBOL"
            )?.component_synonym || null;
          targetInfo[t.target_chembl_id] = {
            organism: t.organism,
            gene: geneSyn,
            pref_name: t.pref_name,
          };
        }
      }
      if (human_only)
        acts = acts.filter((a) => (targetInfo[a.target_chembl_id]?.organism || "").includes("Homo"));
      const byTarget = {};
      for (const a of acts) {
        const k = a.target_chembl_id;
        byTarget[k] ??= {
          target_chembl_id: k,
          target_pref_name: a.target_pref_name || targetInfo[k]?.pref_name || null,
          gene: targetInfo[k]?.gene || null,
          organism: targetInfo[k]?.organism || null,
          n_activities: 0,
          best_pchembl: 0,
          best_activity: null,
          examples: [],
        };
        const t = byTarget[k];
        t.n_activities++;
        const pv = a.pchembl_value || 0;
        if (pv > t.best_pchembl) {
          t.best_pchembl = pv;
          t.best_activity = `${a.standard_type || "?"} ${a.standard_value ?? "?"} ${a.standard_units || ""}`;
        }
        if (t.examples.length < 3)
          t.examples.push(
            `${a.standard_type || "?"} ${a.standard_value ?? "?"} ${a.standard_units || ""} pChEMBL=${a.pchembl_value ?? "-"} (${a.doc_type || ""} ${a.document_year || ""})`
          );
      }
      const targets = Object.values(byTarget).sort((x, y) => y.best_pchembl - x.best_pchembl);
      return {
        molecule: id,
        total_activities: acts.length,
        human_only,
        n_targets: targets.length,
        targets: targets.slice(0, 60),
      };
    },
  },

  {
    name: "chembl_similarity",
    description:
      "ChEMBL 结构相似性垂钓：SMILES + 相似度阈值 → 最相似的 ChEMBL 分子列表（含 Tanimoto 相似度、首选名、临床阶段）。网络药理学用它替代已失效的 SwissTargetPrediction（取相似分子的活性靶点做靶点转移）。慢（约 1-4 分钟/分子），结果建议缓存。",
    schema: {
      type: "object",
      properties: {
        smiles: { type: "string", description: "查询分子的 SMILES（URL 编码由服务端处理）" },
        threshold: { type: "integer", description: "Tanimoto 相似度阈值百分比，默认 80；网药垂钓建议 50" },
      },
      required: ["smiles"],
    },
    run: async ({ smiles, threshold = 80 }) => {
      const BASE = "https://www.ebi.ac.uk/chembl/api/data";
      const j = await fetchWithRetry(
        `${BASE}/similarity/${encodeURIComponent(smiles)}/${threshold}.json?limit=40`
      );
      const mols = j?.molecules || [];
      return {
        threshold,
        n: mols.length,
        note: "对下一步：逐个分子调 chembl_activities 取其活性靶点，合并即'相似性垂钓'靶点集",
        molecules: mols.map((m) => ({
          molecule_chembl_id: m.molecule_chembl_id,
          pref_name: m.pref_name || null,
          similarity: m.similarity ?? null,
          max_phase: m.max_phase ?? null,
        })),
      };
    },
  },

  {
    name: "string_interactions",
    description:
      "STRING 蛋白互作（PPI）：蛋白名/基因名 → 互作伙伴列表（组合得分 0-1）。默认人 9606。网络药理学 PPI 网络/degree 枢纽分析用。",
    schema: {
      type: "object",
      properties: {
        protein: { type: "string", description: "蛋白符号，如 IL6、TP53" },
        species: { type: "string", description: "NCBI 分类 ID，默认 9606（人）；小鼠 10090" },
        limit: { type: "integer", description: "返回伙伴数上限，默认 50" },
      },
      required: ["protein"],
    },
    run: async ({ protein, species = "9606", limit = 50 }) => {
      const tsv = await fetchWithRetry(
        `https://string-db.org/api/tsv/interaction_partners?identifiers=${encodeURIComponent(
          protein
        )}&species=${species}&limit=${Math.min(limit, 200)}&caller_identity=biomed_mcp`,
        { raw: true }
      );
      const rows = parseTSV(tsv);
      if (!rows.length) throw new Error(`STRING 无互作记录: ${protein}（检查物种/符号）`);
      return {
        query: protein,
        species,
        n: rows.length,
        partners: rows.map((r) => ({
          partner: r.preferredName_B,
          score: Number(r.score),
          stringId: r.stringId_B,
        })),
      };
    },
  },

  {
    name: "string_network",
    description:
      "STRING 多蛋白互作网络：输入基因/蛋白列表（≥2 个），返回它们之间的全部互作边（含 0-1 得分）与各节点度；可选 add_nodes 让 STRING 自动补充高置信互作伙伴（扩展网络/找模块）。PPI 网络构建与枢纽分析第一步。",
    schema: {
      type: "object",
      properties: {
        proteins: {
          type: "array",
          items: { type: "string" },
          description: "基因符号列表，如 [\"IL6\",\"TNF\",\"IL1B\"]",
        },
        species: { type: "string", description: "NCBI 分类 ID，默认 9606（人）；小鼠 10090" },
        add_nodes: { type: "integer", description: "自动补充的互作伙伴数，默认 0（只在输入节点间连边）" },
        min_score: { type: "number", description: "边得分下限（返回后过滤），默认 0.15；严格分析用 0.4（STRING 中等置信）" },
      },
      required: ["proteins"],
    },
    run: async ({ proteins, species = "9606", add_nodes = 0, min_score = 0.15 }) => {
      if (!Array.isArray(proteins) || proteins.length < 2)
        throw new Error("proteins 需为 ≥2 个基因符号的数组");
      const params = new URLSearchParams({
        identifiers: proteins.join("\r"),
        species,
        caller_identity: "biomed_mcp",
      });
      if (add_nodes > 0) params.set("add_nodes", String(add_nodes));
      // >40 个蛋白时 URL 过长，改 POST（STRING API 支持）
      const usePost = proteins.length > 40 || add_nodes > 50;
      let tsv;
      if (usePost) {
        const res = await fetch("https://string-db.org/api/tsv/network", {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: params.toString(),
        });
        if (!res.ok) throw new Error(`STRING HTTP ${res.status}`);
        tsv = await res.text();
      } else {
        tsv = await fetchWithRetry(
          `https://string-db.org/api/tsv/network?${params.toString()}`,
          { raw: true, timeout: 90000 }
        );
      }
      const rows = parseTSV(tsv);
      const edges = rows
        .filter((r) => Number(r.score) >= min_score)
        .map((r) => ({
          a: r.preferredName_A,
          b: r.preferredName_B,
          score: Number(r.score),
        }))
        .sort((x, y) => y.score - x.score);
      const degree = {};
      const nodes = new Set();
      for (const e of edges) {
        nodes.add(e.a);
        nodes.add(e.b);
        degree[e.a] = (degree[e.a] || 0) + 1;
        degree[e.b] = (degree[e.b] || 0) + 1;
      }
      for (const p of proteins) if (!nodes.has(p)) nodes.add(p);
      return {
        query: proteins,
        species,
        add_nodes,
        min_score,
        n_nodes: nodes.size,
        n_edges: edges.length,
        degrees: Object.entries(degree)
          .sort((x, y) => y[1] - x[1])
          .map(([gene, deg]) => ({ gene, degree: deg })),
        edges: edges.slice(0, 1000),
      };
    },
  },

  {
    name: "geo_search",
    description:
      "GEO 数据集检索（NCBI db=gds）：检索式 → GSE 编号、标题、摘要、样本数、平台、研究类型、发表日期、补充文件 FTP 链接。找表达谱/单细胞数据集用。示例：\"acute lung injury\"[All Fields] AND \"Mus musculus\"[orgn] AND gse[ETYP]",
    schema: {
      type: "object",
      properties: {
        query: { type: "string", description: "GEO 检索式（英文）；物种用 [orgn]，限 Series 加 AND gse[ETYP]" },
        limit: { type: "integer", description: "返回条数，默认 10，最大 30" },
      },
      required: ["query"],
    },
    run: async ({ query, limit = 10 }) => {
      const EU = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils";
      const sj = await fetchWithRetry(
        `${EU}/esearch.fcgi?db=gds&term=${encodeURIComponent(query)}&retmax=${Math.min(limit, 30)}&retmode=json`
      );
      const ids = sj?.esearchresult?.idlist || [];
      const count = Number(sj?.esearchresult?.count) || 0;
      if (!ids.length) return { query, total_hits: count, n: 0, results: [] };
      await sleep(400);
      const sumJ = await fetchWithRetry(`${EU}/esummary.fcgi?db=gds&id=${ids.join(",")}&retmode=json`);
      const results = ids
        .map((id) => sumJ?.result?.[id])
        .filter(Boolean)
        .map((s) => ({
          accession: s.accession,
          type: s.entrytype,
          title: s.title,
          n_samples: s.n_samples,
          platform: s.gpl,
          platform_title: s.gplname || null,
          design: s.gdstype || null,
          taxon: s.taxon,
          pubdate: s.pdat,
          summary: (s.summary || "").slice(0, 400),
          supplementary_ftp: s.FTPLink || null,
        }));
      return { query, total_hits: count, n: results.length, results };
    },
  },

  {
    name: "admet_predict",
    description:
      "ADMET 成药性预测（调本机 CPU ADMET 控制台 v3.2，端口 8100）：SMILES → 24 端点（Caco2/LogD/HIA/Pgp/CYP×5/hERG/LogS/BBB/PAMPA/AMES/F/DILI/VDss/LD50/PPB/t1/2/致癌/皮肤/清除率×2）。⚠️ 需先启动桌面「ADMET控制台_实验室部署包」的 启动.bat；未启动时本工具会报连接失败并提示。",
    schema: {
      type: "object",
      properties: {
        smiles_list: {
          type: "array",
          items: { type: "string" },
          description: "SMILES 列表（一次最多按控制台批量上限）",
        },
      },
      required: ["smiles_list"],
    },
    run: async ({ smiles_list }) => {
      const list = (Array.isArray(smiles_list) ? smiles_list : [smiles_list]).filter(Boolean);
      if (!list.length) throw new Error("smiles_list 为空");
      let resp;
      try {
        resp = await fetch("http://127.0.0.1:8100/api/predict", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ smiles: list.join("\n") }),
          signal: AbortSignal.timeout(120000),
        });
      } catch (e) {
        throw new Error(
          `无法连接本机 ADMET 控制台(127.0.0.1:8100)：${e?.message || e}。请先双击桌面「ADMET控制台_实验室部署包\\ADMET预测模型\\启动.bat」启动服务（首次加载模型需数十秒），再重试本工具。`
        );
      }
      const text = await resp.text();
      if (!resp.ok) throw new Error(`ADMET 控制台 HTTP ${resp.status}: ${text.slice(0, 300)}`);
      const j = JSON.parse(text);
      return { model: j.model, n: j.n, results: j.results, note: j.note };
    },
  },

  {
    name: "uniprot_lookup",
    description: "UniProt 蛋白信息：基因名/蛋白名/ accession → 功能描述、基因符号、物种。优先 reviewed（Swiss-Prot）条目。",
    schema: {
      type: "object",
      properties: {
        query: { type: "string", description: "基因符号或蛋白名，如 TP53" },
        size: { type: "integer", description: "返回条目数，默认 3" },
      },
      required: ["query"],
    },
    run: async ({ query, size = 3 }) => {
      const tryQ = async (q) =>
        fetchWithRetry(
          `https://rest.uniprot.org/uniprotkb/search?query=${encodeURIComponent(
            q
          )}&fields=accession,id,protein_name,gene_names,organism_name,cc_function&format=json&size=${Math.min(size, 10)}`
        );
      let j;
      try {
        j = await tryQ(`${query} AND reviewed:true`);
        if (!j?.results?.length) j = await tryQ(query);
      } catch {
        j = await tryQ(query);
      }
      const results = (j?.results || []).map((r) => ({
        accession: r.primaryAccession,
        entry: r.uniProtkbId,
        protein_name:
          r.proteinDescription?.recommendedName?.fullName?.value ||
          r.proteinDescription?.submissionNames?.[0]?.fullName?.value ||
          null,
        genes: (r.genes || [])
          .flatMap((g) => [g.geneName?.value, ...(g.synonyms || []).map((s) => s.value)])
          .filter(Boolean),
        organism: r.organism?.scientificName,
        function: (
          r.comments?.find((c) => c.commentType === "FUNCTION")?.texts?.map((t) => t.value).join(" ") || ""
        ).slice(0, 800),
      }));
      if (!results.length) throw new Error(`UniProt 无匹配: ${query}`);
      return { query, results };
    },
  },

  {
    name: "openalex_search",
    description:
      "OpenAlex 文献检索：跨库学术搜索，返回标题/年份/期刊/DOI/被引数/OA链接/作者/摘要（由倒排索引重建）。适合广撒网式主题检索与被引排序。与 europepmc_search 互补。",
    schema: {
      type: "object",
      properties: {
        query: { type: "string", description: "英文检索式（自然语言或关键词）" },
        from_year: { type: "integer", description: "起始年份（含）" },
        to_year: { type: "integer", description: "截止年份（含）" },
        limit: { type: "integer", description: "返回条数，默认 15，最大 50" },
      },
      required: ["query"],
    },
    run: async ({ query, from_year, to_year, limit = 15 }) => {
      const filters = [];
      if (from_year) filters.push(`from_publication_date:${from_year}-01-01`);
      if (to_year) filters.push(`to_publication_date:${to_year}-12-31`);
      let url = `https://api.openalex.org/works?search=${encodeURIComponent(
        query
      )}&per-page=${Math.min(limit, 50)}&sort=relevance_score:desc`;
      if (filters.length) url += `&filter=${filters.join(",")}`;
      const j = await fetchWithRetry(url);
      const works = (j?.results || []).map((w) => ({
        title: w.title,
        year: w.publication_year,
        journal: w.primary_location?.source?.display_name || null,
        doi: w.doi,
        cited_by_count: w.cited_by_count,
        type: w.type,
        is_oa: w.open_access?.is_oa,
        oa_url: w.open_access?.oa_url || null,
        authors: (w.authorships || []).slice(0, 5).map((a) => a.author?.display_name).join(", "),
        abstract: abstractFromInverted(w.abstract_inverted_index),
      }));
      return { query, n: works.length, works };
    },
  },

  {
    name: "pubmed_search",
    description:
      "PubMed 官方检索（NCBI E-utilities）：esearch 检索 + esummary 元数据 + efetch 摘要，返回结构化结果（标题/期刊/年份/DOI/PMID/PMCID/摘要）。支持 PubMed 检索语法，如 quercetin AND \"acute lung injury\"[Title/Abstract]。生物医药文献检索首选。",
    schema: {
      type: "object",
      properties: {
        query: { type: "string", description: "PubMed 检索式（英文）" },
        limit: { type: "integer", description: "返回条数，默认 15，最大 50" },
        from_year: { type: "integer", description: "起始年份（含）" },
        to_year: { type: "integer", description: "截止年份（含）" },
        sort: {
          type: "string",
          enum: ["relevance", "pub_date", "most_recent", "author"],
          description: "排序方式，默认 relevance",
        },
      },
      required: ["query"],
    },
    run: async ({ query, limit = 15, from_year, to_year, sort = "relevance" }) => {
      const EU = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils";
      let term = query;
      if (from_year || to_year)
        term += ` AND ${from_year || 1900}:${to_year || new Date().getFullYear()}[dp]`;
      const sj = await fetchWithRetry(
        `${EU}/esearch.fcgi?db=pubmed&term=${encodeURIComponent(
          term
        )}&retmax=${Math.min(limit, 50)}&sort=${sort}&retmode=json`
      );
      const ids = sj?.esearchresult?.idlist || [];
      const count = Number(sj?.esearchresult?.count) || 0;
      if (!ids.length) return { query, total_hits: count, n: 0, results: [] };
      await sleep(400); // E-utilities 免 key 限 3 次/秒
      const sumJ = await fetchWithRetry(
        `${EU}/esummary.fcgi?db=pubmed&id=${ids.join(",")}&retmode=json`
      ).catch(() => null);
      await sleep(400);
      const text = await fetchWithRetry(
        `${EU}/efetch.fcgi?db=pubmed&id=${ids.join(",")}&rettype=abstract&retmode=text`,
        { raw: true }
      ).catch(() => "");
      const abstracts = parseEfetchAbstracts(text);
      const results = ids.map((id, i) => {
        const s = sumJ?.result?.[id] || {};
        const doi = s.articleids?.find((a) => a.idtype === "doi")?.value || null;
        const pmcid = s.articleids?.find((a) => a.idtype === "pmc")?.value || null;
        return {
          pmid: id,
          title: s.title || null,
          journal: s.fulljournalname || s.source || null,
          pubdate: s.pubdate || null,
          first_author: s.sortfirstauthor || null,
          doi,
          pmcid,
          abstract: abstracts[i] || null,
        };
      });
      return { query, total_hits: count, n: results.length, results };
    },
  },

  {
    name: "europepmc_search",
    description:
      "EuropePMC 检索（备用，服务近期常 503，首选 pubmed_search / openalex_search）：支持 TITLE_ABS:\"...\" AND PUB_YEAR:2024 等字段语法，覆盖 PMC 全文库。返回标题/摘要/PMID/PMCID/DOI/被引。",
    schema: {
      type: "object",
      properties: {
        query: { type: "string", description: "EuropePMC 检索式（英文）" },
        limit: { type: "integer", description: "返回条数，默认 15，最大 50" },
      },
      required: ["query"],
    },
    run: async ({ query, limit = 15 }) => {
      const j = await fetchWithRetry(
        `https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=${encodeURIComponent(
          query
        )}&format=json&pageSize=${Math.min(limit, 50)}`
      );
      const hits = (j?.resultList?.result || []).map((r) => ({
        title: (r.title || "").replace(/\.$/, ""),
        authors: r.authorString,
        journal: r.journalTitle || null,
        year: r.pubYear,
        doi: r.doi,
        pmid: r.pmid,
        pmcid: r.pmcid,
        cited_by: r.citedByCount,
        is_oa: r.isOpenAccess === "Y",
        abstract: r.abstractText ? r.abstractText.replace(/<[^>]+>/g, "").slice(0, 1500) : null,
      }));
      return { query, total_hits: j?.hitCount, n: hits.length, results: hits };
    },
  },

  {
    name: "opentargets_search",
    description:
      "OpenTargets 搜索：术语 → 疾病（含 MONDO/EFO ID，供 opentargets_disease_targets 用）与靶点。疾病靶点挖掘第一步。免认证。",
    schema: {
      type: "object",
      properties: {
        term: { type: "string", description: "疾病或靶点名称（英文），如 acute lung injury" },
      },
      required: ["term"],
    },
    run: async ({ term }) => {
      const q =
        "query Search($q: String!) { search(queryString: $q) { hits { id name entity description score } } }";
      const j = await otGraphQL(q, { q: term });
      const hits = j?.data?.search?.hits || [];
      const diseases = hits
        .filter((h) => h.entity === "disease")
        .map((h) => ({ id: h.id, name: h.name, description: (h.description || "").slice(0, 200), score: h.score }))
        .slice(0, 8);
      const targets = hits
        .filter((h) => h.entity === "target")
        .map((h) => ({ id: h.id, name: h.name, description: (h.description || "").slice(0, 200), score: h.score }))
        .slice(0, 8);
      if (!diseases.length && !targets.length) throw new Error(`OpenTargets 无匹配: ${term}`);
      return { term, diseases, targets };
    },
  },

  {
    name: "opentargets_disease_targets",
    description:
      "OpenTargets 疾病关联靶点：MONDO/EFO ID → 全部关联靶点+评分（已分页拉全）。网络药理学疾病靶点的最佳来源。⚠️ 评分阈值 0.05 裁剪极狠（总量骤降一个量级），阈值上下建议各留一版。",
    schema: {
      type: "object",
      properties: {
        disease_id: { type: "string", description: "MONDO/EFO ID，如 MONDO_0015796（急性肺损伤）" },
        min_score: { type: "number", description: "评分下限，默认 0.05；传 0 取全量" },
      },
      required: ["disease_id"],
    },
    run: async ({ disease_id, min_score = 0.05 }) => {
      const all = [];
      let index = 0;
      let count = 0;
      while (index <= 20) {
        const q =
          "query D($d: String!, $i: Int!, $s: Int!) { disease(efoId: $d) { associatedTargets(page: {index: $i, size: $s}) { count rows { score target { approvedSymbol } } } } }";
        const j = await otGraphQL(q, { d: disease_id, i: index, s: 500 });
        const at = j?.data?.disease?.associatedTargets;
        if (!at) throw new Error(`OpenTargets 无该疾病: ${disease_id}（先用 opentargets_search 找 ID）`);
        count = at.count;
        if (!at.rows?.length) break;
        all.push(...at.rows);
        if (all.length >= count) break;
        index++;
      }
      const filtered = all
        .filter((r) => r.score >= min_score)
        .map((r) => ({ target: r.target?.approvedSymbol, score: Number(r.score.toFixed(3)) }));
      return {
        disease_id,
        total_associations: count,
        min_score,
        n_targets: filtered.length,
        targets: filtered,
      };
    },
  },
];

// --------------------------------------------------------------- plumbing ---

function send(obj) {
  process.stdout.write(JSON.stringify(obj) + "\n");
}

async function handleMessage(msg) {
  const { id, method, params } = msg;
  if (method === "initialize") {
    return {
      jsonrpc: "2.0",
      id,
      result: {
        protocolVersion: params?.protocolVersion || "2025-06-18",
        capabilities: { tools: { listChanged: false } },
        serverInfo: { name: SERVER_NAME, version: VERSION },
      },
    };
  }
  if (typeof method === "string" && method.startsWith("notifications/")) return null;
  if (method === "ping") return { jsonrpc: "2.0", id, result: {} };
  if (method === "tools/list") {
    return {
      jsonrpc: "2.0",
      id,
      result: { tools: TOOLS.map((t) => ({ name: t.name, description: t.description, inputSchema: t.schema })) },
    };
  }
  if (method === "tools/call") {
    const name = params?.name;
    const args = params?.arguments || {};
    const tool = TOOLS.find((t) => t.name === name);
    if (!tool) {
      return {
        jsonrpc: "2.0",
        id,
        result: { content: [{ type: "text", text: `未知工具: ${name}` }], isError: true },
      };
    }
    try {
      log(`[call] ${name} ${JSON.stringify(args).slice(0, 300)}`);
      const out = await tool.run(args);
      let text = typeof out === "string" ? out : JSON.stringify(out, null, 1);
      if (text.length > 45000) text = text.slice(0, 45000) + "\n...[已截断]";
      return { jsonrpc: "2.0", id, result: { content: [{ type: "text", text }] } };
    } catch (e) {
      const msg = `ERROR (${name}): ${e?.message || String(e)}`;
      log(msg);
      return { jsonrpc: "2.0", id, result: { content: [{ type: "text", text: msg }], isError: true } };
    }
  }
  if (id !== undefined && id !== null) {
    return { jsonrpc: "2.0", id, error: { code: -32601, message: `Method not found: ${method}` } };
  }
  return null;
}

const rl = readline.createInterface({ input: process.stdin, terminal: false });
rl.on("line", (line) => {
  const s = line.trim();
  if (!s) return;
  let msg;
  try {
    msg = JSON.parse(s);
  } catch {
    log("非 JSON 行，忽略");
    return;
  }
  handleMessage(msg)
    .then((resp) => {
      if (resp) send(resp);
    })
    .catch((e) => {
      log("handler 崩溃:", e?.stack || e);
      if (msg.id !== undefined) {
        send({ jsonrpc: "2.0", id: msg.id, error: { code: -32603, message: String(e?.message || e) } });
      }
    });
});

log(`biomed MCP server v${VERSION} 就绪（${TOOLS.length} 个工具），等待 stdio 消息`);
