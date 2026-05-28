from __future__ import annotations

from typing import Any

from elasticsearch import Elasticsearch

from settings import ES_INDEX

MAX_PAGE_SIZE = 100
SCROLL_TIMEOUT = "2m"


def validate_page_size(page_size: int) -> None:
    """校验每页返回数量。"""
    if page_size < 1:
        msg = "page_size must be greater than or equal to 1"
        raise ValueError(msg)
    if page_size > MAX_PAGE_SIZE:
        msg = f"page_size must be less than or equal to {MAX_PAGE_SIZE}"
        raise ValueError(msg)


def extract_total(hits_block: dict[str, Any]) -> int:
    """从 ES hits 块中提取文档总数。"""
    total = hits_block.get("total", 0)
    if isinstance(total, dict):
        return int(total.get("value", 0))
    return int(total)


def clear_scroll(es_client: Elasticsearch, scroll_id: str | None) -> None:
    """清理 scroll 上下文，避免 ES 资源泄漏。"""
    if not scroll_id:
        return
    try:
        es_client.clear_scroll(scroll_id=scroll_id)
    except Exception:
        pass


def scroll_search(
    es_client: Elasticsearch,
    query: dict[str, Any],
    page_size: int = 10,
    scroll_id: str | None = None,
    index_name: str | None = None,
    sort: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """使用 ES scroll 游标执行查询，返回总数、游标和原始 hits。"""
    validate_page_size(page_size)

    if scroll_id:
        response = es_client.scroll(scroll_id=scroll_id, scroll=SCROLL_TIMEOUT)
    else:
        search_kwargs: dict[str, Any] = {
            "index": index_name or ES_INDEX,
            "query": query,
            "size": page_size,
            "scroll": SCROLL_TIMEOUT,
        }
        if sort is not None:
            search_kwargs["sort"] = sort
        response = es_client.search(**search_kwargs)

    response_dict = dict(response)
    hits_block = response_dict.get("hits", {})
    hits = hits_block.get("hits", [])
    total = extract_total(hits_block)
    current_scroll_id = response_dict.get("_scroll_id", scroll_id)

    if not hits:
        clear_scroll(es_client, current_scroll_id)
        return {
            "total": total,
            "page_size": page_size,
            "scroll_id": None,
            "has_more": False,
            "hits": [],
        }

    has_more = len(hits) == page_size
    if not has_more:
        clear_scroll(es_client, current_scroll_id)
        current_scroll_id = None

    return {
        "total": total,
        "page_size": page_size,
        "scroll_id": current_scroll_id,
        "has_more": has_more,
        "hits": hits,
    }
