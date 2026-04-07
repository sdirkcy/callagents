#!/usr/bin/env python3
"""
LiveKit Dashboard 启动脚本
用于启动后端服务
"""
import os
import sys
import subprocess
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

def check_dependencies():
    """检查依赖是否安装"""
    print("检查Python依赖...")
    
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import aiomysql
        print("✓ Python依赖已安装")
        return True
    except ImportError as e:
        print(f"✗ 缺少依赖: {e}")
        print("\n请运行以下命令安装依赖:")
        print("  pip install -r dashboard/backend/requirements.txt")
        return False

def check_mysql():
    """检查MySQL连接"""
    print("\n检查MySQL连接...")
    
    try:
        from sqlalchemy import create_engine
        from config import settings
        
        engine = create_engine(settings.SYNC_DATABASE_URL)
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        print("✓ MySQL连接成功")
        return True
    except Exception as e:
        print(f"✗ MySQL连接失败: {e}")
        print("\n请确保:")
        print("  1. MySQL服务正在运行")
        print("  2. 数据库 'livekit_dashboard' 已创建")
        print("  3. 用户权限已配置")
        print("\n运行以下命令初始化数据库:")
        print("  mysql -u root -p < dashboard/scripts/init-mysql.sql")
        return False

def init_database():
    """初始化数据库表"""
    print("\n初始化数据库表...")
    
    try:
        from database import sync_engine, Base
        from models import agent, session, logs, metrics, api_key, system_config
        
        Base.metadata.create_all(sync_engine)
        print("✓ 数据库表初始化完成")
        return True
    except Exception as e:
        print(f"✗ 数据库初始化失败: {e}")
        return False

def start_server():
    """启动服务器"""
    print("\n启动LiveKit Dashboard...")
    print(f"后端服务: http://localhost:8080")
    print(f"API文档: http://localhost:8080/api/docs")
    print("\n按 Ctrl+C 停止服务\n")
    
    os.chdir(backend_dir)
    
    # 使用uvicorn启动
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--host", "0.0.0.0",
        "--port", "8080",
        "--reload"
    ])

def main():
    """主函数"""
    print("=" * 60)
    print("  LiveKit Dashboard 启动脚本")
    print("=" * 60)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 检查MySQL
    if not check_mysql():
        print("\n尝试初始化数据库...")
        if not init_database():
            sys.exit(1)
    
    # 启动服务器
    start_server()

if __name__ == "__main__":
    main()