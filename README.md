# Document Retrieval System

## 项目简介

最小 FastAPI 文献检索项目，围绕 Elasticsearch 文献数据实现查询封装、倒排索引、CSV 批量导入和 mapping 迁移示例。

项目包含两类检索能力：

- 基于 Elasticsearch 的文献全文检索、聚合、过滤、CSV 导入和 mapping 迁移。
- 基于进程内内存单例的手写倒排索引，用于展示倒排索引的构建、查询、AND 查询和 tombstone 软删除能力。

## 在线体验地址

- http://drs.songsijie.cn/docs
- http://songsijie.cn:8010/docs(当上面无法访问时,可尝试这个)

## 技术要求

- Python >= 3.12
- Docker / Docker Compose（使用容器启动时需要）
- Elasticsearch 8.x（本地直接启动时需要自行准备）
- Redis 5.x/7.x（本地直接启动且启用限流中间件时需要自行准备）

## 安装方法

### 本地启动

1. 创建并激活虚拟环境（推荐）

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 启动项目

```bash
# Windows(cmd)
set APP_ENV=dev
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# macOS/Linux
APP_ENV=dev uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

本地启动需自行准备 Elasticsearch 和 Redis，并通过环境变量配置连接信息。

### Docker 启动

```bash
docker compose up --build -d
```

该命令会构建并启动 FastAPI、Elasticsearch 和 Redis，无需单独安装依赖或配置 ES / Redis。

### 代码规范

本项目使用 Ruff 进行代码检查和格式化，配置详见 `pyproject.toml`。

- 检查代码：`ruff check .`
- 修复问题：`ruff check --fix .`
- 格式化代码：`ruff format .`

### 本地访问

- 健康检查：`http://127.0.0.1:8000/health`
- Swagger 文档：`http://127.0.0.1:8000/docs`（仅 `APP_ENV=dev` 时开启）

---

## 项目目录结构

```
Document-Retrieval-System/
├── main.py                        # 应用入口（FastAPI 实例、路由注册、中间件挂载）
├── requirements.txt               # Python 依赖
├── pyproject.toml                 # 项目配置 & Ruff 规则
├── Dockerfile                     # Docker 构建文件
├── docker-compose.yml             # 本地编排（app + ES + Redis）
│
├── app/                           # 业务应用
│   ├── retrieval/                 #   文献检索模块
│   │   ├── router.py              #     API 路由
│   │   ├── schemas.py             #     Pydantic 请求/响应模型
│   │   └── services/              #     核心功能实现
│   │       ├── es_query.py        #       ES 查询封装
│   │       ├── inverted_index.py  #       手写倒排索引
│   │       ├── csv_loader.py      #       CSV bulk 导入
│   │       ├── csv_template.py    #       CSV 模板与示例数据生成
│   │       └── migration.py       #       reindex 与 alias 切换
│   └── test/                      #   测试工具模块（dev 环境）
│       ├── router.py              #     API 路由
│       ├── schemas.py             #     Pydantic 请求/响应模型
│       └── services/              #     核心功能实现
│           ├── article_query.py   #       scroll 游标分页查询
│           ├── index_admin.py     #       索引管理（清空、flush、mapping）
│           └── sample_data.py     #       批量写入示例数据
│
├── base/                          # 基础库 & 工具
│   ├── es.py                      #   Elasticsearch 客户端
│   ├── exception.py               #   自定义异常
│   ├── cache.py                   #   Redis 缓存
│   ├── decorator.py               #   装饰器
│   └── utils.py                   #   通用工具函数
│
├── middleware/                    # 中间件
│   ├── log.py                     #   请求日志
│   ├── rate_limit.py              #   限流
│   ├── ip_filter.py               #   IP 白名单过滤
│   ├── timeout.py                 #   超时控制
│   ├── exception.py               #   全局异常处理
│   └── response.py                #   统一响应格式
│
├── settings/                      # 多环境配置
│   ├── __init__.py                #   环境加载
│   ├── dev.py                     #   开发环境
│   └── prod.py                    #   生产环境
│
└── docs/                          # 文档
    └── python后端开发笔试题（数据库方向）.md
```

---

## 技术栈

### 通用

| 层级 | 技术 | 说明 |
|------|------|------|
| Web 框架 | FastAPI | 异步高性能 Web 框架 |
| 搜索引擎 | Elasticsearch 8.x | 文献全文检索、聚合、bulk 导入与 mapping 迁移 |
| 缓存 | Redis | 通过 redis-py 客户端，用于限流中间件 |
| 数据校验 | Pydantic | 请求/响应模型校验与序列化 |
| 运行服务 | Uvicorn | ASGI Server |
| 容器编排 | Docker Compose | 本地一键启动 app、ES、Redis |
| 代码规范 | Ruff | Lint + Format |

---

## 环境变量

### Elasticsearch

通过环境变量配置 ES，不在代码仓库中保存真实密钥。

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ES_HOSTS` | ES 地址，多个地址用英文逗号分隔 | `http://localhost:9200` |
| `ES_USERNAME` | 用户名，可选 | - |
| `ES_PASSWORD` | 密码，可选 | - |
| `ES_API_KEY` | API Key，可选，优先级高于用户名密码 | - |
| `ES_PHYSICAL_INDEX` | 文献物理索引名 | `articles_v1` |
| `ES_INDEX` | 文献业务别名（读写统一走别名） | `articles` |
| `ES_REQUEST_TIMEOUT` | 请求超时秒数 | `30` |

