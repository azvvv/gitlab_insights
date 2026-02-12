"""
首页链接配置服务
"""
from typing import List, Optional, Dict
from datetime import datetime
from database.connection import get_db_session
from database.models import HomeLink
from dto.home_link_dto import (
    HomeLinkCreate, 
    HomeLinkUpdate, 
    HomeLinkResponse,
    HomeLinkGroupResponse,
    HomeLinksResponse
)


class HomeLinkService:
    """首页链接服务"""
    
    # 分组标题映射
    GROUP_TITLES = {
        'devops': 'DevOps 平台',
        'jira': 'Jira 项目管理',
        'ai': 'AI 开发平台',
        'monitoring': '平台监控'
    }
    
    def __init__(self):
        pass
    
    def get_all_links(self, include_inactive: bool = False) -> HomeLinksResponse:
        """
        获取所有首页链接（按分类和分组组织）
        
        Args:
            include_inactive (bool): 是否包含未激活的记录，默认为False
        
        Returns:
            HomeLinksResponse: 包含文档链接和平台链接的响应对象
        """
        with get_db_session() as db:
            # 查询链接，按排序顺序
            query = db.query(HomeLink)
            
            # 如果不包含未激活记录，则只查询启用的链接
            if not include_inactive:
                query = query.filter(HomeLink.is_active == True)
            
            links = query.order_by(
                HomeLink.category,
                HomeLink.group_name,
                HomeLink.sort_order
            ).all()
            
            # 按分类分组
            doc_links_dict: Dict[str, List[HomeLink]] = {}
            platform_links: List[HomeLink] = []
            
            for link in links:
                if link.category == 'doc_links':
                    if link.group_name not in doc_links_dict:
                        doc_links_dict[link.group_name] = []
                    doc_links_dict[link.group_name].append(link)
                elif link.category == 'platform_links':
                    platform_links.append(link)
            
            # 转换为响应格式
            doc_link_groups = [
                HomeLinkGroupResponse(
                    group_name=group_name,
                    group_title=group_name,  # 直接使用数据库原始值，不再转换
                    links=[self._to_response(link) for link in group_links]
                )
                for group_name, group_links in doc_links_dict.items()
            ]
            
            platform_link_responses = [
                self._to_response(link) for link in platform_links
            ]
            
            return HomeLinksResponse(
                doc_links=doc_link_groups,
                platform_links=platform_link_responses
            )
    
    def get_links_by_category(self, category: str) -> List[HomeLinkResponse]:
        """
        按分类获取链接
        
        Args:
            category: 分类名称 (doc_links/platform_links)
            
        Returns:
            List[HomeLinkResponse]: 链接列表
        """
        with get_db_session() as db:
            links = db.query(HomeLink).filter(
                HomeLink.category == category,
                HomeLink.is_active == True
            ).order_by(
                HomeLink.group_name,
                HomeLink.sort_order
            ).all()
            
            return [self._to_response(link) for link in links]
    
    def get_links_by_group(self, category: str, group_name: str) -> List[HomeLinkResponse]:
        """
        按分类和分组获取链接
        
        Args:
            category: 分类名称
            group_name: 分组名称
            
        Returns:
            List[HomeLinkResponse]: 链接列表
        """
        with get_db_session() as db:
            links = db.query(HomeLink).filter(
                HomeLink.category == category,
                HomeLink.group_name == group_name,
                HomeLink.is_active == True
            ).order_by(
                HomeLink.sort_order
            ).all()
            
            return [self._to_response(link) for link in links]
    
    def get_link_by_id(self, link_id: int) -> Optional[HomeLinkResponse]:
        """
        根据ID获取链接
        
        Args:
            link_id: 链接ID
            
        Returns:
            Optional[HomeLinkResponse]: 链接对象，不存在则返回None
        """
        with get_db_session() as db:
            link = db.query(HomeLink).filter(HomeLink.id == link_id).first()
            return self._to_response(link) if link else None
    
    def create_link(self, link_data: HomeLinkCreate) -> HomeLinkResponse:
        """
        创建新链接
        
        Args:
            link_data: 链接创建数据
            
        Returns:
            HomeLinkResponse: 创建的链接对象
        """
        with get_db_session() as db:
            new_link = HomeLink(
                category=link_data.category,
                group_name=link_data.group_name,
                title=link_data.title,
                description=link_data.description,
                url=link_data.url,
                icon=link_data.icon,
                color=link_data.color,
                ip=link_data.ip,
                port=link_data.port,
                sort_order=link_data.sort_order,
                is_active=link_data.is_active
            )
            
            db.add(new_link)
            db.commit()
            db.refresh(new_link)
            
            return self._to_response(new_link)
    
    def update_link(self, link_id: int, link_data: HomeLinkUpdate) -> Optional[HomeLinkResponse]:
        """
        更新链接
        
        Args:
            link_id: 链接ID
            link_data: 更新数据
            
        Returns:
            Optional[HomeLinkResponse]: 更新后的链接对象，不存在则返回None
        """
        with get_db_session() as db:
            link = db.query(HomeLink).filter(HomeLink.id == link_id).first()
            if not link:
                return None
            
            # 更新字段（只更新非None的字段）
            update_data = link_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(link, field, value)
            
            link.updated_at = datetime.now()
            
            db.commit()
            db.refresh(link)
            
            return self._to_response(link)
    
    def delete_link(self, link_id: int) -> bool:
        """
        删除链接
        
        Args:
            link_id: 链接ID
            
        Returns:
            bool: 删除成功返回True，链接不存在返回False
        """
        with get_db_session() as db:
            link = db.query(HomeLink).filter(HomeLink.id == link_id).first()
            if not link:
                return False
            
            db.delete(link)
            db.commit()
            
            return True
    
    def toggle_active(self, link_id: int) -> Optional[HomeLinkResponse]:
        """
        切换链接启用状态
        
        Args:
            link_id: 链接ID
            
        Returns:
            Optional[HomeLinkResponse]: 更新后的链接对象，不存在则返回None
        """
        with get_db_session() as db:
            link = db.query(HomeLink).filter(HomeLink.id == link_id).first()
            if not link:
                return None
            
            link.is_active = not link.is_active
            link.updated_at = datetime.now()
            
            db.commit()
            db.refresh(link)
            
            return self._to_response(link)
    
    def update_sort_orders(self, link_orders: List[Dict[str, int]]) -> bool:
        """
        批量更新排序顺序
        
        Args:
            link_orders: 链接ID和排序顺序的列表，例如: [{"id": 1, "sort_order": 0}, {"id": 2, "sort_order": 1}]
            
        Returns:
            bool: 更新成功返回True
        """
        with get_db_session() as db:
            try:
                for order_data in link_orders:
                    link_id = order_data.get('id')
                    sort_order = order_data.get('sort_order')
                    
                    if link_id is not None and sort_order is not None:
                        db.query(HomeLink).filter(HomeLink.id == link_id).update(
                            {'sort_order': sort_order, 'updated_at': datetime.now()}
                        )
                
                db.commit()
                return True
            except Exception:
                db.rollback()
                return False
    
    @staticmethod
    def _to_response(link: HomeLink) -> HomeLinkResponse:
        """
        将数据库模型转换为响应DTO
        
        Args:
            link: 数据库链接对象
            
        Returns:
            HomeLinkResponse: 响应DTO对象
        """
        return HomeLinkResponse(
            id=link.id,
            category=link.category,
            group_name=link.group_name,
            title=link.title,
            description=link.description,
            url=link.url,
            icon=link.icon,
            color=link.color,
            ip=link.ip,
            port=link.port,
            sort_order=link.sort_order,
            is_active=link.is_active,
            created_at=link.created_at.isoformat() if link.created_at else '',
            updated_at=link.updated_at.isoformat() if link.updated_at else ''
        )
