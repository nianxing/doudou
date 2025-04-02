#!/bin/bash
echo "正在启动小红书帖子分析与内容生成工具..."
echo "正在检查依赖项..."

# 检查并安装依赖项
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "依赖项安装失败，请确保已安装Python和pip。"
    read -p "按回车键退出..."
    exit 1
fi

echo "依赖项检查完成，正在启动应用..."
python app.py

echo ""
echo "应用已关闭。"
read -p "按回车键退出..." 