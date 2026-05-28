from __future__ import annotations

from elasticsearch import Elasticsearch

from settings import ES_INDEX


def clear_index_data(es_client: Elasticsearch, index_name: str | None = None) -> dict[str, str | int]:
    """清空索引中的全部文档，保留索引结构和 mapping。"""
    target_index = index_name or ES_INDEX
    if not es_client.indices.exists(index=target_index):
        return {"index": target_index, "deleted": 0}

    response = es_client.delete_by_query(
        index=target_index,
        query={"match_all": {}},
        refresh=True,
    )
    deleted = int(dict(response).get("deleted", 0))
    return {"index": target_index, "deleted": deleted}
