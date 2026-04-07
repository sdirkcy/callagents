"""
会话模型
"""
from sqlalchemy import Column, String, Integer, Float, Enum, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


class SessionStatus(enum.Enum):
    """会话状态枚举"""
    ACTIVE = "active"
    COMPLETED = "completed"
    ERROR = "error"


class Session(Base):
    """会话记录表"""
    __tablename__ = "sessions"
    
    id = Column(String(64), primary_key=True, comment='会话ID')
    agent_id = Column(String(64), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, comment='Agent ID')
    room_name = Column(String(128), comment='房间名称')
    participant_identity = Column(String(128), comment='参与者身份')
    started_at = Column(TIMESTAMP, server_default=func.now(), comment='开始时间')
    ended_at = Column(TIMESTAMP, comment='结束时间')
    status = Column(Enum(SessionStatus), default=SessionStatus.ACTIVE, comment='会话状态')
    
    # 会话统计
    user_messages = Column(Integer, default=0, comment='用户消息数')
    agent_messages = Column(Integer, default=0, comment='Agent消息数')
    total_duration = Column(Float, default=0, comment='总时长（秒）')
    
    # 关系
    agent = relationship("Agent", back_populates="sessions")
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "room_name": self.room_name,
            "participant_identity": self.participant_identity,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "status": self.status.value if self.status else None,
            "user_messages": self.user_messages,
            "agent_messages": self.agent_messages,
            "total_duration": self.total_duration,
        }