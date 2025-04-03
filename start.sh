#!/bin/bash

echo "小红书内容分析工具启动脚本"
echo "============================"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未安装Python，请先安装Python 3.8或更高版本。"
    echo "可以从 https://www.python.org/downloads/ 下载安装，或使用系统包管理器安装。"
    exit 1
fi

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "正在创建虚拟环境..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "创建虚拟环境失败，请检查Python安装是否完整。"
        exit 1
    fi
fi

# 激活虚拟环境并安装依赖
echo "正在激活虚拟环境并安装依赖..."
source venv/bin/activate
pip install -r requirements.txt

# 安装Chrome WebDriver
echo "安装Chrome WebDriver..."
pip install webdriver-manager

# 启动应用
echo ""
echo "启动小红书内容分析工具..."
echo "请在浏览器中访问: http://localhost:8080"
echo ""
echo "按Ctrl+C可以停止服务。"
echo "============================"
python app.py 