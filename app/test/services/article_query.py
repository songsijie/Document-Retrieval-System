from __future__ import annotations

from typing import Any

from elasticsearch import Elasticsearch

from base.es_scroll import scroll_search


def list_articles(
    es_client: Elasticsearch,
    page_size: int = 10,
    scroll_id: str | None = None,
    index_name: str | None = None,
) -> dict[str, Any]:
    """使用 ES scroll 游标分页查询索引中的全部文献数据。"""
    result = scroll_search(
        es_client=es_client,
        query={"match_all": {}},
        page_size=page_size,
        scroll_id=scroll_id,
        index_name=index_name,
        sort=[{"pmid": {"order": "desc"}}],
    )
    return {
        "total": result["total"],
        "page_size": result["page_size"],
        "scroll_id": result["scroll_id"],
        "has_more": result["has_more"],
        "items": [hit.get("_source", {}) for hit in result["hits"]],
    }
