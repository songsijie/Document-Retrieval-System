from __future__ import annotations

from elasticsearch import Elasticsearch

from base.es_index import ARTICLE_INDEX_MAPPING


def migrate_pub_type_keyword(es_client: Elasticsearch, old_index: str, new_index: str, alias_name: str) -> int:
    """创建新索引、reindex 旧数据，并原子切换 alias。"""
    # 创建新索引：使用更新后的 mapping 承载迁移数据。
    if not es_client.indices.exists(index=new_index):
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
        raise RuntimeError(f"alias update failed: {alias_response_dict}")

    # 不删除旧索引，便于回滚或后续人工清理。
    return migrated_count
