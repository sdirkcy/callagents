"""
数据库连接模块 - SQLAlchemy配置
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings

# 异步引擎（用于FastAPI异步操作）
async_engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.MYSQL_POOL_SIZE,
    max_overflow=settings.MYSQL_MAX_OVERFLOW,
    pool_recycle=settings.MYSQL_POOL_RECYCLE,
    pool_timeout=settings.MYSQL_POOL_TIMEOUT,
    echo=settings.DEBUG,
    pool_pre_ping=True,  # MySQL连接池优化：自动检测失效连接
)

# 同步引擎（用于启动脚本和后台任务）
sync_engine = create_engine(
    settings.SYNC_DATABASE_URL,
    pool_size=settings.MYSQL_POOL_SIZE,
    max_overflow=settings.MYSQL_MAX_OVERFLOW,
    pool_recycle=settings.MYSQL_POOL_RECYCLE,
    pool_timeout=settings.MYSQL_POOL_TIMEOUT,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

# 异步会话工厂
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 同步会话工厂
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

# 基础模型类
Base = declarative_base()


# 依赖注入：获取异步数据库会话
async def get_async_db():
    """获取异步数据库会话（用于FastAPI）"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# 依赖注入：获取同步数据库会话
def get_sync_db():
    """获取同步数据库会话（用于脚本和后台任务）"""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()