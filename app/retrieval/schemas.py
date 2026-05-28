from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ArticleHit(BaseModel):
    """ES 单条检索结果。"""

    score: float | None = Field(None, description="ES 相关度评分")
    source: dict[str, Any] = Field(default_factory=dict, description="文献原始字段")


class ArticleSearchResponse(BaseModel):
    """ES 全文检索和多条件过滤响应。"""

    total: int = Field(..., description="命中文档总数")
    page_size: int = Field(..., description="每页返回数量")
    scroll_id: str | None = Field(None, description="游标 ID，has_more 为 true 时用于拉取下一页")
    has_more: bool = Field(..., description="是否还有下一页数据")
    items: list[ArticleHit] = Field(default_factory=list, description="当前页文献列表")


class YearAggregationItem(BaseModel):
    """按年份聚合的单个桶。"""

    year: int = Field(..., description="发表年份")
    count: int = Field(..., description="该年份命中数量")


class InvertedIndexDocumentRequest(BaseModel):
    """写入内存倒排索引的文档。"""

    doc_id: int = Field(..., description="文档 ID")
    text: str = Field(..., description="待分词文本")


class InvertedIndexWriteResponse(BaseModel):
    """倒排索引写入或删除响应。"""

    doc_id: int = Field(..., description="文档 ID")
    status: Literal["indexed", "deleted"] = Field(..., description="操作状态")


class InvertedIndexSearchResponse(BaseModel):
    """倒排索引单词查询响应。"""

    term: str = Field(..., description="查询 term")
    doc_ids: list[int] = Field(default_factory=list, description="命中的文档 ID 列表")


class InvertedIndexSearchAndResponse(BaseModel):
    """倒排索引 AND 查询响应。"""

    terms: list[str] = Field(..., description="参与 AND 查询的两个 term")
    doc_ids: list[int] = Field(default_factory=list, description="同时命中的文档 ID 列表")


class CsvLoadFailure(BaseModel):
    """CSV 单行或 bulk 写入失败明细。"""

    line_number: int | None = Field(None, description="CSV 行号")
    id: str | None = Field(None, description="失败文档 ID")
    reason: Any = Field(..., description="失败原因")


class CsvLoadResponse(BaseModel):
    """CSV 导入响应。"""

    index_name: str = Field(..., description="实际写入的 ES 索引名")
    batch_size: int = Field(..., description="bulk 每批写入数量")
    success: int = Field(..., description="成功写入数量")
    failures: list[CsvLoadFailure] = Field(default_factory=list, description="失败明细")


class MigrationRequest(BaseModel):
    """pub_type keyword 迁移请求。"""

    old_index: str = Field(..., description="旧索引名")
    new_index: str = Field(..., description="新索引名")
    alias_name: str = Field(..., description="需要切换的 alias 名称")


class MigrationResponse(BaseModel):
    """mapping 迁移响应。"""

    migrated_count: int = Field(..., description="迁移文档数量")
