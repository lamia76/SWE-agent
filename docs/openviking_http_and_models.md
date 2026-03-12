# OpenViking HTTP 调用原理与模型依赖说明

本文说明：**用 HTTP 调用 OpenViking 的原理**、**依赖哪些模型能力**、以及**这些模型是如何被调用的**。适用于 `tools/openviking`（嵌入式）和 `tools/openviking_cli`（CLI 连 Server）两种方式。

---

## 一、HTTP 调用的整体原理

### 1. 两种使用方式

| 方式 | 谁发 HTTP | 谁用模型 | 配置文件 |
|------|-----------|----------|----------|
| **嵌入式**（tools/openviking） | 无：进程内直接调用 | 本进程按 ov.conf 调 embedding/VLM/rerank 的 **API 地址** | ov.conf |
| **CLI 连 Server**（tools/openviking_cli） | CLI 客户端 → OpenViking Server | **Server 进程**按自己的 ov.conf 调 embedding/VLM/rerank | 客户端：ovcli.conf（只写 Server URL）；Server：ov.conf（写模型 API） |

共同点：**真正调用“模型”的永远是读 ov.conf 的那一侧**（嵌入式=本机进程，CLI 方式=Server 进程）。部署的模型地址和接口不变，指的就是 ov.conf 里配置的那套 API（embedding api_base、vlm api_base、rerank host 等）。

### 2. CLI 方式的 HTTP 链路（你当前用的）

```
Agent (SWE) 
  → 执行 ov_index_repo / ov_find / ov_read 等
  → bin 里脚本调 ov/openviking 命令
  → ov 读 ovcli.conf，得到 Server 的 url（与 ov.conf server.port 一致，如 http://141.61.16.3:8090）
  → 发 HTTP 到 OpenViking Server
       POST /api/v1/resources          (添加资源)
       POST /api/v1/system/wait        (等待处理)
       POST /api/v1/search/find        (语义搜索)
       GET  /api/v1/content/read       (读内容)
       GET  /api/v1/content/abstract   (L0 摘要)
       GET  /api/v1/content/overview   (L1 概览)
       ...
  → Server 内部根据 **自己的 ov.conf** 调 embedding / VLM / rerank 等外部 API
  → 返回 JSON，ov 再输出给 Agent
```

也就是说：**HTTP 只存在于「客户端 ↔ OpenViking Server」这一段**；**模型调用**发生在 **Server 内部**，由 Server 的 ov.conf 决定连哪些接口（部署的模型地址和接口没有改变，就是 ov.conf 里那些）。

---

## 二、依赖的模型功能有哪些

OpenViking 依赖三类“模型/服务”，都在 **ov.conf** 里配置（嵌入式用本机 ov.conf，CLI 方式用 **Server 上的 ov.conf**）：

| 能力 | 用途 | ov.conf 典型配置 | 何时被调用 |
|------|------|------------------|------------|
| **Embedding**（向量化） | 把文本变成向量，用于语义检索、索引 | `embedding.dense`：`api_base`、`api_key`、`model` 等 | 索引资源时写入向量；语义搜索时把 query 转成向量 |
| **VLM**（视觉/大模型） | 生成 L0/L1 摘要、理解多模态内容 | `vlm`：`api_base`、`api_key`、`model` 等 | 生成 abstract/overview、处理图片/视频等 |
| **Rerank**（重排序） | 对检索结果做精排，提高相关性 | `rerank`：`host`、`model_name`、鉴权等 | 语义搜索（find）时对候选结果做 rerank |

也就是说：**需要依赖的“模型功能”就是这三类**，且都是通过 **HTTP 调外部服务**（你部署的模型地址和接口没变，就是这些 api_base / host）。

---

## 三、这些模型是怎么被调用的

### 1. 配置从哪里来

- **谁跑 OpenViking 的“服务端逻辑”**（索引、检索、生成摘要），谁就 **读 ov.conf**。
  - 嵌入式：本机进程读 `OPENVIKING_CONFIG_FILE` 指向的 ov.conf（如 tools/openviking 的 ov.conf）。
  - CLI 方式：**OpenViking Server** 启动时用 `--config` 或默认路径读 **Server 上的 ov.conf**。
- 因此：**调用的 API 地址和 tools/openviking 一致** = Server 上的 ov.conf 里 embedding/vlm/rerank 的地址、接口和 tools/openviking 的 ov.conf **保持一致**（同一套部署、同一批模型）。

### 2. Embedding 的调用

- **配置**：ov.conf 里 `embedding.dense`（或其它后端）的 `api_base`、`api_key`、`model`。
- **调用时机**：
  - **索引**：资源解析完后，内容入队，后台任务把文本送给 embedder，embedder 按 `api_base` 发 HTTP 到你的 embedding 服务（如 `http://141.61.16.3:8002/v1`），拿到向量再写入向量库。
  - **搜索**：`find` 时先把 query 文本交给 embedder，同样按 `api_base` 请求一次，得到 query 向量，再做向量检索。
- **代码路径（概念）**：`VikingFS.find` → 用 `embedder.embed(query)` → 底层按 ov.conf 的 embedding 配置发 HTTP。

### 3. VLM 的调用

- **配置**：ov.conf 里 `vlm` 的 `api_base`、`api_key`、`model`、`backend` 等。
- **调用时机**：
  - 生成 **L0 abstract**、**L1 overview**：语义队列消费时，调用 VLM 生成摘要（Summarizer 等用 VLMProcessor）。
  - 解析图片/视频等：媒体处理器把图像/帧送给 VLM 做理解。
- **代码路径（概念）**：`Summarizer`、`UnifiedResourceProcessor` 等使用 `VLMProcessor`，最终通过 ov.conf 的 vlm 配置发 HTTP（如 `http://141.61.16.3:10193/v1`）。

### 4. Rerank 的调用

- **配置**：ov.conf 里 `rerank` 的 `host`、`model_name`、`model_version`、鉴权等。
- **调用时机**：仅在 **语义搜索（find）** 时：先做向量检索得到一批候选，再用 rerank 模型对「query + 候选文档」做精排，按分数截断返回。
- **代码路径（概念）**：`HierarchicalRetriever.retrieve` 里，若有 `rerank_config` 且为 thinking 模式，会调 `rerank_client.rerank_batch(query, docs)`，底层按 ov.conf 的 rerank 配置发 HTTP（如火山方 rerank 服务）。

---

## 四、和“部署的模型地址和接口没有改变”的关系

- **部署的模型** = 你现有的 embedding 服务、VLM 服务、rerank 服务（例如 141.61.16.3 上的 8002、10193 以及 vikingdb rerank）。
- **接口没变** = 这些服务仍然用原来的 URL、路径、鉴权方式；ov.conf 里填的就是这些地址和参数。
- **用 HTTP 调用 OpenViking 的原理**：
  - CLI 方式：Agent 只和 **OpenViking Server** 通信（HTTP），不直接调模型。
  - Server 收到请求后，在内部按 **自己的 ov.conf** 去调 embedding/VLM/rerank；若 Server 的 ov.conf 与 tools/openviking 的 ov.conf 一致，则**调用的 API 地址和 tools/openviking 一致**，部署的模型地址和接口也就没有改变。

总结：**HTTP 只负责“客户端 ↔ OpenViking Server”**；**依赖的模型功能**是 embedding、VLM、rerank；**这些模型的调用**由 **Server（或嵌入式进程）读 ov.conf** 决定，按其中配置的 api_base/host 发 HTTP 到你的模型服务。
