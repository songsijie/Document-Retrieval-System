from __future__ import annotations

from elasticsearch import Elasticsearch

from base.es_index import ARTICLE_INDEX_MAPPING
from base.exception import create_custom_error, index_already_exists_exception


def migrate_pub_type_keyword(es_client: Elasticsearch, old_index: str, new_index: str, alias_name: str) -> int:
    """创建新索引、reindex 旧数据，并原子切换 alias。"""
    if es_client.indices.exists(index=new_index):
        raise create_custom_error(index_already_exists_exception.code, f"{index_already_exists_exception} {new_index}")

    es_client.indices.create(index=new_index, **ARTICLE_INDEX_MAPPING)

    # reindex：从旧索引复制数据到新索引，并等待迁移完成。
    response = es_client.reindex(
        source={"index": old_index},
        dest={"index": new_index},
        refresh=True,
        wait_for_completion=True,
    )
    migrated_count = int(dict(response).get("created", 0) + dict(response).get("updated", 0))

    # alias 原子切换：同一次 update_aliases 中移除旧指向并添加新指向。
    alias_response = es_client.indices.update_aliases(
        actions=[
            {"remove": {"index": old_index, "alias": alias_name, "must_exist": False}},
            {"add": {"index": new_index, "alias": alias_name}},
        ]
    )
    alias_response_dict = dict(alias_response)
    if alias_response_dict.get("errors"):
        fatal_results = [
            result
            for result in alias_response_dict.get("action_results", [])
            if int(result.get("status", 200)) >= 400
            and not (
                result.get("action", {}).get("type") == "remove"
                and result.get("error", {}).get("type") == "aliases_not_found_exception"
            )
        ]
        if fatal_results:
            raise RuntimeError(f"alias update failed: {alias_response_dict}")

    # 不删除旧索引，便于回滚或后续人工清理。
    return migrated_count
