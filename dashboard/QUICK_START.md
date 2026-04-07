# LiveKit Dashboard 快速启动指南

## 🚀 快速启动步骤

### 方式一：使用 Python 启动（推荐用于开发）

#### 1. 初始化 MySQL 数据库

```bash
# 方式A: 使用 Docker MySQL
docker-compose up -d mysql

# 等待 MySQL 完全启动（约30秒）
docker-compose logs -f mysql

# 方式B: 使用本地 MySQL
mysql -u root -p < dashboard/scripts/init-mysql.sql
```

#### 2. 配置后端环境变量

```bash
cd dashboard/backend
cp .env.example .env

# 编辑 .env 文件，确保 MySQL 配置正确：
# MYSQL_HOST=localhost
# MYSQL_PORT=3306
# MYSQL_USER=livekit
# MYSQL_PASSWORD=livekit_password
# MYSQL_DATABASE=livekit_dashboard
```

#### 3. 安装 Python 依赖

```bash
# 在项目根目录
cd D:\Github\callagents\dashboard\backend
pip install -r requirements.txt
```

#### 4. 启动后端服务

```bash
# 使用启动脚本
cd D:\Github\callagents\dashboard
python scripts/start_dashboard.py

# 或直接运行
cd D:\Github\callagents\dashboard\backend
python main.py

# 或使用 uvicorn
cd D:\Github\callagents\dashboard\backend
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

后端将启动在: http://localhost:8080  
API 文档: http://localhost:8080/api/docs

#### 5. 安装前端依赖并启动

```bash
cd D:\Github\callagents\dashboard\frontend
npm install
npm run dev
```

前端将启动在: http://localhost:5173

### 方式二：使用 Docker Compose（推荐用于生产）

```bash
# 一键启动所有服务
cd D:\Github\callagents\dashboard
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

服务:
- MySQL: localhost:3306
- 后端: http://localhost:8080
- 前端: http://localhost (需要配置nginx)

## 📋 验证安装

### 1. 验证 MySQL 连接

```bash
# 连接到 MySQL
mysql -u livekit -plivekit_password -h localhost livekit_dashboard

# 查看表
SHOW TABLES;

# 退出
EXIT;
```

### 2. 验证后端 API

```bash
# 健康检查
curl http://localhost:8080/health

# 查看 API 文档
# 浏览器打开: http://localhost:8080/api/docs
```

### 3. 验证前端

```bash
# 浏览器打开
http://localhost:5173
```

## ⚙️ 配置说明

### 数据库配置

默认配置:
- 主机: localhost
- 端口: 3306
- 用户: livekit
- 密码: livekit_password
- 数据库: livekit_dashboard

修改配置: 编辑 `dashboard/backend/.env`

### LiveKit 配置

编辑 `dashboard/backend/.env`:

```env
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
```

## 🐛 故障排查

### MySQL 连接失败

```bash
# 检查 MySQL 是否运行
docker ps | grep mysql

# 查看 MySQL 日志
docker logs livekit-mysql

# 重启 MySQL
docker-compose restart mysql
```

### 后端启动失败

```bash
# 检查端口占用
netstat -ano | findstr :8080

# 查看详细错误
cd D:\Github\callagents\dashboard\backend
python -m uvicorn main:app --reload --log-level debug
```

### 前端启动失败

```bash
# 清除缓存
cd D:\Github\callagents\dashboard\frontend
rm -rf node_modules
npm install

# 检查端口占用
netstat -ano | findstr :5173
```

## 📚 下一步

1. ✅ 基础设施已搭建完成
2. 🚧 完成Agent配置向导（Step 2-5）
3. 🚧 实现日志查看功能
4. 🚧 添加实时监控功能
5. 🚧 完善错误处理和用户引导

## 🎯 功能状态

| 功能 | 状态 | 说明 |
|------|------|------|
| 后端框架 | ✅ 完成 | FastAPI + SQLAlchemy |
| 数据库设计 | ✅ 完成 | MySQL 8.0+ |
| 前端框架 | ✅ 完成 | Vue 3 + Element Plus |
| Agent CRUD API | ✅ 完成 | 基础API已实现 |
| 配置向导 | 🚧 进行中 | Step 1 完成 |
| 日志查看 | 🚧 待开始 | - |
| 实时监控 | 🚧 待开始 | - |

## 📝 开发计划

### 阶段 1: 基础设施 ✅ (已完成)
- 创建项目结构
- 配置FastAPI后端
- 设计MySQL数据库
- 搭建Vue 3前端框架

### 阶段 2: 配置管理 (进行中)
- ✅ Step 1: 基础信息
- 🚧 Step 2: LiveKit连接
- 🚧 Step 3: 模型配置
- 🚧 Step 4: 高级设置
- 🚧 Step 5: 确认创建

### 阶段 3: Agent管理 (待开始)
- Agent启动/停止/重启
- 实时状态监控
- 进程管理

### 阶段 4: 日志系统 (待开始)
- 实时日志查看
- 日志搜索和过滤
- 错误诊断

### 阶段 5: 监控仪表盘 (待开始)
- Agent运行状态
- 性能指标图表
- 会话统计

---

有问题？请查看 [README.md](./README.md) 或提交 Issue！