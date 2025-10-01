# 深思智聊平台 - Docker 部署指南

## 🚀 快速开始

### 1. 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- Linux/macOS/Windows (推荐 Linux)

### 2. 配置环境变量

复制并编辑环境变量文件：

```bash
cp .env.production .env.production.local
```

编辑 `.env.production.local` 文件，配置以下关键参数：

```bash
# DeepSeek API配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 数据库配置
MYSQL_ROOT_PASSWORD=your_secure_root_password
MYSQL_PASSWORD=your_secure_password

# 域名配置（生产环境）
DOMAIN_NAME=your-domain.com
SSL_EMAIL=your-email@example.com
```

### 3. 一键部署

```bash
# 给脚本执行权限
chmod +x deploy.sh

# 启动服务
./deploy.sh start
```

## 📋 部署命令

### 基本操作

```bash
# 启动所有服务
./deploy.sh start

# 停止所有服务
./deploy.sh stop

# 重启所有服务
./deploy.sh restart

# 查看服务状态
./deploy.sh status
```

### 日志管理

```bash
# 查看所有服务日志
./deploy.sh logs

# 查看特定服务日志
./deploy.sh logs backend
./deploy.sh logs frontend
./deploy.sh logs mysql
```

### 维护操作

```bash
# 更新服务
./deploy.sh update

# 备份数据
./deploy.sh backup

# 配置SSL证书
./deploy.sh ssl
```

## 🏗️ 架构说明

### 服务组件

- **Frontend**: Vue3 + Element Plus (端口: 80)
- **Backend**: FastAPI + Python (端口: 8000)
- **Database**: MySQL 8.0 (端口: 3306)
- **Cache**: Redis (端口: 6379)
- **Proxy**: Nginx (反向代理)

### 网络架构

```
Internet → Nginx (80/443) → Frontend (Vue3)
                         → Backend API (FastAPI)
                         → Database (MySQL)
                         → Cache (Redis)
```

## 🔧 配置说明

### Docker Compose 服务

| 服务名 | 描述 | 端口 | 依赖 |
|--------|------|------|------|
| mysql | MySQL 数据库 | 3306 | - |
| redis | Redis 缓存 | 6379 | - |
| backend | FastAPI 后端 | 8000 | mysql, redis |
| frontend | Vue3 前端 | 80 | backend |

### 数据持久化

- MySQL 数据: `./data/mysql`
- Redis 数据: `./data/redis`
- 应用日志: `./backend/logs`
- SSL 证书: `./deploy/ssl`

## 🔒 安全配置

### 生产环境建议

1. **修改默认密码**
   ```bash
   # 在 .env.production 中设置强密码
   MYSQL_ROOT_PASSWORD=your_very_secure_password
   MYSQL_PASSWORD=another_secure_password
   ```

2. **配置防火墙**
   ```bash
   # 只开放必要端口
   ufw allow 80
   ufw allow 443
   ufw enable
   ```

3. **SSL 证书**
   ```bash
   # 自动配置 Let's Encrypt 证书
   ./deploy.sh ssl
   ```

## 📊 监控和维护

### 健康检查

所有服务都配置了健康检查：

```bash
# 查看服务健康状态
docker-compose ps
```

### 日志轮转

日志文件会自动轮转，避免磁盘空间不足：

- 最大文件大小: 10MB
- 保留文件数: 3个

### 备份策略

```bash
# 定期备份数据库
./deploy.sh backup

# 设置定时任务
crontab -e
# 添加: 0 2 * * * /path/to/deploy.sh backup
```

## 🐛 故障排除

### 常见问题

1. **端口冲突**
   ```bash
   # 检查端口占用
   netstat -tlnp | grep :80
   
   # 修改 docker-compose.yml 中的端口映射
   ```

2. **内存不足**
   ```bash
   # 检查系统资源
   docker stats
   
   # 清理未使用的镜像
   docker system prune -f
   ```

3. **数据库连接失败**
   ```bash
   # 检查数据库日志
   ./deploy.sh logs mysql
   
   # 重启数据库服务
   docker-compose restart mysql
   ```

### 调试模式

```bash
# 以调试模式启动
DEBUG=true ./deploy.sh start

# 查看详细日志
./deploy.sh logs -f
```

## 🔄 更新和升级

### 应用更新

```bash
# 拉取最新代码并重新部署
./deploy.sh update
```

### 数据库迁移

```bash
# 备份数据
./deploy.sh backup

# 执行迁移
docker-compose exec backend python -m alembic upgrade head
```

## 📞 技术支持

如遇到问题，请检查：

1. Docker 和 Docker Compose 版本
2. 系统资源使用情况
3. 网络连接状态
4. 环境变量配置

更多帮助信息：

```bash
./deploy.sh help
```