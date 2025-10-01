#!/bin/bash

# 深思智聊平台 - 自动化服务器部署脚本
# 使用方法: ./deploy-to-server.sh [server-ip] [username]

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查参数
if [ $# -lt 2 ]; then
    echo "使用方法: $0 <服务器IP> <用户名> [项目路径]"
    echo "示例: $0 192.168.1.100 ubuntu /home/ubuntu/chatbot"
    exit 1
fi

SERVER_IP=$1
USERNAME=$2
REMOTE_PATH=${3:-"/home/$USERNAME/chatbot-system"}
LOCAL_PATH="."

log_info "开始部署到服务器 $SERVER_IP..."

# 1. 检查本地文件
log_info "检查本地文件..."
if [ ! -f "docker-compose.yml" ]; then
    log_error "未找到 docker-compose.yml 文件，请确保在项目根目录执行"
    exit 1
fi

# 2. 创建部署包
log_info "创建部署包..."
DEPLOY_PACKAGE="chatbot-deploy-$(date +%Y%m%d_%H%M%S).tar.gz"

tar --exclude='node_modules' \
    --exclude='.git' \
    --exclude='*.log' \
    --exclude='backend/logs/*' \
    --exclude='backend/chatbot.db' \
    --exclude='frontend/dist' \
    --exclude='data' \
    -czf $DEPLOY_PACKAGE .

log_success "部署包创建完成: $DEPLOY_PACKAGE"

# 3. 上传到服务器
log_info "上传文件到服务器..."
scp $DEPLOY_PACKAGE $USERNAME@$SERVER_IP:/tmp/

# 4. 在服务器上执行部署
log_info "在服务器上执行部署..."
ssh $USERNAME@$SERVER_IP << EOF
    set -e
    
    echo "准备部署环境..."
    
    # 创建项目目录
    mkdir -p $REMOTE_PATH
    cd $REMOTE_PATH
    
    # 备份现有部署（如果存在）
    if [ -f "docker-compose.yml" ]; then
        echo "备份现有部署..."
        mkdir -p backups
        tar -czf backups/backup-\$(date +%Y%m%d_%H%M%S).tar.gz . --exclude=backups --exclude=data 2>/dev/null || true
    fi
    
    # 解压新版本
    echo "解压新版本..."
    tar -xzf /tmp/$DEPLOY_PACKAGE
    
    # 设置执行权限
    chmod +x deploy.sh
    
    # 检查Docker环境
    echo "检查Docker环境..."
    if ! command -v docker &> /dev/null; then
        echo "安装Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker \$USER
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo "安装Docker Compose..."
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
    
    # 配置环境变量
    if [ ! -f ".env.production.local" ]; then
        echo "创建环境变量配置文件..."
        cp .env.production .env.production.local
        echo ""
        echo "⚠️  请编辑 .env.production.local 文件配置以下参数："
        echo "   - DEEPSEEK_API_KEY"
        echo "   - MYSQL_ROOT_PASSWORD"
        echo "   - MYSQL_PASSWORD"
        echo "   - DOMAIN_NAME（如果需要域名访问）"
        echo ""
        echo "配置完成后运行: ./deploy.sh start"
    else
        echo "环境变量文件已存在，直接启动服务..."
        ./deploy.sh restart
    fi
    
    # 清理临时文件
    rm -f /tmp/$DEPLOY_PACKAGE
    
    echo ""
    echo "🎉 部署完成！"
    echo "📍 项目路径: $REMOTE_PATH"
    echo "🌐 访问地址: http://$SERVER_IP"
    echo "📋 管理命令:"
    echo "   ./deploy.sh start   # 启动服务"
    echo "   ./deploy.sh stop    # 停止服务"
    echo "   ./deploy.sh logs    # 查看日志"
    echo "   ./deploy.sh status  # 查看状态"
EOF

# 5. 清理本地临时文件
rm -f $DEPLOY_PACKAGE

log_success "部署完成！"
log_info "您现在可以通过 http://$SERVER_IP 访问应用"
log_info "SSH连接服务器: ssh $USERNAME@$SERVER_IP"
log_info "项目目录: $REMOTE_PATH"