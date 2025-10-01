#!/bin/bash

# 深思智聊平台 - Docker一键部署脚本
# 使用方法: ./deploy.sh [start|stop|restart|logs|update]

set -e

PROJECT_NAME="deepsmart-chat"
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env.production"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
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

# 检查Docker和Docker Compose
check_requirements() {
    log_info "检查系统要求..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    log_success "系统要求检查通过"
}

# 检查环境变量文件
check_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        log_warning "环境变量文件 $ENV_FILE 不存在，正在创建..."
        cp .env.production.example $ENV_FILE 2>/dev/null || {
            log_error "请先配置环境变量文件 $ENV_FILE"
            exit 1
        }
    fi
    
    # 检查必要的环境变量
    source $ENV_FILE
    
    if [ -z "$DEEPSEEK_API_KEY" ] || [ "$DEEPSEEK_API_KEY" = "your_deepseek_api_key_here" ]; then
        log_error "请在 $ENV_FILE 中配置 DEEPSEEK_API_KEY"
        exit 1
    fi
    
    log_success "环境变量检查通过"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    mkdir -p deploy/ssl
    mkdir -p backend/logs
    
    log_success "目录创建完成"
}

# 启动服务
start_services() {
    log_info "启动深思智聊平台服务..."
    
    check_requirements
    check_env_file
    create_directories
    
    # 构建并启动服务
    docker-compose --env-file $ENV_FILE -f $COMPOSE_FILE up -d --build
    
    log_success "服务启动完成！"
    log_info "访问地址: http://localhost"
    log_info "查看日志: ./deploy.sh logs"
}

# 停止服务
stop_services() {
    log_info "停止深思智聊平台服务..."
    
    docker-compose -f $COMPOSE_FILE down
    
    log_success "服务已停止"
}

# 重启服务
restart_services() {
    log_info "重启深思智聊平台服务..."
    
    stop_services
    start_services
}

# 查看日志
show_logs() {
    if [ -z "$2" ]; then
        docker-compose -f $COMPOSE_FILE logs -f
    else
        docker-compose -f $COMPOSE_FILE logs -f "$2"
    fi
}

# 更新服务
update_services() {
    log_info "更新深思智聊平台服务..."
    
    # 拉取最新代码（如果是Git仓库）
    if [ -d ".git" ]; then
        log_info "拉取最新代码..."
        git pull
    fi
    
    # 重新构建并启动
    docker-compose --env-file $ENV_FILE -f $COMPOSE_FILE up -d --build
    
    # 清理未使用的镜像
    docker image prune -f
    
    log_success "服务更新完成！"
}

# 显示服务状态
show_status() {
    log_info "深思智聊平台服务状态:"
    docker-compose -f $COMPOSE_FILE ps
}

# 备份数据
backup_data() {
    log_info "备份数据库..."
    
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p $BACKUP_DIR
    
    # 备份MySQL数据
    docker-compose -f $COMPOSE_FILE exec mysql mysqldump -u root -p$MYSQL_ROOT_PASSWORD --all-databases > $BACKUP_DIR/mysql_backup.sql
    
    log_success "数据备份完成: $BACKUP_DIR"
}

# SSL证书配置
setup_ssl() {
    if [ -z "$DOMAIN_NAME" ]; then
        log_error "请在 $ENV_FILE 中配置 DOMAIN_NAME"
        exit 1
    fi
    
    log_info "为域名 $DOMAIN_NAME 配置SSL证书..."
    
    # 使用Certbot申请SSL证书
    docker run --rm -v $(pwd)/deploy/ssl:/etc/letsencrypt certbot/certbot certonly \
        --standalone \
        --email $SSL_EMAIL \
        --agree-tos \
        --no-eff-email \
        -d $DOMAIN_NAME
    
    log_success "SSL证书配置完成"
}

# 显示帮助信息
show_help() {
    echo "深思智聊平台 Docker 部署脚本"
    echo ""
    echo "使用方法:"
    echo "  ./deploy.sh [命令]"
    echo ""
    echo "可用命令:"
    echo "  start     启动所有服务"
    echo "  stop      停止所有服务"
    echo "  restart   重启所有服务"
    echo "  logs      查看服务日志"
    echo "  update    更新服务"
    echo "  status    显示服务状态"
    echo "  backup    备份数据"
    echo "  ssl       配置SSL证书"
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  ./deploy.sh start"
    echo "  ./deploy.sh logs backend"
    echo "  ./deploy.sh update"
}

# 主函数
main() {
    case "${1:-help}" in
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        logs)
            show_logs "$@"
            ;;
        update)
            update_services
            ;;
        status)
            show_status
            ;;
        backup)
            backup_data
            ;;
        ssl)
            setup_ssl
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"