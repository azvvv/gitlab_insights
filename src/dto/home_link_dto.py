"""
首页链接配置 DTO
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class HomeLinkBase(BaseModel):
    """首页链接基础模型"""
    category: str = Field(..., description="分类：doc_links(文档链接) 或 platform_links(平台链接)")
    group_name: str = Field(..., description="分组名称：devops, jira, ai, monitoring等")
    title: str = Field(..., description="链接标题")
    description: Optional[str] = Field(None, description="链接描述")
    url: str = Field(..., description="链接地址")
    icon: Optional[str] = Field(None, description="图标名称")
    color: Optional[str] = Field(None, description="颜色（渐变色CSS）")
    ip: Optional[str] = Field(None, description="平台IP地址")
    port: Optional[str] = Field(None, description="平台端口")
    sort_order: int = Field(0, description="排序顺序")
    is_active: bool = Field(True, description="是否启用")


class HomeLinkCreate(HomeLinkBase):
    """创建首页链接"""
    pass


class HomeLinkUpdate(BaseModel):
    """更新首页链接"""
    category: Optional[str] = None
    group_name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    ip: Optional[str] = None
    port: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class HomeLinkResponse(HomeLinkBase):
    """首页链接响应"""
    id: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class HomeLinkGroupResponse(BaseModel):
    """分组链接响应"""
    group_name: str
    group_title: str
    links: List[HomeLinkResponse]


class HomeLinksResponse(BaseModel):
    """首页所有链接响应"""
    doc_links: List[HomeLinkGroupResponse] = Field(default_factory=list, description="文档链接分组")
    platform_links: List[HomeLinkResponse] = Field(default_factory=list, description="平台监控链接")
