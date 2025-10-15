#!/bin/bash

# 旅游攻略小助手启动脚本

echo "🌟 旅游攻略小助手启动脚本"
echo "================================"

# 检查Python版本
python_version=$(python3 --version 2>&1)
echo "Python版本: $python_version"

# 检查是否安装了依赖
if [ ! -f "requirements.txt" ]; then
    echo "❌ 未找到requirements.txt文件"
    exit 1
fi

# 安装依赖（如果需要）
echo "📦 检查依赖包..."
pip3 install -r requirements.txt --quiet

# 检查参数
if [ $# -eq 0 ]; then
    echo "🚀 启动交互模式..."
    python3 main.py interactive
elif [ "$1" = "demo" ]; then
    echo "🎭 启动演示模式..."
    python3 main.py demo
elif [ "$1" = "test" ]; then
    echo "🧪 运行系统测试..."
    python3 test_system.py
elif [ "$1" = "interactive" ]; then
    echo "🚀 启动交互模式..."
    python3 main.py interactive
else
    echo "用法: ./run.sh [demo|test|interactive]"
    echo "  demo       - 运行演示模式"
    echo "  test       - 运行系统测试"
    echo "  interactive - 运行交互模式（默认）"
    echo "  无参数     - 运行交互模式"
fi
