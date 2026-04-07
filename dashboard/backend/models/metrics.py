"""
性能指标模型
"""
from sqlalchemy import Column, String, Float, Integer, TIMESTAMP, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Metric(Base):
    """性能指标表"""
    __tablename__ = "metrics"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='指标ID')
    agent_id = Column(String(64), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, comment='Agent ID')
    timestamp = Column(TIMESTAMP(3), server_default=func.now(), comment='采集时间')
    cpu_usage = Column(Float, comment='CPU使用率（%）')
    memory_usage = Column(Float, comment='内存使用（MB）')
    active_sessions = Column(Integer, default=0, comment='活跃会话数')
    messages_per_minute = Column(Integer, default=0, comment='每分钟消息数')
    avg_response_time = Column(Float, comment='平均响应时间（秒）')
    
    # 关系
    agent = relationship("Agent", back_populates="metrics")
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "active_sessions": self.active_sessions,
            "messages_per_minute": self.messages_per_minute,
            "avg_response_time": self.avg_response_time,
        }