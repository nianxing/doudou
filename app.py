from flask import Flask, request, jsonify, render_template
import os
import json
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger('app')

# 导入基本工具和增强的wrapper
import xiaohongshu_tool as basic_tool

# 尝试导入API代理工具
try:
    import api_proxy_tool as proxy_tool
    API_PROXY_AVAILABLE = True
    logger.info("API代理工具可用")
except ImportError as e:
    API_PROXY_AVAILABLE = False
    logger.error(f"API代理工具不可用: {str(e)}")

# 尝试导入浏览器工具
try:
    import xiaohongshu_browser_tool as browser_tool
    BROWSER_TOOL_AVAILABLE = True
    logger.info("浏览器抓取工具可用")
except ImportError as e:
    BROWSER_TOOL_AVAILABLE = False
    logger.error(f"浏览器抓取工具不可用: {str(e)}")

# 尝试导入增强的wrapper
try:
    import use_minimal as wrapper
    WRAPPER_AVAILABLE = True
    logger.info("增强的wrapper可用")
except ImportError as e:
    WRAPPER_AVAILABLE = False
    logger.error(f"增强的wrapper不可用: {str(e)}")

# 检查是否配置了API密钥
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

app = Flask(__name__)

@app.route('/')
def index():
    tools_status = {
        'browser_tool': BROWSER_TOOL_AVAILABLE,
        'wrapper': WRAPPER_AVAILABLE
    }
    return render_template('index.html', tools_status=tools_status)

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    url = data.get('url')
    force_manual = data.get('force_manual', False)
    
    if not url:
        return jsonify({"error": "请提供小红书帖子URL"}), 400
    
    try:
        logger.info(f"开始分析URL: {url}")
        
        # 检查是否要强制手动输入
        if force_manual:
            logger.info("用户请求强制手动输入")
            return jsonify({
                "error": "请手动输入内容",
                "force_manual": True
            }), 200
            
        # 优先使用API代理工具
        if API_PROXY_AVAILABLE:
            try:
                logger.info("使用API代理工具...")
                result = proxy_tool.main(url)
                
                # 验证结果有效性
                if (result and 
                    result.get('original') and 
                    result['original'].get('title') != '未找到标题' and
                    result['original'].get('text') != '未找到内容'):
                    logger.info("API代理工具分析成功")
                    return jsonify(result)
                else:
                    logger.warning("API代理工具返回空结果或默认内容")
            except Exception as e:
                logger.error(f"API代理工具失败: {str(e)}")
                # 如果API代理工具失败，尝试其他工具
        
        # 如果API代理工具不可用或失败，尝试浏览器工具
        if BROWSER_TOOL_AVAILABLE:
            try:
                logger.info("使用浏览器工具...")
                content = browser_tool.fetch_post_content(url, allow_manual=False)
                analysis = browser_tool.analyze_content(content)
                result = {
                    "original": content,
                    "analysis": analysis
                }
                
                logger.info("浏览器工具分析成功")
                return jsonify(result)
            except Exception as e:
                logger.error(f"浏览器工具失败: {str(e)}")
                # 如果浏览器工具失败，尝试其他工具
        
        # 如果浏览器工具不可用或失败，尝试使用wrapper
        if WRAPPER_AVAILABLE:
            try:
                logger.info("使用wrapper...")
                result = wrapper.analyze_post(url)
                
                # 验证结果结构
                if not isinstance(result, dict):
                    raise ValueError("分析结果不是有效的字典格式")
                
                # 确保结果有必要的键
                if 'original' not in result:
                    result['original'] = {
                        'title': '未找到标题', 
                        'text': '未找到内容',
                        'images': [],
                        'video': None
                    }
                
                if 'analysis' not in result:
                    result['analysis'] = {
                        'keywords': ['小红书', '好物', '推荐'],
                        'top_posts': []
                    }
                
                logger.info("wrapper分析成功")
                return jsonify(result)
            except Exception as e:
                logger.error(f"wrapper失败: {str(e)}")
                # 如果wrapper失败，使用基本工具
        
        # 如果其他方法都不可用或失败，使用基本工具
        logger.info("使用基本工具...")
        result = basic_tool.main(url)
        logger.info("基本工具分析成功")
        return jsonify(result)
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"分析过程中出错: {str(e)}")
        logger.error(error_trace)
        
        # 返回带有错误信息的结果
        return jsonify({
            "error": str(e),
            "original": {
                "title": "处理出错",
                "text": f"分析过程中出现错误: {str(e)}",
                "images": [],
                "video": None,
                "source": "error"
            },
            "analysis": {
                "keywords": ["小红书", "好物", "推荐"],
                "top_posts": []
            }
        }), 500

