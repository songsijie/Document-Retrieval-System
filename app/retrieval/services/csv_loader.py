from __future__ import annotations

import csv
import io
from typing import Any, BinaryIO

from elasticsearch import Elasticsearch, helpers

from settings import ES_INDEX


def _parse_row(row: dict[str, str | None], line_number: int) -> dict[str, Any]:
    """解析单行 CSV，转换字段类型并整理为 ES 文档。"""
    try:
        pmid = int(row["pmid"])
        pub_year = int(row["pub_year"])
    except KeyError as exc:
        msg = f"missing required field: {exc.args[0]}"
        raise ValueError(msg) from exc
    except (TypeError, ValueError) as exc:
        msg = "pmid and pub_year must be integers"
        raise ValueError(msg) from exc

    title = row.get("title") or ""
    abstracts = row.get("abstracts") or ""
    authors_text = row.get("authors") or ""
    pub_type = row.get("pub_type") or ""
    authors = [author.strip() for author in authors_text.split(";") if author.strip()]
    return {
        "_id": str(pmid),
        "_source": {
            "pmid": pmid,
            "pub_year": pub_year,
            "title": title,
            "abstracts": abstracts,
            "authors": authors,
            "pub_type": pub_type,
        },
        "_line_number": line_number,
    }


def _flush_batch(es_client: Elasticsearch, batch: list[dict[str, Any]], index_name: str) -> tuple[int, list[dict[str, Any]]]:
    """将当前批次转换为 ES bulk action 并提交。"""
    actions = [
        {
            "_op_type": "index",
            "_index": index_name,
            "_id": item["_id"],
            "_source": item["_source"],
            "_line_number": item["_line_number"],
        }
        for item in batch
    ]

    success_count = 0
    failures: list[dict[str, Any]] = []
    for action, (ok, item) in zip(actions, helpers.streaming_bulk(es_client, actions, raise_on_error=False), strict=False):
        response_action = item.get("index", {})
        if ok:
            success_count += 1
        else:
            failures.append(
                {
                    "id": response_action.get("_id", action["_id"]),
                    "line_number": action["_line_number"],
                    "reason": response_action.get("error", "bulk item failed"),
                }
            )
    return success_count, failures


def load_csv_to_es(
    es_client: Elasticsearch,
    file_obj: BinaryIO,
    index_name: str | None = None,
    batch_size: int = 500,
) -> dict[str, Any]:
    """流式读取上传的 CSV 文件，按批写入 ES，并返回成功数量和失败明细。"""
    if batch_size < 1:
        msg = "batch_size must be greater than or equal to 1"
        raise ValueError(msg)

    target_index = index_name or ES_INDEX
    success_count = 0
    failures: list[dict[str, Any]] = []
    batch: list[dict[str, Any]] = []

    file_obj.seek(0)
    text_stream = io.TextIOWrapper(file_obj, encoding="utf-8", newline="")
    try:
        reader = csv.DictReader(text_stream)
        for line_number, row in enumerate(reader, start=2):
            try:
                batch.append(_parse_row(row, line_number))
            except ValueError as exc:
                failures.append({"line_number": line_number, "reason": str(exc)})
                continue

            if len(batch) >= batch_size:
                batch_success, batch_failures = _flush_batch(es_client, batch, target_index)
                success_count += batch_success
                failures.extend(batch_failures)
                batch = []
    finally:
        text_stream.detach()

    if batch:
        batch_success, batch_failures = _flush_batch(es_client, batch, target_index)
        success_count += batch_success
        failures.extend(batch_failures)

    return {
        "index_name": target_index,
        "batch_size": batch_size,
        "success": success_count,
        "failures": failures,
    }
