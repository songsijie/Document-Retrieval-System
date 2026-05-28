from __future__ import annotations

from typing import Any

from elasticsearch import Elasticsearch, NotFoundError

from base.es_index import ensure_es_index
from base.exception import create_custom_error, index_not_found_exception
from settings import ES_INDEX, ES_PHYSICAL_INDEX


def clear_index_data(es_client: Elasticsearch, index_name: str) -> dict[str, str | int]:
    """清空索引中的全部文档，保留索引结构和 mapping。"""
    if not es_client.indices.exists(index=index_name):
        raise create_custom_error(index_not_found_exception.code, f"{index_not_found_exception} {index_name}")

    response = es_client.delete_by_query(
        index=index_name,
        query={"match_all": {}},
        refresh=True,
    )
    deleted = int(dict(response).get("deleted", 0))
    return {"index": index_name, "deleted": deleted}


def _list_user_index_names(es_client: Elasticsearch) -> list[str]:
    """列出全部用户索引名（跳过系统索引）。"""
    try:
        indices_response = es_client.indices.get(index="*")
    except NotFoundError:
        return []

    return sorted(name for name in indices_response if not name.startswith("."))


def flush_all_indices(es_client: Elasticsearch) -> dict[str, list[str] | int | str]:
    """删除全部用户索引后，重建物理索引 articles_v1 并挂载别名 articles。"""
    deleted_indices: list[str] = []
    for index_name in _list_user_index_names(es_client):
        es_client.indices.delete(index=index_name)
        deleted_indices.append(index_name)

    ensure_es_index(es_client)

    return {
        "deleted_indices": deleted_indices,
        "count": len(deleted_indices),
        "recreated_index": ES_PHYSICAL_INDEX,
        "recreated_alias": ES_INDEX,
    }


def list_all_indices_mappings(es_client: Elasticsearch) -> dict[str, Any]:
    """查看全部用户索引及其 mapping、别名与文档数。"""
    try:
        mapping_response = es_client.indices.get_mapping(index="*")
        alias_response = es_client.indices.get_alias(index="*")
    except NotFoundError:
        return {"indices": [], "total_indices": 0}

    index_names = {
        name
        for name in (*mapping_response.keys(), *alias_response.keys())
        if not name.startswith(".")
    }

    indices: list[dict[str, Any]] = []
    for index_name in sorted(index_names):
        count_response = es_client.count(index=index_name)
        doc_count = int(dict(count_response).get("count", 0))
        aliases = sorted(alias_response.get(index_name, {}).get("aliases", {}))
        mappings = dict(mapping_response.get(index_name, {})).get("mappings", {})

        indices.append(
            {
                "index": index_name,
                "doc_count": doc_count,
                "aliases": aliases,
                "mappings": mappings,
            }
        )

    return {"indices": indices, "total_indices": len(indices)}