@app.route('/status', methods=['GET'])
def status():
    """返回工具状态"""
    status = {
        "api_proxy_available": API_PROXY_AVAILABLE,
        "browser_tool_available": BROWSER_TOOL_AVAILABLE,
        "wrapper_available": WRAPPER_AVAILABLE,
        "openai_configured": OPENAI_API_KEY != "",
        "deepseek_configured": DEEPSEEK_API_KEY != ""
    }
    return jsonify(status)

@app.route('/manual_input', methods=['POST'])
def manual_input_route():
    """路由处理手动输入内容"""
    data = request.json
    url = data.get('url')
    title = data.get('title', '')
    text = data.get('text', '')
    images = data.get('images', [])
    
    if not url:
        return jsonify({"error": "请提供小红书帖子URL"}), 400
    
    try:
        # 创建内容对象
        content = {
            "title": title,
            "text": text,
            "images": images,
            "video": None,
            "original_url": url,
            "source": "manual_input_api"
        }
        
        # 提取标题和内容中的关键词
        combined_text = f"{title} {text}"
        
        # 按标点符号和空格分割文本
        import re
        segments = re.split(r'[,，.。!！?？:：;；\s]+', combined_text)
        
        # 过滤掉常见的停用词和短词
        stopwords = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
        keywords = [segment for segment in segments if len(segment) > 1 and segment not in stopwords]
        
        # 如果没有提取到关键词，使用标题作为关键词
        if not keywords and title:
            keywords = [title]
        # 如果还是没有，使用默认关键词
        if not keywords:
            keywords = ["小红书", "好物", "推荐"]
        
        # 选取前5个关键词（如果有）
        final_keywords = keywords[:5]
        
        # 生成相关热门帖子
        if BROWSER_TOOL_AVAILABLE:
            try:
                top_posts = browser_tool.generate_mock_top_posts(final_keywords)
            except Exception as e:
                logger.error(f"生成模拟热门帖子失败: {e}")
                # 备用方案 - 使用wrapper或基础工具
                if WRAPPER_AVAILABLE:
                    top_posts = wrapper.scraper.generate_mock_top_posts(final_keywords)
                else:
                    top_posts = basic_tool.generate_mock_top_posts(final_keywords)
        elif WRAPPER_AVAILABLE:
            top_posts = wrapper.scraper.generate_mock_top_posts(final_keywords)
        else:
            top_posts = basic_tool.generate_mock_top_posts(final_keywords)
        
        # 创建分析结果
        analysis = {
            "keywords": final_keywords,
            "top_posts": top_posts
        }
        
        # 返回结果
        result = {
            "original": content,
            "analysis": analysis
        }
        
        logger.info(f"手动输入处理成功: {title[:20]}... - 关键词: {', '.join(final_keywords)}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"手动输入处理失败: {str(e)}")
        return jsonify({"error": str(e)}), 500

# 确保在Azure上运行时绑定正确的主机和端口
if __name__ == '__main__':
    # 获取端口，如果在本地运行，则使用8080，如果在Azure上运行，则使用环境变量中指定的端口
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False) 