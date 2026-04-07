"""
Agent配置模型
"""
from sqlalchemy import Column, String, Text, Integer, Boolean, Enum, JSON, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


class AgentType(enum.Enum):
    """Agent类型枚举"""
    VOICE = "voice"
    VIDEO = "video"
    TEXT = "text"


class AgentStatus(enum.Enum):
    """Agent状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"


class Agent(Base):
    """Agent配置表"""
    __tablename__ = "agents"
    
    id = Column(String(64), primary_key=True, comment='Agent唯一ID')
    name = Column(String(100), nullable=False, comment='Agent名称')
    description = Column(Text, comment='Agent描述')
    agent_type = Column(Enum(AgentType), default=AgentType.VOICE, comment='Agent类型')
    
    # LiveKit配置
    livekit_url = Column(String(512), comment='LiveKit服务器URL')
    livekit_api_key = Column(String(128), comment='LiveKit API密钥')
    livekit_api_secret = Column(String(256), comment='LiveKit API密文')
    
    # 模型配置（JSON）
    stt_config = Column(JSON, comment='STT模型配置')
    llm_config = Column(JSON, comment='LLM模型配置')
    tts_config = Column(JSON, comment='TTS模型配置')
    vad_config = Column(JSON, comment='VAD模型配置')
    
    # 高级配置
    instructions = Column(Text, comment='Agent指令')
    max_tool_steps = Column(Integer, default=5, comment='最大工具调用步数')
    allow_interruptions = Column(Boolean, default=True, comment='是否允许打断')
    
    # 运行状态
    status = Column(Enum(AgentStatus), default=AgentStatus.IDLE, comment='运行状态')
    pid = Column(Integer, comment='进程ID')
    
    # 元数据
    created_at = Column(TIMESTAMP, server_default=func.now(), comment='创建时间')
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment='更新时间')
    created_by = Column(String(64), default="user", comment='创建者')
    is_active = Column(Boolean, default=True, comment='是否启用')
    
    # 关系
    sessions = relationship("Session", back_populates="agent", cascade="all, delete-orphan")
    logs = relationship("Log", back_populates="agent")
    metrics = relationship("Metric", back_populates="agent", cascade="all, delete-orphan")
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "agent_type": self.agent_type.value if self.agent_type else None,
            "livekit_url": self.livekit_url,
            "status": self.status.value if self.status else None,
            "pid": self.pid,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active,
        }