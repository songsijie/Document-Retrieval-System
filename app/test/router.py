from __future__ import annotations

from elasticsearch import Elasticsearch
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.test.schemas import ArticleListResponse, ClearIndexResponse, GenerateArticlesResponse
from app.test.services.article_query import list_articles
from app.test.services.index_admin import clear_index_data
from app.test.services.sample_data import articles_to_csv, bulk_insert_articles, generate_articles
from base.es import get_es_client
from settings import ES_INDEX

router = APIRouter()


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
    description="一键删除默认索引中的全部文档，保留索引结构和 mapping。",
)
async def clear_index_api(
    es_client: Elasticsearch = Depends(get_es_client),
) -> ClearIndexResponse:
    return ClearIndexResponse.model_validate(clear_index_data(es_client=es_client))


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
    return ArticleListResponse.model_validate(
        list_articles(es_client=es_client, page_size=page_size, scroll_id=scroll_id)
    )


@router.get(
    "/csv/template",
    tags=["测试工具"],
    summary="下载 CSV 模板",
    description="下载符合笔试题格式的 CSV 模板，authors 字段使用分号分隔。",
)
async def download_csv_template_api(
    count: int = Query(10, ge=0, le=10000, description="模板中的示例数据条数，0 表示仅返回表头"),
) -> Response:
    csv_content = articles_to_csv(generate_articles(count))
    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="articles_template.csv"'},
    )
