# LiveKit Dashboard - Web管理后台

这是一个基于 Vue 3 + Element Plus + FastAPI + MySQL 构建的 LiveKit Agents 管理后台，用于配置、管理和监控 AI Agent。

## 功能特性

### ✅ 已实现

- **基础架构搭建**
  - ✅ FastAPI 后端框架
  - ✅ Vue 3 + TypeScript 前端框架
  - ✅ MySQL 数据库配置
  - ✅ SQLAlchemy ORM 模型
  - ✅ Docker 部署配置

- **数据库设计**
  - ✅ Agent 配置表
  - ✅ 会话记录表
  - ✅ 日志表
  - ✅ 性能指标表
  - ✅ API 密钥表
  - ✅ 系统配置表

### 🚧 待实现

- **配置管理模块**
  - 配置向导（5步骤）
  - Agent 创建/编辑/删除
  - 配置模板管理

- **Agent 运行管理**
  - 启动/停止/重启 Agent
  - 实时状态监控
  - 进程管理

- **日志系统**
  - 实时日志查看
  - 日志搜索和过滤
  - 错误诊断

- **监控仪表盘**
  - Agent 运行状态
  - 性能指标图表
  - 会话统计

## 技术栈

### 后端
- **框架**: FastAPI 0.109
- **数据库**: MySQL 8.0+
- **ORM**: SQLAlchemy 2.0
- **异步**: aiomysql

### 前端
- **框架**: Vue 3.4
- **UI**: Element Plus 2.5
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **构建工具**: Vite 5

## 快速开始

### 前置要求

- Python 3.9+
- Node.js 18+
- MySQL 8.0+
- Docker & Docker Compose（可选）

### 1. 克隆项目

```bash
cd callagents/dashboard
```

### 2. 启动 MySQL 数据库

#### 方式 A: 使用 Docker Compose

```bash
docker-compose up -d mysql
```

#### 方式 B: 使用本地 MySQL

```bash
# 初始化数据库
mysql -u root -p < scripts/init-mysql.sql
```

### 3. 配置环境变量

```bash
# 后端配置
cd backend
cp .env.example .env
# 编辑 .env 文件，配置 MySQL 连接信息
```

### 4. 安装依赖

#### 后端依赖

```bash
cd backend
pip install -r requirements.txt
```

#### 前端依赖

```bash
cd frontend
npm install
```

### 5. 启动服务

#### 启动后端

```bash
# 在 dashboard 目录下
python scripts/start_dashboard.py

# 或者直接在 backend 目录下
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

后端服务将运行在: http://localhost:8080  
API 文档: http://localhost:8080/api/docs

#### 启动前端

```bash
cd frontend
npm run dev
```

前端服务将运行在: http://localhost:5173

### 6. 访问管理后台

打开浏览器访问: http://localhost:5173

## 项目结构

```
dashboard/
├── backend/                 # FastAPI 后端
│   ├── api/                # API 路由
│   ├── models/             # 数据库模型
│   ├── services/           # 业务逻辑
│   ├── utils/              # 工具函数
│   ├── main.py             # 应用入口
│   ├── config.py           # 配置文件
│   ├── database.py         # 数据库连接
│   └── requirements.txt    # Python 依赖
│
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── components/     # Vue 组件
│   │   ├── views/          # 页面视图
│   │   ├── api/            # API 封装
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── router/         # Vue Router 路由
│   │   ├── composables/    # 组合式函数
│   │   ├── App.vue         # 根组件
│   │   └── main.ts         # 入口文件
│   ├── package.json        # Node 依赖
│   ├── vite.config.ts      # Vite 配置
│   └── tsconfig.json       # TypeScript 配置
│
├── scripts/                # 工具脚本
│   ├── init-mysql.sql      # MySQL 初始化脚本
│   └── start_dashboard.py  # 启动脚本
│
├── data/                   # 数据目录
│   ├── logs/              # 日志文件
│   └── configs/           # 配置文件
│
└── docker-compose.yml      # Docker Compose 配置
```

## 数据库配置

### MySQL 连接参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| MYSQL_HOST | localhost | MySQL 服务器地址 |
| MYSQL_PORT | 3306 | MySQL 端口 |
| MYSQL_USER | livekit | 数据库用户名 |
| MYSQL_PASSWORD | livekit_password | 数据库密码 |
| MYSQL_DATABASE | livekit_dashboard | 数据库名称 |

### 数据库表结构

- **agents**: Agent 配置信息
- **sessions**: 会话记录
- **logs**: 运行日志
- **metrics**: 性能指标
- **api_keys**: API 密钥管理
- **system_config**: 系统配置

## API 文档

启动后端服务后，访问以下地址查看 API 文档：

- Swagger UI: http://localhost:8080/api/docs
- ReDoc: http://localhost:8080/api/redoc

## 开发指南

### 添加新的 API 路由

1. 在 `backend/api/` 目录下创建新的路由文件
2. 在 `backend/main.py` 中导入并注册路由

### 添加新的数据模型

1. 在 `backend/models/` 目录下创建新的模型文件
2. 在 `backend/models/__init__.py` 中导出模型
3. 运行数据库迁移（使用 Alembic）

### 添加新的前端页面

1. 在 `frontend/src/views/` 目录下创建 Vue 组件
2. 在 `frontend/src/router/index.ts` 中添加路由配置

## 环境变量

创建 `backend/.env` 文件：

```env
# 应用配置
APP_NAME=LiveKit Dashboard
DEBUG=False

# MySQL配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=livekit
MYSQL_PASSWORD=livekit_password
MYSQL_DATABASE=livekit_dashboard

# LiveKit配置
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# JWT配置
JWT_SECRET=change-this-to-a-random-secret-key-in-production
```

## 故障排查

### MySQL 连接失败

```bash
# 检查 MySQL 服务状态
docker ps | grep mysql

# 查看 MySQL 日志
docker logs livekit-mysql

# 重新初始化数据库
mysql -u root -p < scripts/init-mysql.sql
```

### 后端启动失败

```bash
# 检查依赖是否安装
pip install -r backend/requirements.txt

# 检查配置文件
cat backend/.env

# 查看详细日志
cd backend
python -m uvicorn main:app --reload --log-level debug
```

### 前端启动失败

```bash
# 清除依赖缓存
rm -rf frontend/node_modules
rm frontend/package-lock.json

# 重新安装
cd frontend
npm install
```

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

Apache License 2.0