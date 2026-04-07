"""
日志模型
"""
from sqlalchemy import Column, String, Text, Enum, JSON, TIMESTAMP, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


class LogLevel(enum.Enum):
    """日志级别枚举"""
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Log(Base):
    """日志表"""
    __tablename__ = "logs"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='日志ID')
    agent_id = Column(String(64), ForeignKey("agents.id", ondelete="SET NULL"), comment='Agent ID')
    session_id = Column(String(64), ForeignKey("sessions.id", ondelete="SET NULL"), comment='会话ID')
    timestamp = Column(TIMESTAMP(3), server_default=func.now(), comment='日志时间（毫秒精度）')
    level = Column(Enum(LogLevel), nullable=False, comment='日志级别')
    message = Column(Text, nullable=False, comment='日志内容')
    metadata = Column(JSON, comment='额外元数据')
    
    # 关系
    agent = relationship("Agent", back_populates="logs")
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "level": self.level.value if self.level else None,
            "message": self.message,
            "metadata": self.metadata,
        }