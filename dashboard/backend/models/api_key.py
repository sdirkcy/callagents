"""
API密钥模型
"""
from sqlalchemy import Column, String, Boolean, TIMESTAMP, BigInteger
from sqlalchemy.sql import func
from database import Base


class APIKey(Base):
    """API密钥表"""
    __tablename__ = "api_keys"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='密钥ID')
    service_name = Column(String(64), nullable=False, comment='服务名称')
    api_key = Column(String(512), nullable=False, comment='API密钥（加密存储）')
    api_endpoint = Column(String(512), comment='API端点')
    is_valid = Column(Boolean, default=True, comment='是否有效')
    last_tested_at = Column(TIMESTAMP, comment='最后测试时间')
    created_at = Column(TIMESTAMP, server_default=func.now(), comment='创建时间')
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment='更新时间')
    
    def to_dict(self):
        """转换为字典（不包含密钥）"""
        return {
            "id": self.id,
            "service_name": self.service_name,
            "api_endpoint": self.api_endpoint,
            "is_valid": self.is_valid,
            "last_tested_at": self.last_tested_at.isoformat() if self.last_tested_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }