from __future__ import annotations

from elasticsearch import Elasticsearch
from fastapi import APIRouter, Depends, Query

from app.test.schemas import (
    ArticleListResponse,
    ClearIndexResponse,
    FlushIndicesResponse,
    GenerateArticlesResponse,
    ListIndicesMappingsResponse,
)
from app.test.services.article_query import list_articles
from app.test.services.index_admin import clear_index_data, flush_all_indices, list_all_indices_mappings
from app.retrieval.services.csv_template import generate_articles
from app.test.services.sample_data import bulk_insert_articles
from base.es import get_es_client
from settings import ES_INDEX

router = APIRouter()


@router.get(
    "/articles",
    response_model=ArticleListResponse,
    tags=["测试工具"],
    summary="游标分页查询全部文献",
    description="使用 Elasticsearch scroll 游标分页返回文献数据。首次请求不传 scroll_id，后续请求传入上一次返回的 scroll_id。",
)
async def list_articles_api(
    page_size: int = Query(10, ge=1, le=100, description="每页返回数量，最大 100"),
    scroll_id: str | None = Query(None, description="游标 ID，首次请求不传；后续仅传 scroll_id，page_size 以首次请求为准"),
    es_client: Elasticsearch = Depends(get_es_client),
) -> ArticleListResponse:
    return ArticleListResponse.model_validate(list_articles(es_client=es_client, page_size=page_size, scroll_id=scroll_id))


@router.post(
    "/articles/generate",
    response_model=GenerateArticlesResponse,
    tags=["测试工具"],
    summary="生成随机文献数据",
    description="按笔试题字段格式生成随机文献，并批量写入 Elasticsearch。",
)
async def generate_articles_api(
    count: int = Query(10, ge=0, le=10000, description="生成条数，0 表示不写入"),
    es_client: Elasticsearch = Depends(get_es_client),
) -> GenerateArticlesResponse:
    articles = generate_articles(count)
    success = bulk_insert_articles(es_client=es_client, articles=articles)
    return GenerateArticlesResponse(success=success, index=ES_INDEX)


@router.post(
    "/index/clear",
    response_model=ClearIndexResponse,
    tags=["测试工具"],
    summary="清空索引数据",
    description="删除指定索引或别名中的全部文档，保留索引结构和 mapping。",
)
async def clear_index_api(
    index_name: str = Query(ES_INDEX, description="索引或别名名称，默认 articles"),
    es_client: Elasticsearch = Depends(get_es_client),
) -> ClearIndexResponse:
    return ClearIndexResponse.model_validate(clear_index_data(es_client=es_client, index_name=index_name))


@router.post(
    "/index/flush",
    response_model=FlushIndicesResponse,
    tags=["测试工具"],
    summary="一键重建 ES 索引",
    description="删除全部用户索引后，重建物理索引 articles_v1 并挂载别名 articles。",
)
async def flush_indices_api(
    es_client: Elasticsearch = Depends(get_es_client),
) -> FlushIndicesResponse:
    return FlushIndicesResponse.model_validate(flush_all_indices(es_client=es_client))


@router.get(
    "/indices",
    response_model=ListIndicesMappingsResponse,
    tags=["测试工具"],
    summary="查看全部索引及 mapping",
    description="列出全部用户索引的名称、文档数、别名及 mapping 定义。",
)
async def list_indices_mappings_api(
    es_client: Elasticsearch = Depends(get_es_client),
) -> ListIndicesMappingsResponse:
    return ListIndicesMappingsResponse.model_validate(list_all_indices_mappings(es_client=es_client))