启动时会创建物理索引 `articles_v1` 并挂载别名 `articles`。CSV 导入与检索均通过别名访问；mapping 迁移时 `old_index` 填物理索引名，`alias_name` 填 `articles`。

CSV 导入和 mapping 迁移接口会写入或修改 Elasticsearch。

### Redis

Redis 用于限流中间件。

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `CACHE_HOST` | Redis 主机 | `127.0.0.1` |
| `CACHE_PORT` | Redis 端口 | `6379` |
| `CACHE_PASSWORD` | Redis 密码，可选 | - |
| `CACHE_DB` | Redis DB | `0` |
| `CACHE_KEYPREFIX` | Redis Key 前缀 | `document_retrieval` |

---

## 接口列表

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/retrieval/articles/search` | 关键词全文检索 |
| GET | `/retrieval/articles/aggregate-by-year` | 近三年按年份聚合 |
| GET | `/retrieval/articles/filter` | 关键词 + 年份 + 文献类型过滤 |
| POST | `/retrieval/inverted-index/documents` | 添加或覆盖内存倒排索引文档 |
| GET | `/retrieval/inverted-index/search` | 单 term 查询 |
| GET | `/retrieval/inverted-index/search-and` | 两个 term 的 AND 查询 |
| DELETE | `/retrieval/inverted-index/documents/{doc_id}` | tombstone 软删除文档 |
| GET | `/retrieval/csv/template` | 下载 CSV 导入模板 |
| POST | `/retrieval/csv/load` | 上传 CSV 文件批量导入 ES |
| POST | `/retrieval/migrations/pub-type-keyword` | reindex 并原子切换 alias |

---

## 笔试题简答

### 一、ES 查询封装

**问：为什么年份和文献类型走 filter 不走 query？**

答：年份和文献类型是结构化精确条件，只决定文档是否符合条件，不应该参与相关度评分。放在 filter 上下文可以避免影响 `_score`，也更利于 Elasticsearch 缓存过滤结果。

---

### 二、倒排索引

**问 1：AND 查询走 posting list 交集 vs 遍历全部文档，复杂度差多少？**

答：posting list 交集复杂度约为 `O(len(p1) + len(p2))`，其中 `p1` 和 `p2` 是两个 term 的倒排列表长度。遍历全部文档复杂度是 `O(N)`。当关键词只命中少量文档时，posting list 交集会明显更快。

**问 2：三个核心方法（`add` / `search` / `search_and`）的时间复杂度？**

答：

- `add`：与新文本 term 数和旧文档 term 数相关，覆盖写入时需要先清理旧倒排记录。
- `search`：与该 term 的 posting list 长度相关。
- `search_and`：与两个 term 的 posting list 长度相关，使用较短列表遍历并检查交集。

**问 3：ES 的 segment merge 解决什么问题？tombstone 在 merge 时起什么作用？**

答：Elasticsearch 写入会产生多个不可变 segment。segment merge 会把小 segment 合并为更大的 segment，减少搜索时需要访问的 segment 数量，并清理已经删除或被覆盖的旧文档。tombstone 用来标记逻辑删除的文档，merge 时这些文档不会写入新 segment，从而完成物理清理。

---

### 三、CSV → ES 批量加载

**问：bulk 部分失败时怎么处理？**

答：bulk 返回中每一条 action 都有独立结果。成功项保留，失败项记录 `_id`、行号和错误原因。由于文档 `_id` 使用 `pmid`，失败项可以修复后按相同 `_id` 幂等重试，不需要回滚整个批次。

---

### 四、CSV → ES 同步方案设计

**问 4.1：每日增量由新增/修改 CSV 和 `deleted.csv` 两部分组成，分别怎么处理？对应 ES 哪个 API？为什么 `pmid` 当 `_id` 而不是自增 ID？**

答：

- 新增/修改 CSV：流式读取，按批 `_bulk` + `index`（`_id = pmid`），覆盖写入。
- `deleted.csv`：单列 `pmid`，按批 `_bulk` + `delete`。
- `pmid` 是业务唯一键，重跑覆盖同文档、删除可精确命中；自增 ID 会导致重复文档。

**问 4.2：首次 100 万条全量灌入，怎么调最快？**

答：灌入阶段可临时调大 `bulk size`、拉长或关闭 `refresh_interval`、将 `number_of_replicas` 设为 `0`、客户端多 worker 并发提交 bulk，可选 `translog.durability = async`。灌完后恢复 `refresh_interval` 和副本数，并校验文档总数。

**问 4.3：同步跑到一半进程挂了，重启如何续传？需要持久化什么？存在哪里？**

答：从 checkpoint 记录的进度续传，每批 bulk 成功后再更新。持久化 `file_name`、`file_hash`、`byte_offset` / `line_number`、`last_batch_no`、`status`、`updated_at`，可存本地 JSON / SQLite 或独立状态索引。

```json
{ "file_name": "articles_20260527.csv", "file_hash": "a1b2c3", "byte_offset": 1048576, "status": "running" }
```

**问 4.4：同一个文件被处理两次，ES 最终状态完全一致，怎么保证？**

答：`_id = pmid` 使 `index` 重复提交结果相同、`delete` 重复执行无副作用；记录已处理文件的 `file_name + file_hash` 跳过重复文件；checkpoint 仅在批次成功后更新，失败项单独重试。
