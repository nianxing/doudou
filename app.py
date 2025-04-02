from flask import Flask, request, jsonify, render_template
import os
import json

# 导入两个工具，根据配置决定使用哪个
import xiaohongshu_tool as basic_tool
# 检查AI版本工具是否存在
try:
    import xiaohongshu_ai_tool as ai_tool
    AI_TOOL_AVAILABLE = True
except ImportError:
    AI_TOOL_AVAILABLE = False

# 检查是否配置了AI API密钥
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
USE_AI = (OPENAI_API_KEY != "" or DEEPSEEK_API_KEY != "") and AI_TOOL_AVAILABLE

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', use_ai=USE_AI)

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "请提供小红书帖子URL"}), 400
    
    try:
        # 根据配置选择使用哪个工具
        if USE_AI:
            result = ai_tool.main(url)
        else:
            result = basic_tool.main(url)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    """返回AI集成状态"""
    status = {
        "ai_available": AI_TOOL_AVAILABLE,
        "openai_configured": OPENAI_API_KEY != "",
        "deepseek_configured": DEEPSEEK_API_KEY != "",
        "using_ai": USE_AI
    }
    return jsonify(status)

# 确保在Azure上运行时绑定正确的主机和端口
if __name__ == '__main__':
    # 获取端口，如果在本地运行，则使用8080，如果在Azure上运行，则使用环境变量中指定的端口
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False) 