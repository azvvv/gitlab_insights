from pydantic import BaseModel, Field
from typing import Optional

class TagCreateDTO(BaseModel):
    tag_name: str = Field(..., description="Tag名称")
    repository_id: int = Field(..., description="仓库ID（GitlabRepository.id）")
    branch: str = Field(..., description="分支名")
    user: Optional[str] = Field(None, description="操作人")
    description: Optional[str] = Field(None, description="备注")
