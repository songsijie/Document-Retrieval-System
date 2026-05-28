from __future__ import annotations

import csv
import io
import random
from datetime import datetime
from typing import Any

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


def build_csv_template(count: int) -> str:
    """生成符合笔试题格式的 CSV 模板文本，authors 使用分号分隔。"""
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(CSV_HEADER)
    for article in generate_articles(count):
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
