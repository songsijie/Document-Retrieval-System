from pydantic import BaseModel, Field


class GenerateArticlesResponse(BaseModel):
    success: int = Field(..., description="成功写入 ES 的文档数")
    index: str = Field(..., description="目标索引名")


class ClearIndexResponse(BaseModel):
    index: str = Field(..., description="清空的索引名")
    deleted: int = Field(..., description="删除的文档数")


class FlushIndicesResponse(BaseModel):
    deleted_indices: list[str] = Field(default_factory=list, description="已删除的索引名列表")
    count: int = Field(..., description="删除的索引数量")
    recreated_index: str = Field(..., description="flush 后重建的物理索引名")
    recreated_alias: str = Field(..., description="flush 后挂载的业务别名")


class IndexMappingBucket(BaseModel):
    index: str = Field(..., description="索引名")
    doc_count: int = Field(..., description="文档总数")
    aliases: list[str] = Field(default_factory=list, description="绑定的别名列表")
    mappings: dict = Field(default_factory=dict, description="索引 mapping 定义")


class ListIndicesMappingsResponse(BaseModel):
    indices: list[IndexMappingBucket] = Field(default_factory=list, description="各索引 mapping 概览")
    total_indices: int = Field(..., description="用户索引数量")


class ArticleRecord(BaseModel):
    pmid: int = Field(..., description="文献 PMID")
    pub_year: int = Field(..., description="发表年份")
    title: str = Field(..., description="标题")
    abstracts: str = Field(..., description="摘要")
    authors: list[str] = Field(default_factory=list, description="作者列表")
    pub_type: str = Field(..., description="文献类型")


class ArticleListResponse(BaseModel):
    total: int = Field(..., description="文献总数")
    page_size: int = Field(..., description="每页返回数量")
    scroll_id: str | None = Field(None, description="游标 ID，has_more 为 true 时用于拉取下一页")
    has_more: bool = Field(..., description="是否还有下一页数据")
    items: list[ArticleRecord] = Field(default_factory=list, description="当前页文献列表")
