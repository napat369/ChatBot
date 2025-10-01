# 深思智聊平台 (DeepSmart Chat)

基于 DeepSeek API 的智能对话平台，采用 Vue3 + FastAPI + Docker 架构。

## ✨ 功能特性

- 🤖 **智能对话**：集成 DeepSeek API，支持多轮对话
- 💬 **会话管理**：支持创建、删除、重命名会话
- 📱 **响应式设计**：适配桌面端和移动端
- 🔄 **实时交互**：流式响应，实时显示AI回复
- 📊 **数据持久化**：MySQL数据库存储对话历史
- 🐳 **容器化部署**：Docker一键部署，环境一致性
- 🔒 **安全可靠**：SSL证书支持，生产级配置

## 🏗️ 技术架构

### 前端技术栈
- **Vue 3** - 渐进式JavaScript框架
- **Element Plus** - Vue 3组件库
- **Axios** - HTTP客户端
- **Vue Router** - 路由管理

### 后端技术栈
- **FastAPI** - 现代Python Web框架
- **SQLAlchemy** - ORM框架
- **MySQL** - 关系型数据库
- **Redis** - 缓存数据库
- **Uvicorn** - ASGI服务器

### 部署技术
- **Docker** - 容器化平台
- **Docker Compose** - 多容器编排
- **Nginx** - 反向代理服务器
- **Let's Encrypt** - SSL证书

## 🚀 快速开始

### 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- Git

### 1. 克隆项目

```bash
git clone https://github.com/your-username/deepsmart-chat.git
cd deepsmart-chat
```

### 2. 配置环境变量

```bash
cp .env.production .env.production.local
```

编辑 `.env.production.local` 文件：

```bash
# DeepSeek API配置
DEEPSEEK_API_KEY=sk-your-api-key-here

# 数据库配置
MYSQL_ROOT_PASSWORD=your_secure_password
MYSQL_PASSWORD=another_secure_password

# 域名配置（可选）
DOMAIN_NAME=your-domain.com
SSL_EMAIL=your-email@example.com
```

### 3. 启动服务

```bash
chmod +x deploy.sh
./deploy.sh start
```

### 4. 访问应用

- 本地访问：http://localhost
- 生产环境：https://your-domain.com

## 📋 管理命令

```bash
./deploy.sh start     # 启动所有服务
./deploy.sh stop      # 停止所有服务
./deploy.sh restart   # 重启所有服务
./deploy.sh logs      # 查看服务日志
./deploy.sh status    # 查看服务状态
./deploy.sh update    # 更新服务
./deploy.sh backup    # 备份数据
./deploy.sh ssl       # 配置SSL证书
```

## 🔧 开发环境

### 前端开发

```bash
cd frontend
npm install
npm run serve
```

### 后端开发

```bash
cd backend
pip install -r requirements.txt
python start.py
```

## 📦 部署指南

### 本地部署

```bash
# 使用Docker Compose
./deploy.sh start
```

### 服务器部署

```bash
# 自动化部署到Linux服务器
./deploy-to-server.sh 服务器IP 用户名

# 示例
./deploy-to-server.sh 192.168.1.100 ubuntu
```

详细部署说明请参考：[部署指南](部署指南.md)

## 📁 项目结构

```
deepsmart-chat/
├── backend/                 # 后端服务
│   ├── app/                # 应用代码
│   ├── Dockerfile          # 后端Docker配置
│   └── requirements.txt    # Python依赖
├── frontend/               # 前端服务
│   ├── src/               # 源代码
│   ├── Dockerfile         # 前端Docker配置
│   └── package.json       # Node.js依赖
├── deploy/                # 部署配置
│   ├── mysql/            # 数据库初始化
│   └── nginx/            # Nginx配置
├── docker-compose.yml     # Docker编排文件
├── deploy.sh             # 部署脚本
└── README.md             # 项目说明
```

## 🔒 安全配置

### 生产环境建议

1. **修改默认密码**
2. **配置防火墙规则**
3. **启用SSL证书**
4. **定期备份数据**

### 环境变量安全

- 不要将 `.env.production.local` 提交到Git
- 使用强密码
- 定期轮换API密钥

## 📊 性能优化

### 服务器配置建议

- **最低配置**：2核CPU，4GB内存，20GB存储
- **推荐配置**：4核CPU，8GB内存，50GB存储

### 数据库优化

- 配置合适的连接池大小
- 启用查询缓存
- 定期优化数据库表

## 🐛 故障排除

### 常见问题

1. **端口冲突**：检查80/443端口占用
2. **内存不足**：清理Docker镜像和容器
3. **数据库连接失败**：检查数据库配置和网络

### 调试命令

```bash
# 查看容器状态
docker ps -a

# 查看服务日志
./deploy.sh logs [service-name]

# 检查系统资源
free -h && df -h
```

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

- 项目链接：https://github.com/your-username/deepsmart-chat
- 问题反馈：https://github.com/your-username/deepsmart-chat/issues

## 🙏 致谢

- [DeepSeek](https://www.deepseek.com/) - 提供强大的AI API
- [Vue.js](https://vuejs.org/) - 优秀的前端框架
- [FastAPI](https://fastapi.tiangolo.com/) - 现代Python Web框架
- [Element Plus](https://element-plus.org/) - Vue 3组件库