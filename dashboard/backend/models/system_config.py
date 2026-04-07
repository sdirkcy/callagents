"""
系统配置模型
"""
from sqlalchemy import Column, String, Text, TIMESTAMP
from sqlalchemy.sql import func
from database import Base


class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = "system_config"
    
    config_key = Column(String(64), primary_key=True, comment='配置键')
    config_value = Column(Text, comment='配置值')
    description = Column(String(256), comment='配置说明')
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment='更新时间')
    
    def to_dict(self):
        """转换为字典"""
        return {
            "config_key": self.config_key,
            "config_value": self.config_value,
            "description": self.description,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }