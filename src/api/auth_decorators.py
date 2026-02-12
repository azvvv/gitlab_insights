"""
认证装饰器 - 桥接到 shared 模块

重构说明：
- 直接使用 shared.auth_middleware 的装饰器
- 通过 response_formatter 参数适配 api_response 格式
- 所有现有路由无需修改
- 代码量大幅减少
"""

from shared.auth_middleware import token_required as shared_token_required
from shared.auth_middleware import admin_required as shared_admin_required
from api.response import api_response


# 使用 shared 模块的装饰器，传入 api_response 作为响应格式化器
token_required = shared_token_required(response_formatter=api_response)
admin_required = shared_admin_required(response_formatter=api_response)


# 为了完全向后兼容，也可以导出原始装饰器供需要的场景使用
__all__ = ['token_required', 'admin_required']
