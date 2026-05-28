from __future__ import annotations

from typing import Any

from elasticsearch import Elasticsearch, helpers

from app.retrieval.services.csv_template import generate_articles
from settings import ES_INDEX


def bulk_insert_articles(
    es_client: Elasticsearch,
    articles: list[dict[str, Any]],
    index_name: str | None = None,
) -> int:
    """将随机文献数据批量写入 ES。"""
    if not articles:
        return 0

    target_index = index_name or ES_INDEX
    actions = [
        {
            "_op_type": "index",
            "_index": target_index,
            "_id": str(article["pmid"]),
            "_source": article,
        }
        for article in articles
    ]

    success_count = 0
    for ok, _ in helpers.streaming_bulk(es_client, actions, raise_on_error=False):
        if ok:
            success_count += 1
    return success_count
