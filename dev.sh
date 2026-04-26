#!/bin/bash
# v1.1 - 物采通本地开发辅助脚本
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[OK]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 启动后端（FastAPI）
start_backend() {
    print_info "启动后端 API 服务..."
    export PYTHONPATH="$PROJECT_ROOT"
    .venv2/bin/uvicorn app.main:app --reload --port 8001 &
    print_success "后端启动：http://localhost:8001  文档：http://localhost:8001/docs"
}

# 启动前端（Web 管理台）
start_frontend() {
    print_info "启动 Web 管理台..."
    cd web-admin && npm run dev &
    cd "$PROJECT_ROOT"
    print_success "前端启动：http://localhost:3000"
}

# 执行数据库迁移
migrate() {
    print_info "执行数据库迁移..."
    PYTHONPATH="$PROJECT_ROOT" .venv2/bin/alembic upgrade head
    print_success "迁移完成"
}

# 运行代码检查
check() {
    print_info "运行 flake8 检查..."
    .venv2/bin/flake8 app/ --max-line-length=120 --ignore=E203,W503 || true
    print_success "检查完成"
}

# 全部启动
start_all() {
    start_backend
    sleep 2
    start_frontend
    print_success "全部服务已启动"
    print_info "按 Ctrl+C 停止所有进程"
    wait
}

case "${1:-help}" in
    backend)    start_backend; wait ;;
    frontend)   start_frontend; wait ;;
    migrate)    migrate ;;
    check)      check ;;
    all)        start_all ;;
    *)
        echo "物采通本地开发脚本"
        echo "用法："
        echo "  ./dev.sh all       # 同时启动后端+前端"
        echo "  ./dev.sh backend   # 只启动后端 (port 8001)"
        echo "  ./dev.sh frontend  # 只启动前端 (port 3000)"
        echo "  ./dev.sh migrate   # 执行数据库迁移"
        echo "  ./dev.sh check     # 代码风格检查"
        exit 0
        ;;
esac
