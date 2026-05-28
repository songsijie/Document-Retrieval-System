# Python 后端笔试题（数据库方向）

文献检索系统，数据存在 **Elasticsearch**。

代码推 Github / Gitee 公开仓库，`requirements.txt` 列依赖，`README.md` 写运行方式和必要说明。不需要真连 ES，本地 mock 或其他方式代替即可。


## 一、ES 查询封装

文献文档结构:

```python
{
    "pmid": 12345678,           # int
    "pub_year": 2024,           # int
    "title": "Article Title",     # text，english analyzer
    "abstracts": "...",            # text，english analyzer
    "authors": ["Alice", "Bob"],  # keyword 数组
    "pub_type": "Journal Article"  # keyword
}
```

封装三个查询能力:

1. **关键词全文检索**: 在 `title` 和 `abstracts` 上做全文搜索，分页返回。结果应能拿到总命中数和每条的相关度分数。
2. **按年聚合**: 给定关键词，统计近 3 年（以系统当前年份为当年，含当年）每年的命中数，按年份从新到旧。
3. **多条件过滤**: 关键词 + 年份 + 文献类型，三者 AND。注意区分 query 上下文和 filter 上下文: 年份和类型只过滤、不影响相关度评分。

README 简答: 为什么年份和文献类型走 filter 不走 query？

---

## 二、倒排索引

不依赖外部库，实现一个最小可用的倒排索引。提供四个能力:

- **添加文档**: 传入 `doc_id` 和文本，分词后入库。分词规则: 按非字母数字字符切分（即 `re.split(r'[^a-zA-Z0-9]+', text)`），统一小写。重复添加同一个 `doc_id` 视作覆盖。覆盖时，需要正确移除旧文档对应的倒排记录。
- **单词查询**: 返回包含某 term 的全部 `doc_id`，升序。
- **AND 查询**: 两个 term 同时命中的 `doc_id` 交集。要求走 posting list 交集，不要遍历全部文档。
- **删除**: tombstone 软删，标记但不立即清理倒排表; 后续查询应跳过已删除的 `doc_id`。

示例:

```
add(1, "Hello, World!")
add(2, "hello hello world python")
search("hello")                 -> [1, 2]
search_and("hello", "python")   -> [2]
delete(1)
search("hello")                 -> [2]
```

接口签名: `search_and(term1: str, term2: str) -> list[int]`，两个参数均为单个 term，调用方不做分词。

README 简答:

1. AND 查询走交集 vs 遍历全部文档，复杂度差多少？
2. 三个核心方法 (`add` / `search` / `search_and`) 的时间复杂度？
3. ES 的 segment merge 解决什么问题？tombstone 在 merge 时起什么作用？

---

## 三、CSV → ES 批量加载

实现一个 loader: 把一个 CSV 文件流式读入并批量写到 ES。

CSV 样例:

```csv
pmid,pub_year,title,abstracts,authors,pub_type
12345678,2024,"Title A","Abstract A","Alice;Bob","Journal Article"
12345679,2024,"Title B","Abstract B","Carol","Review"
12345680,bad_year,"Title C","Abstract C","Dave","Journal Article"
```

> 字段说明:
> - `pub_year`: 整数年份（如 `2024`），非数字值视为解析失败
> - `authors`: 多人以 `;` 分隔

要求:

- **流式读**，不能一次性把整个文件读进内存
- `authors` 字段按 `;` 切成数组
- 按批 (比如 500 条一批) 调 ES `_bulk` API
- 单行解析失败 (如 `pub_year` 不是数字) 记下行号和原因，跳过，不影响其他行
- 文档的 `_id` 用 `pmid`，重跑同一个文件 ES 里结果一致 (幂等)
- 文件读完要把最后不满一批的剩余数据也提交
- 返回成功条数和失败明细

**附加**: 实现 mapping 变更场景的迁移。假设旧索引 mapping 中 `pub_type` 为 `text` 类型，现需改为 `keyword` 以支持精确聚合。新建一个 `pub_type` 为 `keyword` 的新索引，把旧索引数据 reindex 过去，再原子切换 alias 从旧索引指向新索引。返回搬运的文档数。

README 说明: bulk 部分失败时怎么处理？

---

## 四、CSV → ES 同步方案设计

**只写方案，不写完整代码**。在 README 中分点回答，关键处贴函数签名或伪代码。

### 场景

每日有新的 CSV 文件落到本地目录，loader 增量同步到 ES。

数据量:
- 首次全量: 100 万条
- 每日增量: 1～5 万条
- 关键字段: `pmid` (唯一)、删除清单单独文件 `deleted.csv`
  - `deleted.csv` 格式: 单列，仅含 `pmid`，每行一个

#### 4.1 增量识别

每日增量由两部分组成：包含新增/修改记录的 CSV 文件，以及独立的删除清单 `deleted.csv`。分别怎么处理？分别对应 ES 哪个 API？为什么 `pmid` 当 `_id` 而不是自增 ID？

#### 4.2 写入性能

首次 100 万条全量灌入，怎么调最快？至少答 3 项 (bulk size、`refresh_interval`、`number_of_replicas`、客户端并发、translog flush 策略、灌完恢复默认值的步骤)。

#### 4.3 断点恢复

同步跑到一半进程挂了，重启如何续传？需要持久化什么？持久化存在哪里？给出 checkpoint 数据结构例子。

#### 4.4 幂等

同一个文件被处理两次，ES 最终状态完全一致。怎么保证？

