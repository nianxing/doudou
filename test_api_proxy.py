"""
测试API代理服务
此脚本用于测试API代理服务是否正常工作
"""

import json
import sys
import time
import logging
from urllib.parse import urlparse, parse_qs

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_api_proxy')

# 导入API代理工具
try:
    import api_proxy_tool as proxy
    logger.info("成功导入API代理工具")
except ImportError as e:
    logger.error(f"导入API代理工具失败: {str(e)}")
    sys.exit(1)

def test_api_key_validity():
    """测试API密钥是否有效"""
    logger.info("测试API密钥有效性...")
    
    # 获取所有可用的API提供商
    providers = list(proxy.API_PROVIDERS.keys())
    valid_providers = []
    
    for provider in providers:
        # 获取提供商配置
        if hasattr(proxy, 'get_api_provider'):
            config = proxy.get_api_provider(provider)
        else:
            config = proxy.API_PROVIDERS.get(provider)
            
        if not config:
            logger.warning(f"找不到提供商 {provider} 的配置")
            continue
        
        # 检查API密钥是否已设置
        params = config.get("params", {})
        api_key_param = next((k for k in params if k in ['api_key', 'access_key', 'apikey']), None)
        
        if not api_key_param:
            logger.warning(f"找不到提供商 {provider} 的API密钥参数")
            continue
            
        api_key = params.get(api_key_param)
        
        if not api_key or api_key in ["YOUR_API_KEY", "your_key_here"]:
            logger.warning(f"提供商 {provider} 的API密钥未设置")
            continue
            
        logger.info(f"提供商 {provider} 的API密钥已设置: {api_key[:5]}...")
        valid_providers.append(provider)
    
    return valid_providers

def test_fetch_content(url, provider=None):
    """测试抓取内容"""
    logger.info(f"测试抓取内容: {url}")
    
    start_time = time.time()
    html = proxy.fetch_via_proxy_api(url, provider)
    fetch_time = time.time() - start_time
    
    if html:
        logger.info(f"抓取成功! 用时: {fetch_time:.2f}秒")
        logger.info(f"HTML长度: {len(html)} 字符")
        # 保存HTML到文件
        filename = f"{urlparse(url).netloc.replace('.', '_')}_{int(time.time())}.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info(f"已保存HTML到文件: {filename}")
        return True, html
    else:
        logger.error(f"抓取失败! 用时: {fetch_time:.2f}秒")
        return False, None

def test_content_extraction(html, url):
    """测试内容提取"""
    logger.info("测试内容提取...")
    
    content = proxy.extract_content_from_html(html)
    
    if content:
        logger.info("提取成功!")
        logger.info(f"标题: {content.get('title', '无标题')}")
        logger.info(f"文本长度: {len(content.get('text', ''))}")
        logger.info(f"图片数量: {len(content.get('images', []))}")
        logger.info(f"视频: {'有' if content.get('video') else '无'}")
        
        # 保存内容到JSON文件
        filename = f"content_{int(time.time())}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
        logger.info(f"已保存内容到文件: {filename}")
        return True, content
    else:
        logger.error("提取失败!")
        return False, None

def test_keyword_search(keyword):
    """测试关键词搜索"""
    logger.info(f"测试关键词搜索: {keyword}")
    
    start_time = time.time()
    posts = proxy.search_keyword(keyword)
    search_time = time.time() - start_time
    
    if posts:
        logger.info(f"搜索成功! 用时: {search_time:.2f}秒")
        logger.info(f"找到 {len(posts)} 个帖子")
        
        for i, post in enumerate(posts[:3]):  # 只显示前3个
            logger.info(f"帖子 {i+1}: {post.get('title', '无标题')} - 点赞: {post.get('likes', 0)}")
        
        # 保存搜索结果到JSON文件
        filename = f"search_{keyword}_{int(time.time())}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        logger.info(f"已保存搜索结果到文件: {filename}")
        return True, posts
    else:
        logger.error(f"搜索失败! 用时: {search_time:.2f}秒")
        return False, None

def run_full_test(url=None, keyword=None):
    """运行完整测试"""
    logger.info("开始运行完整测试...")
    
    # 测试API密钥有效性
    valid_providers = test_api_key_validity()
    
    if not valid_providers:
        logger.error("没有找到有效的API提供商配置，请检查config.py或环境变量")
        return False
    
    logger.info(f"找到 {len(valid_providers)} 个有效的API提供商: {', '.join(valid_providers)}")
    
    # 设置当前提供商为第一个有效的提供商
    proxy.CURRENT_PROVIDER = valid_providers[0]
    
    # 测试抓取内容
    if not url:
        url = "https://www.xiaohongshu.com/explore"  # 默认测试小红书首页
    
    success, html = test_fetch_content(url)
    
    if success and html:
        # 测试内容提取
        content_success, content = test_content_extraction(html, url)
    else:
        content_success = False
    
    # 测试关键词搜索
    if not keyword:
        keyword = "美食"  # 默认搜索关键词
    
    search_success, posts = test_keyword_search(keyword)
    
    # 输出总结
    logger.info("\n测试总结:")
    logger.info(f"有效API提供商: {'成功' if valid_providers else '失败'}")
    logger.info(f"内容抓取: {'成功' if success else '失败'}")
    logger.info(f"内容提取: {'成功' if content_success else '失败'}")
    logger.info(f"关键词搜索: {'成功' if search_success else '失败'}")
    
    # 返回总体成功状态
    return success and content_success and search_success

if __name__ == "__main__":
    print("=" * 50)
    print("API代理服务测试工具")
    print("=" * 50)
    
    url = None
    keyword = None
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        url = sys.argv[1]
    if len(sys.argv) > 2:
        keyword = sys.argv[2]
    
    # 如果没有提供URL，交互式输入
    if not url:
        url = input("请输入要测试的URL(直接回车使用小红书首页): ")
        if not url:
            url = "https://www.xiaohongshu.com/explore"
    
    # 如果没有提供关键词，交互式输入
    if not keyword:
        keyword = input("请输入要测试的搜索关键词(直接回车使用'美食'): ")
        if not keyword:
            keyword = "美食"
    
    print("\n开始测试...")
    success = run_full_test(url, keyword)
    
    if success:
        print("\n✅ 测试全部通过!")
        sys.exit(0)
    else:
        print("\n❌ 测试未通过，请检查日志!")
        sys.exit(1) 