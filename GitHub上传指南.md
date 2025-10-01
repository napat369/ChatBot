# GitHub 上传指南

## 🚀 快速上传到 GitHub

### 方式一：使用 Git 命令行（推荐）

#### 1. 初始化 Git 仓库

```bash
# 进入项目目录
cd chatbot-system

# 初始化 Git 仓库
git init

# 添加所有文件到暂存区
git add .

# 提交到本地仓库
git commit -m "Initial commit: 深思智聊平台完整项目"
```

#### 2. 在 GitHub 创建仓库

1. 登录 [GitHub](https://github.com)
2. 点击右上角的 "+" 号，选择 "New repository"
3. 填写仓库信息：
   - **Repository name**: `deepsmart-chat` 或 `chatbot-system`
   - **Description**: `基于 DeepSeek API 的智能对话平台`
   - **Visibility**: 选择 Public 或 Private
   - **不要**勾选 "Add a README file"（我们已经有了）
4. 点击 "Create repository"

#### 3. 连接本地仓库到 GitHub

```bash
# 添加远程仓库地址（替换为你的用户名和仓库名）
git remote add origin https://github.com/your-username/deepsmart-chat.git

# 推送到 GitHub
git branch -M main
git push -u origin main
```

### 方式二：使用 GitHub Desktop（图形界面）

#### 1. 下载安装 GitHub Desktop
- 访问 [GitHub Desktop](https://desktop.github.com/)
- 下载并安装

#### 2. 创建仓库
1. 打开 GitHub Desktop
2. 点击 "File" → "Add Local Repository"
3. 选择项目文件夹 `chatbot-system`
4. 点击 "create a repository"
5. 填写仓库名称和描述
6. 点击 "Create Repository"

#### 3. 发布到 GitHub
1. 点击 "Publish repository"
2. 选择是否设为私有仓库
3. 点击 "Publish Repository"

---

## 📋 上传前检查清单

### ✅ 必须完成的步骤

- [x] 创建 `.gitignore` 文件（已完成）
- [x] 更新 `README.md` 文件（已完成）
- [ ] 检查敏感信息是否已排除
- [ ] 确认所有必要文件都已包含

### 🔒 安全检查

确保以下敏感文件**不会**被上传：

```bash
# 检查这些文件是否在 .gitignore 中
.env
.env.local
.env.production.local
backend/chatbot.db
backend/logs/
data/
deploy/ssl/
```

### 📁 确认包含的重要文件

```bash
# 确保这些文件会被上传
README.md
docker-compose.yml
deploy.sh
deploy-to-server.sh
.gitignore
backend/Dockerfile
frontend/Dockerfile
backend/requirements.txt
frontend/package.json
```

---

## 🔧 Git 常用命令

### 基本操作

```bash
# 查看仓库状态
git status

# 查看提交历史
git log --oneline

# 添加特定文件
git add filename

# 添加所有文件
git add .

# 提交更改
git commit -m "提交说明"

# 推送到远程仓库
git push origin main
```

### 分支管理

```bash
# 创建新分支
git checkout -b feature/new-feature

# 切换分支
git checkout main

# 合并分支
git merge feature/new-feature

# 删除分支
git branch -d feature/new-feature
```

### 更新和同步

```bash
# 拉取远程更新
git pull origin main

# 查看远程仓库
git remote -v

# 添加远程仓库
git remote add origin https://github.com/username/repo.git
```

---

## 🌟 GitHub 仓库优化建议

### 1. 添加 GitHub Actions（CI/CD）

创建 `.github/workflows/deploy.yml`：

```yaml
name: Deploy to Server

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Deploy to server
      run: |
        echo "部署到服务器的脚本"
```

### 2. 添加 Issue 模板

创建 `.github/ISSUE_TEMPLATE/bug_report.md`：

```markdown
---
name: Bug report
about: 创建一个 bug 报告
---

**描述 bug**
简洁明了地描述这个 bug。

**重现步骤**
1. 进入 '...'
2. 点击 '....'
3. 滚动到 '....'
4. 看到错误

**期望行为**
简洁明了地描述你期望发生什么。

**环境信息**
- OS: [e.g. Ubuntu 20.04]
- Docker版本: [e.g. 20.10.7]
- 浏览器: [e.g. Chrome 91]
```

### 3. 添加贡献指南

创建 `CONTRIBUTING.md`：

```markdown
# 贡献指南

感谢您对深思智聊平台的贡献！

## 开发流程

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 代码规范

- Python 代码遵循 PEP 8
- JavaScript 代码使用 ESLint
- 提交信息使用中文，格式：`类型: 简短描述`
```

---

## 🔄 后续维护

### 定期更新

```bash
# 添加新功能后
git add .
git commit -m "feat: 添加新的聊天功能"
git push origin main

# 修复 bug 后
git add .
git commit -m "fix: 修复消息发送失败的问题"
git push origin main

# 更新文档后
git add .
git commit -m "docs: 更新部署文档"
git push origin main
```

### 版本管理

```bash
# 创建版本标签
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# 查看所有标签
git tag -l
```

---

## 🎯 完整上传流程示例

```bash
# 1. 进入项目目录
cd c:\Users\Napat\Desktop\chatbot\chatbot-system

# 2. 初始化 Git（如果还没有）
git init

# 3. 添加所有文件
git add .

# 4. 检查状态
git status

# 5. 提交到本地
git commit -m "Initial commit: 深思智聊平台完整项目

- 添加 Vue3 + FastAPI 架构
- 集成 DeepSeek API
- 支持 Docker 一键部署
- 包含完整的部署脚本和文档"

# 6. 添加远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/your-username/deepsmart-chat.git

# 7. 推送到 GitHub
git branch -M main
git push -u origin main
```

完成后，你的项目就成功上传到 GitHub 了！🎉

### 📱 访问你的项目

- **仓库地址**: `https://github.com/your-username/deepsmart-chat`
- **克隆命令**: `git clone https://github.com/your-username/deepsmart-chat.git`