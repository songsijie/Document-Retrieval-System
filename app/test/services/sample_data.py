from __future__ import annotations

import csv
import io
import random
from datetime import datetime
from typing import Any

from elasticsearch import Elasticsearch, helpers

from settings import ES_INDEX

CSV_HEADER = ["pmid", "pub_year", "title", "abstracts", "authors", "pub_type"]
PUB_TYPES = ["Journal Article", "Review", "Clinical Trial", "Meta-Analysis"]
AUTHOR_NAMES = ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace", "Henry"]
TITLE_PREFIXES = ["Study of", "Analysis of", "Effects of", "Role of", "Impact of"]
TITLE_SUBJECTS = ["cancer", "diabetes", "heart disease", "immunotherapy", "gene therapy", "inflammation"]


def generate_article(pmid: int) -> dict[str, Any]:
    """生成一条符合笔试题格式的随机文献数据。"""
    current_year = datetime.now().year
    title = f"{random.choice(TITLE_PREFIXES)} {random.choice(TITLE_SUBJECTS)} in clinical research"
    return {
        "pmid": pmid,
        "pub_year": random.randint(current_year - 5, current_year),
        "title": title,
        "abstracts": f"This article discusses {title.lower()} with relevant findings.",
        "authors": random.sample(AUTHOR_NAMES, k=random.randint(1, 3)),
        "pub_type": random.choice(PUB_TYPES),
    }


def generate_articles(count: int, start_pmid: int | None = None) -> list[dict[str, Any]]:
    """批量生成随机文献数据。"""
    if count <= 0:
        return []

    base_pmid = start_pmid if start_pmid is not None else random.randint(10_000_000, 90_000_000)
    return [generate_article(base_pmid + index) for index in range(count)]


def articles_to_csv(articles: list[dict[str, Any]]) -> str:
    """将文献数据转换为 CSV 文本，authors 使用分号分隔。"""
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(CSV_HEADER)
    for article in articles:
        writer.writerow(
            [
                article["pmid"],
                article["pub_year"],
                article["title"],
                article["abstracts"],
                ";".join(article["authors"]),
                article["pub_type"],
            ]
        )
    return output.getvalue()


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
