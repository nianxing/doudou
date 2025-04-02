@echo off
echo 正在启动小红书帖子分析与内容生成工具...
echo 正在检查依赖项...

REM 检查并安装依赖项
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo 依赖项安装失败，请确保已安装Python和pip。
    pause
    exit /b 1
)

echo 依赖项检查完成，正在启动应用...
python app.py

echo.
echo 应用已关闭。
pause 