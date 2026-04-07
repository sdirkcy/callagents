"""
系统配置 API 路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel

from database import get_async_db
from models.system_config import SystemConfig

router = APIRouter(prefix="/api/system", tags=["系统配置"])


class ConfigItem(BaseModel):
    """配置项模型"""
    config_key: str
    config_value: str
    description: str = ""


@router.get("/config", response_model=List[ConfigItem])
async def get_config(
    db: AsyncSession = Depends(get_async_db)
):
    """获取系统配置"""
    query = select(SystemConfig)
    result = await db.execute(query)
    configs = result.scalars().all()
    return [config.to_dict() for config in configs]


@router.put("/config/{config_key}")
async def update_config(
    config_key: str,
    config_value: str,
    db: AsyncSession = Depends(get_async_db)
):
    """更新系统配置"""
    query = select(SystemConfig).where(SystemConfig.config_key == config_key)
    result = await db.execute(query)
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="配置项未找到")
    
    config.config_value = config_value
    await db.commit()
    
    return {"message": "配置更新成功"}


@router.get("/status")
async def get_system_status():
    """获取系统状态"""
    return {
        "status": "running",
        "version": "1.0.0",
        "services": {
            "database": "connected",
            "backend": "running"
        }
    }