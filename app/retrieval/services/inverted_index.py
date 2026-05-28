from __future__ import annotations

import re
from collections import defaultdict


class InvertedIndex:
    """内存倒排索引：维护 term 到 posting list 的映射。"""

    def __init__(self) -> None:
        """初始化正排文档、倒排表和 tombstone 集合。"""
        self.documents: dict[int, set[str]] = {}
        self.index: dict[str, set[int]] = defaultdict(set)
        self.deleted: set[int] = set()

    @staticmethod
    def tokenize(text: str) -> set[str]:
        """按非字母数字切分文本，并统一转为小写。"""
        # 简单分词：按非字母数字切分，并统一转为小写。
        return {term.lower() for term in re.split(r"[^a-zA-Z0-9]+", text) if term}

    def add(self, doc_id: int, text: str) -> None:
        """添加或覆盖文档，覆盖时清理旧倒排记录。"""
        # 覆盖已有文档时，先从旧 posting list 中移除 doc_id。
        if doc_id in self.documents:
            for term in self.documents[doc_id]:
                self.index[term].discard(doc_id)
                if not self.index[term]:
                    del self.index[term]

        terms = self.tokenize(text)
        self.documents[doc_id] = terms
        # 重新添加文档时清除 tombstone。
        self.deleted.discard(doc_id)

        for term in terms:
            self.index[term].add(doc_id)

    def search(self, term: str) -> list[int]:
        """查询单个 term 的 posting list，并跳过已删除文档。"""
        # 查询单个 term 的 posting list，并过滤已删除文档。
        normalized = term.lower()
        return sorted(doc_id for doc_id in self.index.get(normalized, set()) if doc_id not in self.deleted)

    def search_and(self, term1: str, term2: str) -> list[int]:
        """使用两个 posting list 求交集，返回同时命中的文档。"""
        left = self.index.get(term1.lower(), set())
        right = self.index.get(term2.lower(), set())

        # 从较短 posting list 开始做交集，减少遍历次数。
        if len(left) > len(right):
            left, right = right, left

        return sorted(doc_id for doc_id in left if doc_id in right and doc_id not in self.deleted)

    def delete(self, doc_id: int) -> None:
        """通过 tombstone 软删除文档，不立即清理倒排表。"""
        if doc_id in self.documents:
            # tombstone 删除：保留索引结构，只在查询时排除该文档。
            self.deleted.add(doc_id)
