from __future__ import annotations

from typing import Any

from elasticsearch import Elasticsearch, NotFoundError

from settings import ES_INDEX, ES_PHYSICAL_INDEX

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


def ensure_es_index(
    es_client: Elasticsearch,
    physical_index: str | None = None,
    alias_name: str | None = None,
) -> bool:
    """确保物理索引存在，并将业务别名指向该物理索引。"""
    target_physical = physical_index or ES_PHYSICAL_INDEX
    target_alias = alias_name or ES_INDEX

    created = False
    if not es_client.indices.exists(index=target_physical):
        es_client.indices.create(index=target_physical, **ARTICLE_INDEX_MAPPING)
        created = True

    try:
        es_client.indices.get_alias(name=target_alias)
    except NotFoundError:
        es_client.indices.put_alias(index=target_physical, name=target_alias)
        created = True

    return created
