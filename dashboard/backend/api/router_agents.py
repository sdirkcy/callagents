"""
配置管理 API 路由
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel

from database import get_async_db
from models.agent import Agent, AgentType, AgentStatus

router = APIRouter(prefix="/api/agents", tags=["Agent管理"])


# Pydantic 模型
class AgentConfig(BaseModel):
    """Agent配置模型"""
    name: str
    description: str = ""
    agent_type: str = "voice"
    
    # LiveKit配置
    livekit_url: str
    livekit_api_key: str
    livekit_api_secret: str
    
    # 模型配置
    stt_config: dict = {}
    llm_config: dict = {}
    tts_config: dict = {}
    vad_config: dict = {}
    
    # Agent行为配置
    instructions: str = ""
    max_tool_steps: int = 5
    allow_interruptions: bool = True


class AgentResponse(BaseModel):
    """Agent响应模型"""
    id: str
    name: str
    description: str
    agent_type: str
    status: str
    created_at: str
    updated_at: str
    is_active: bool


@router.get("/list", response_model=List[AgentResponse])
async def list_agents(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db)
):
    """获取Agent列表"""
    query = select(Agent).where(Agent.is_active == True).offset(skip).limit(limit)
    result = await db.execute(query)
    agents = result.scalars().all()
    return [agent.to_dict() for agent in agents]


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """获取单个Agent详情"""
    query = select(Agent).where(Agent.id == agent_id)
    result = await db.execute(query)
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent未找到")
    
    return agent.to_dict()


@router.post("/create", response_model=AgentResponse)
async def create_agent(
    config: AgentConfig,
    db: AsyncSession = Depends(get_async_db)
):
    """创建Agent配置"""
    import uuid
    
    agent = Agent(
        id=str(uuid.uuid4()),
        name=config.name,
        description=config.description,
        agent_type=AgentType(config.agent_type),
        livekit_url=config.livekit_url,
        livekit_api_key=config.livekit_api_key,
        livekit_api_secret=config.livekit_api_secret,
        stt_config=config.stt_config,
        llm_config=config.llm_config,
        tts_config=config.tts_config,
        vad_config=config.vad_config,
        instructions=config.instructions,
        max_tool_steps=config.max_tool_steps,
        allow_interruptions=config.allow_interruptions,
        status=AgentStatus.IDLE,
    )
    
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    
    return agent.to_dict()


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    config: AgentConfig,
    db: AsyncSession = Depends(get_async_db)
):
    """更新Agent配置"""
    query = select(Agent).where(Agent.id == agent_id)
    result = await db.execute(query)
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent未找到")
    
    # 更新字段
    agent.name = config.name
    agent.description = config.description
    agent.agent_type = AgentType(config.agent_type)
    agent.livekit_url = config.livekit_url
    agent.livekit_api_key = config.livekit_api_key
    agent.livekit_api_secret = config.livekit_api_secret
    agent.stt_config = config.stt_config
    agent.llm_config = config.llm_config
    agent.tts_config = config.tts_config
    agent.vad_config = config.vad_config
    agent.instructions = config.instructions
    agent.max_tool_steps = config.max_tool_steps
    agent.allow_interruptions = config.allow_interruptions
    
    await db.commit()
    await db.refresh(agent)
    
    return agent.to_dict()


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """删除Agent（软删除）"""
    query = select(Agent).where(Agent.id == agent_id)
    result = await db.execute(query)
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent未找到")
    
    # 软删除
    agent.is_active = False
    await db.commit()
    
    return {"message": "Agent已删除"}