from __future__ import annotations

from typing import Any

from elasticsearch import Elasticsearch

from settings import ES_INDEX

ARTICLE_INDEX_MAPPING: dict[str, Any] = {
    "mappings": {
        "properties": {
            "pmid": {"type": "integer"},
            "pub_year": {"type": "integer"},
            "title": {"type": "text", "analyzer": "english"},
            "abstracts": {"type": "text", "analyzer": "english"},
            "authors": {"type": "keyword"},
            "pub_type": {"type": "keyword"},
        }
    }
}


def ensure_es_index(es_client: Elasticsearch, index_name: str | None = None) -> bool:
    """检查文献索引是否存在，不存在则按标准 mapping 创建。"""
    target_index = index_name or ES_INDEX
    if es_client.indices.exists(index=target_index):
        return False

    es_client.indices.create(index=target_index, **ARTICLE_INDEX_MAPPING)
    return True
