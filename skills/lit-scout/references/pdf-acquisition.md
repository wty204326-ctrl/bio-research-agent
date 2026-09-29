# 文献 PDF 获取实战路径（2026-09 验证有效）

按顺序尝试，仅走合法渠道（OA 副本、订阅权限内的出版社站点）。

## 路径 1：OA 副本三连查（先做，最快）

- Unpaywall：`https://api.unpaywall.org/v2/{DOI}?email=任意邮箱` → `best_oa_location.url_for_pdf`
- OpenAlex：openalex_search 返回的 `oa_url` 字段
- Semantic Scholar：`https://api.semanticscholar.org/graph/v1/paper/DOI:{DOI}?fields=openAccessPdf`

任一命中直接下载（Node fetch / curl 均可，见下方网络注意）。

## 路径 2：PMC PoW 挑战（pmc.ncbi.nlm.nih.gov）

PMC 的 PDF 直链会返回 "Preparing to download..." 页，内嵌工作量证明挑战：

1. 从返回 HTML 提取 `POW_CHALLENGE` 与 `POW_DIFFICULTY`；
2. 本地暴力找 nonce：sha256(challenge + str(nonce)) 的十六进制前缀 == "0"×难度；
3. 带 `Cookie: cloudpmc-viewer-pow=challenge,nonce` 重新请求，即得真 PDF。

文章页 HTML 里 `pdf/xxx.pdf` 相对链接是主文 PDF 的线索。

## 路径 3：Cloudflare 拦截的出版社站（jbc.org、rupress.org 等对脚本 403）

用 browser-use 内置浏览器（真内核可过验证）导航到文章页 → 页面上下文 `fetch('/action/showPdf?pii=...')` → arrayBuffer → 分块 base64 → Node 侧 `Buffer.from(b64,'base64')` 写文件。

JCB（Rockefeller）新文章有 6 个月 embargo，期内无任何免费副本，如实告知。

## 网络注意（本机）

- Windows Python urllib 会走注册表系统代理（<proxy-port>）导致长响应挂死：必须 `ProxyHandler({})` 强制直连 + `socket.setdefaulttimeout(90)`；Node fetch 默认直连，无此坑。
- Windows curl 访问 NCBI（eutils）会因证书吊销检查失败（CRYPT_E_REVOCATION_OFFLINE）静默返回空——文献抓取一律用 Node fetch 或 Python 直连，别用 curl 测 NCBI。
- git 走代理需 `-c http.sslBackend=openssl`；gh 需要 HTTPS_PROXY 环境变量。
