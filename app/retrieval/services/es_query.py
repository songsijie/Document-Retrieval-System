from __future__ import annotations

from datetime import datetime
from typing import Any

from elasticsearch import Elasticsearch

from base.es_scroll import scroll_search
from settings import ES_INDEX


def _keyword_query(keyword: str) -> dict[str, Any]:
    """构造 title 和 abstracts 上的全文检索 query。"""
    return {
        "multi_match": {
            "query": keyword,
            "fields": ["title", "abstracts"],
        }
    }


def _normalize_scroll_hits(result: dict[str, Any]) -> dict[str, Any]:
    """统一整理 scroll 查询结果，保留总数、评分和原始文档。"""
    items = [
        {
            "score": hit.get("_score"),
            "source": hit.get("_source", {}),
        }
        for hit in result.get("hits", [])
    ]
    return {
        "total": result["total"],
        "page_size": result["page_size"],
        "scroll_id": result["scroll_id"],
        "has_more": result["has_more"],
        "items": items,
    }


def _validate_keyword(keyword: str) -> str:
    """清洗并校验关键词不能为空。"""
    cleaned_keyword = keyword.strip()
    if not cleaned_keyword:
        msg = "keyword must not be empty"
        raise ValueError(msg)
    return cleaned_keyword


def search_articles(
    es_client: Elasticsearch,
    keyword: str,
    page_size: int = 10,
    scroll_id: str | None = None,
    index_name: str | None = None,
) -> dict[str, Any]:
    """关键词全文检索：在 title 和 abstracts 上执行 ES multi_match 查询。"""
    cleaned_keyword = _validate_keyword(keyword)
    result = scroll_search(
        es_client=es_client,
        query=_keyword_query(cleaned_keyword),
        page_size=page_size,
        scroll_id=scroll_id,
        index_name=index_name,
    )
    return _normalize_scroll_hits(result)


def aggregate_by_year(es_client: Elasticsearch, keyword: str, index_name: str | None = None) -> list[dict[str, int]]:
    """年份聚合：先按关键词检索，再统计最近三年的 pub_year 分布。"""
    cleaned_keyword = _validate_keyword(keyword)
    current_year = datetime.now().year
    start_year = current_year - 2
    response = es_client.search(
        index=index_name or ES_INDEX,
        size=0,
        query={
            "bool": {
                # query 上下文：关键词命中参与相关性计算。
                "must": [_keyword_query(cleaned_keyword)],
                # filter 上下文：年份范围只做过滤，不影响评分。
                "filter": [{"range": {"pub_year": {"gte": start_year, "lte": current_year}}}],
            }
        },
        aggs={
            "by_year": {
                "terms": {
                    "field": "pub_year",
                    "order": {"_key": "desc"},
                    "size": 3,
                }
            }
        },
    )
    buckets = dict(response).get("aggregations", {}).get("by_year", {}).get("buckets", [])
    counts_by_year = {int(bucket["key"]): int(bucket["doc_count"]) for bucket in buckets}
    return [{"year": year, "count": counts_by_year.get(year, 0)} for year in range(current_year, start_year - 1, -1)]


def filter_articles(
    es_client: Elasticsearch,
    keyword: str,
    pub_year: int,
    pub_type: str,
    page_size: int = 10,
    scroll_id: str | None = None,
    index_name: str | None = None,
) -> dict[str, Any]:
    """复合过滤检索：关键词全文查询叠加年份和发表类型过滤。"""
    cleaned_keyword = _validate_keyword(keyword)
    cleaned_pub_type = pub_type.strip()
    if not cleaned_pub_type:
        msg = "pub_type must not be empty"
        raise ValueError(msg)

    current_year = datetime.now().year
    if not 1800 <= pub_year <= current_year + 1:
        msg = "pub_year is out of supported range"
        raise ValueError(msg)

    result = scroll_search(
        es_client=es_client,
        query={
            "bool": {
                # query 上下文：关键词检索负责召回与评分。
                "must": [_keyword_query(cleaned_keyword)],
                # filter 上下文：精确条件过滤结果集，不参与评分。
                "filter": [
                    {"term": {"pub_year": pub_year}},
                    {"term": {"pub_type": cleaned_pub_type}},
                ],
            }
        },
        page_size=page_size,
        scroll_id=scroll_id,
        index_name=index_name,
    )
    return _normalize_scroll_hits(result)
