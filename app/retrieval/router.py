from __future__ import annotations

from elasticsearch import Elasticsearch
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile

from app.retrieval.schemas import (
    ArticleSearchResponse,
    CsvLoadResponse,
    InvertedIndexDocumentRequest,
    InvertedIndexSearchAndResponse,
    InvertedIndexSearchResponse,
    InvertedIndexWriteResponse,
    MigrationRequest,
    MigrationResponse,
    YearAggregationItem,
)
from app.retrieval.services.csv_loader import load_csv_to_es
from app.retrieval.services.es_query import aggregate_by_year, filter_articles, search_articles
from app.retrieval.services.inverted_index import InvertedIndex
from app.retrieval.services.migration import migrate_pub_type_keyword
from base.es import get_es_client

router = APIRouter()

# 使用进程内单例保存手写倒排索引状态，服务重启后会清空。
inverted_index = InvertedIndex()


@router.get(
    "/articles/search",
    response_model=ArticleSearchResponse,
    tags=["笔试题一：ES 查询封装"],
    summary="关键词全文检索",
    description="关键词全文检索：在 title 和 abstracts 上查询，使用 scroll 游标分页返回总命中数、相关度评分和文档内容。",
)
async def search_articles_api(
    keyword: str = Query(..., description="全文检索关键词"),
    page_size: int = Query(10, ge=1, le=100, description="每页返回数量，最大 100"),
    scroll_id: str | None = Query(None, description="游标 ID，首次请求不传；后续仅传 scroll_id，page_size 以首次请求为准"),
    es_client: Elasticsearch = Depends(get_es_client),
) -> ArticleSearchResponse:
    return ArticleSearchResponse.model_validate(search_articles(es_client=es_client, keyword=keyword, page_size=page_size, scroll_id=scroll_id))


@router.get(
    "/articles/aggregate-by-year",
    response_model=list[YearAggregationItem],
    tags=["笔试题一：ES 查询封装"],
    summary="近三年按年份聚合",
    description="按年聚合：给定关键词，统计近三年每年的命中数量。",
)
async def aggregate_by_year_api(
    keyword: str = Query(..., description="聚合使用的关键词"),
    es_client: Elasticsearch = Depends(get_es_client),
) -> list[YearAggregationItem]:
    # 调用 ES 聚合封装，年份范围在 filter 上下文中处理。
    return [YearAggregationItem.model_validate(item) for item in aggregate_by_year(es_client=es_client, keyword=keyword)]


@router.get(
    "/articles/filter",
    response_model=ArticleSearchResponse,
    tags=["笔试题一：ES 查询封装"],
    summary="多条件过滤检索",
    description="多条件过滤：关键词、年份、文献类型三者 AND，年份和类型走 filter 上下文，使用 scroll 游标分页返回。",
)
async def filter_articles_api(
    keyword: str = Query(..., description="全文检索关键词"),
    pub_year: int = Query(..., description="发表年份"),
    pub_type: str = Query(..., description="文献类型"),
    page_size: int = Query(10, ge=1, le=100, description="每页返回数量，最大 100"),
    scroll_id: str | None = Query(None, description="游标 ID，首次请求不传；后续仅传 scroll_id，page_size 以首次请求为准"),
    es_client: Elasticsearch = Depends(get_es_client),
) -> ArticleSearchResponse:
    return ArticleSearchResponse.model_validate(
        filter_articles(
            es_client=es_client,
            keyword=keyword,
            pub_year=pub_year,
            pub_type=pub_type,
            page_size=page_size,
            scroll_id=scroll_id,
        )
    )


@router.post(
    "/inverted-index/documents",
    response_model=InvertedIndexWriteResponse,
    tags=["笔试题二：倒排索引"],
    summary="添加或覆盖倒排索引文档",
    description="添加文档：写入或覆盖内存倒排索引中的文档。",
)
async def add_inverted_index_document(request: InvertedIndexDocumentRequest) -> InvertedIndexWriteResponse:
    # 写入内存倒排索引；同一 doc_id 会覆盖旧文本。
    inverted_index.add(request.doc_id, request.text)
    return InvertedIndexWriteResponse(doc_id=request.doc_id, status="indexed")


@router.get(
    "/inverted-index/search",
    response_model=InvertedIndexSearchResponse,
    tags=["笔试题二：倒排索引"],
    summary="单词查询",
    description="单词查询：返回包含指定 term 的全部未删除文档 ID。",
)
async def search_inverted_index(term: str = Query(..., description="查询 term")) -> InvertedIndexSearchResponse:
    # 直接查询 term 对应的 posting list，并跳过 tombstone 文档。
    return InvertedIndexSearchResponse(term=term, doc_ids=inverted_index.search(term))


@router.get(
    "/inverted-index/search-and",
    response_model=InvertedIndexSearchAndResponse,
    tags=["笔试题二：倒排索引"],
    summary="AND 查询",
    description="AND 查询：通过两个 term 的 posting list 交集返回同时命中的文档 ID。",
)
async def search_inverted_index_and(
    term1: str = Query(..., description="第一个 term"),
    term2: str = Query(..., description="第二个 term"),
) -> InvertedIndexSearchAndResponse:
    # 通过两个 posting list 求交集，不遍历全部文档。
    return InvertedIndexSearchAndResponse(terms=[term1, term2], doc_ids=inverted_index.search_and(term1, term2))


@router.delete(
    "/inverted-index/documents/{doc_id}",
    response_model=InvertedIndexWriteResponse,
    tags=["笔试题二：倒排索引"],
    summary="软删除倒排索引文档",
    description="删除文档：写入 tombstone 软删除标记，查询时跳过该文档。",
)
async def delete_inverted_index_document(doc_id: int) -> InvertedIndexWriteResponse:
    # 写入 tombstone，查询时会跳过该文档。
    inverted_index.delete(doc_id)
    return InvertedIndexWriteResponse(doc_id=doc_id, status="deleted")


@router.post(
    "/csv/load",
    response_model=CsvLoadResponse,
    tags=["笔试题三：CSV → ES 批量加载"],
    summary="CSV 批量导入 ES",
    description="CSV 批量加载：上传 CSV 文件后流式读取，并按批写入 Elasticsearch。",
)
async def load_csv(
    file: UploadFile = File(..., description="CSV 文件"),
    batch_size: int = Form(default=500, ge=1, description="bulk 每批写入数量"),
    es_client: Elasticsearch = Depends(get_es_client),
) -> CsvLoadResponse:
    return CsvLoadResponse.model_validate(load_csv_to_es(es_client=es_client, file_obj=file.file, batch_size=batch_size))


@router.post(
    "/migrations/pub-type-keyword",
    response_model=MigrationResponse,
    tags=["笔试题三：CSV → ES 批量加载"],
    summary="pub_type keyword 迁移",
    description="Mapping 迁移：新建 pub_type 为 keyword 的索引，reindex 后原子切换 alias。",
)
async def migrate_pub_type_keyword_api(
    request: MigrationRequest,
    es_client: Elasticsearch = Depends(get_es_client),
) -> MigrationResponse:
    # 创建新索引、执行 reindex，并将 alias 原子切换到新索引。
    migrated_count = migrate_pub_type_keyword(
        es_client=es_client,
        old_index=request.old_index,
        new_index=request.new_index,
        alias_name=request.alias_name,
    )
    return MigrationResponse(migrated_count=migrated_count)
