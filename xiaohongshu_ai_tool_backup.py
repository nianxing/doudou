import requests
from bs4 import BeautifulSoup
import json
import re
import os
import random
import time
import hashlib
from urllib.parse import quote
import logging
from datetime import datetime

# 导入反爬机制工具类
try:
    from xiaohongshu_tool import AntiCrawlUtils, logger
except ImportError:
    # 如果无法导入，配置自己的日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('xiaohongshu_ai_scraper.log', encoding='utf-8')
        ]
    )
    logger = logging.getLogger('xiaohongshu_ai_scraper')
    # 重新定义AntiCrawlUtils类(这里依赖原始工具类)
    raise ImportError("必须能够导入xiaohongshu_tool模块中的AntiCrawlUtils")

# 检查是否安装了OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# 检查是否安装了DeepSeek库
try:
    # DeepSeek不需要专门的库，但我们可以检查requests是否可用
    import requests
    DEEPSEEK_AVAILABLE = True
except ImportError:
    DEEPSEEK_AVAILABLE = False

# 尝试导入媒体分析模块
try:
    import media_analyzer
    MEDIA_ANALYSIS_AVAILABLE = True
except ImportError:
    MEDIA_ANALYSIS_AVAILABLE = False

# 定义API密钥和默认配置
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

# 如果有OpenAI API密钥，则配置客户端
if OPENAI_API_KEY and OPENAI_AVAILABLE:
    openai.api_key = OPENAI_API_KEY

# 使用哪个AI服务，优先DeepSeek，其次OpenAI
USE_DEEPSEEK = DEEPSEEK_API_KEY != ""
USE_OPENAI = not USE_DEEPSEEK and OPENAI_API_KEY != "" and OPENAI_AVAILABLE

# 尝试导入反爬机制工具类
try:
    from xiaohongshu_tool import AntiCrawlUtils
except ImportError:
    # 如果无法导入，使用基本的方法
    logger.warning("无法导入AntiCrawlUtils，将使用基本的请求方法")
    
    # 基本的用户代理列表
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
    ]
    
    # 基本的请求函数
    def get_random_user_agent():
        return random.choice(USER_AGENTS)
        
    def add_random_delay(min_seconds=1, max_seconds=3):
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
        return delay
        
    def get_enhanced_headers(referer=None, is_api=False):
        headers = {
            "User-Agent": get_random_user_agent(),
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": referer or "https://www.xiaohongshu.com/"
        }
        if is_api:
            headers["Accept"] = "application/json"
        else:
            headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        return headers
        
    def get_cookies(custom_cookies_str=None):
        return {}
        
    # 简化版的请求函数
    class AntiCrawlUtils:
        @staticmethod
        def make_request(url, method="GET", params=None, headers=None, timeout=15, **kwargs):
            if headers is None:
                headers = get_enhanced_headers(referer=url)
            
            add_random_delay(1, 3)
            
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=headers,
                    timeout=timeout,
                    **kwargs
                )
                return response
            except Exception as e:
                logger.error(f"请求失败: {str(e)}")
                raise
else:
    # 使用已导入的AntiCrawlUtils
    def get_random_user_agent():
        return AntiCrawlUtils.get_random_user_agent()
        
    def add_random_delay(min_seconds=1, max_seconds=3):
        return AntiCrawlUtils.add_random_delay(min_seconds, max_seconds)
        
    def get_enhanced_headers(referer=None, is_api=False):
        return AntiCrawlUtils.get_enhanced_headers(referer, is_api)
        
    def get_cookies(custom_cookies_str=None):
        return AntiCrawlUtils.get_cookies(custom_cookies_str=custom_cookies_str)

def fetch_post_content(url):
    """
    抓取小红书帖子内容，包括文字和图片
    
    Args:
        url: 小红书帖子URL
        
    Returns:
        dict: 包含文字、图片和视频URL的字典
    """
    try:
        # 使用增强的请求方法
        headers = get_enhanced_headers(referer=url)
        response = AntiCrawlUtils.make_request(
            url=url, 
            headers=headers,
            timeout=15
        )
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 检查是否有反爬验证
        if "验证" in soup.text or "校验" in soup.text or "captcha" in soup.text.lower():
            logger.warning(f"检测到反爬验证码，尝试备选方法...")
            return fetch_post_content_alternative(url)
        
        # 提取标题
        title_elem = soup.select_one('h1.title') or soup.select_one('div.content-container div.title')
        if not title_elem:
            # 尝试JS渲染的帖子页面结构
            title_elem = soup.select_one('meta[property="og:title"]')
            title = title_elem['content'] if title_elem and 'content' in title_elem.attrs else "未找到标题"
        else:
            title = title_elem.text.strip()
        
        # 提取正文内容
        content_elem = soup.select_one('div.content') or soup.select_one('div.desc')
        if not content_elem:
            # 尝试提取script中的数据
            scripts = soup.select('script')
            content = ""
            for script in scripts:
                if script.string and "window.__INITIAL_STATE__" in script.string:
                    try:
                        # 提取JSON部分
                        json_str = script.string.split("window.__INITIAL_STATE__=")[1].split(";")[0]
                        data = json.loads(json_str)
                        # 尝试从数据中提取内容
                        if "note" in data and "desc" in data["note"]:
                            content = data["note"]["desc"]
                            break
                    except Exception:
                        pass
            
            if not content:
                logger.warning(f"未能从页面直接提取内容，尝试备选方法...")
                return fetch_post_content_alternative(url)
        else:
            content = content_elem.text.strip()
        
        # 提取图片URL
        image_urls = []
        img_elems = soup.select('div.carousel img') or soup.select('div.swiper-slide img')
        
        # 如果上面的选择器没有找到图片，尝试其他选择器
        if not img_elems:
            img_elems = soup.select('div.note-content img') or soup.select('img.upload-image')
        
        for img in img_elems:
            if img.get('src'):
                image_urls.append(img['src'])
            elif img.get('data-src'):
                image_urls.append(img['data-src'])
                
        # 如果图片列表为空，尝试从JavaScript数据中提取
        if not image_urls:
            scripts = soup.select('script')
            for script in scripts:
                if script.string and "window.__INITIAL_STATE__" in script.string:
                    try:
                        # 提取JSON部分
                        json_str = script.string.split("window.__INITIAL_STATE__=")[1].split(";")[0]
                        data = json.loads(json_str)
                        # 尝试从数据中提取图片
                        if "note" in data and "imageList" in data["note"]:
                            for img in data["note"]["imageList"]:
                                if "url" in img:
                                    image_urls.append(img["url"])
                    except Exception:
                        pass
        
        # 提取视频URL
        video_url = None
        video_elem = soup.select_one('video')
        if video_elem and video_elem.get('src'):
            video_url = video_elem['src']
        else:
            # 尝试从JavaScript数据中提取视频URL
            scripts = soup.select('script')
            for script in scripts:
                if script.string and "window.__INITIAL_STATE__" in script.string:
                    try:
                        # 提取JSON部分
                        json_str = script.string.split("window.__INITIAL_STATE__=")[1].split(";")[0]
                        data = json.loads(json_str)
                        # 尝试从数据中提取视频URL
                        if "note" in data and "video" in data["note"] and "url" in data["note"]["video"]:
                            video_url = data["note"]["video"]["url"]
                            break
                    except Exception:
                        pass
        
        # 如果内容非常短，可能抓取失败，尝试备选方法
        if len(content) < 10 and not image_urls and not video_url:
            logger.warning(f"抓取内容异常，尝试备选方法...")
            return fetch_post_content_alternative(url)
        
        logger.info(f"成功提取帖子内容: 标题={title[:20]}..., 内容长度={len(content)}, 图片数={len(image_urls)}")
        
        return {
            "title": title,
            "text": content,
            "images": image_urls,
            "video": video_url
        }
    
    except Exception as e:
        logger.error(f"抓取帖子内容失败: {str(e)}，尝试备选方法")
        return fetch_post_content_alternative(url)

def fetch_post_content_alternative(url):
    """备用抓取方法，使用移动端模拟或不同的请求方式"""
    # 模拟移动设备
    mobile_headers = get_enhanced_headers(referer=url, is_api=False)
    mobile_headers["User-Agent"] = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
    
    cookies = get_cookies()
    add_random_delay(2, 4)
    
    try:
        response = requests.get(url, headers=mobile_headers, cookies=cookies, timeout=15)
    response.raise_for_status()
        
    soup = BeautifulSoup(response.text, 'html.parser')
    
        # 尝试提取JSON数据
        json_data = None
        scripts = soup.select('script')
        for script in scripts:
            if script.string and ("window.__INITIAL_STATE__" in script.string or "window.__INITIAL_SSR_STATE__" in script.string):
                try:
                    # 提取JSON部分
                    if "window.__INITIAL_STATE__" in script.string:
                        json_str = script.string.split("window.__INITIAL_STATE__=")[1].split(";")[0]
                    else:
                        json_str = script.string.split("window.__INITIAL_SSR_STATE__=")[1].split(";")[0]
                    
                    json_data = json.loads(json_str)
                break
                except:
                    continue
        
        if json_data and "note" in json_data:
            note_data = json_data["note"]
            
            # 提取标题 (通常是作者名称 + 正文前几个字)
            title = note_data.get("title", "")
            if not title and "user" in note_data and "nickname" in note_data["user"]:
                # 如果没有标题，使用作者名称
                title = note_data["user"]["nickname"] + "的笔记"
            
            # 提取正文
            content = note_data.get("desc", "")
            
            # 提取图片
            image_urls = []
            if "imageList" in note_data:
                for img in note_data["imageList"]:
                    if "url" in img:
                        image_urls.append(img["url"])
    
    # 提取视频
            video_url = None
            if "video" in note_data and "url" in note_data["video"]:
                video_url = note_data["video"]["url"]
            
            return {
                "title": title,
                "text": content,
                "images": image_urls,
                "video": video_url
            }
        
        # 如果无法从JSON提取，使用传统方法
        title_elem = soup.select_one('h1.title') or soup.select_one('div.content-container div.title')
        title = title_elem.text.strip() if title_elem else "未找到标题"
        
        content_elem = soup.select_one('div.content') or soup.select_one('div.desc')
        content = content_elem.text.strip() if content_elem else "未找到内容"
        
        image_urls = []
        img_elems = soup.select('div.carousel img') or soup.select('div.swiper-slide img') or soup.select('div.note-content img')
        for img in img_elems:
            if img.get('src'):
                image_urls.append(img['src'])
            elif img.get('data-src'):
                image_urls.append(img['data-src'])
        
        video_url = None
        video_elem = soup.select_one('video')
        if video_elem and video_elem.get('src'):
            video_url = video_elem['src']
    
    return {
            "title": title,
            "text": content,
            "images": image_urls,
            "video": video_url
        }
    
    except Exception as e:
        print(f"备选方法抓取失败: {str(e)}，使用手动输入提示")
        # 如果备选方法也失败，直接返回空结果
        # 调用方应检查结果是否为空并提示用户手动输入
        return {
            "title": "未找到标题",
            "text": "未找到内容，请手动输入",
            "images": [],
            "video": None
    }

def manual_input():
    """用户手动输入内容"""
    print("抓取失败，请手动输入内容:")
    title = input("请输入帖子标题: ")
    text = input("请输入帖子正文: ")
    img_count = int(input("图片数量: ") or "0")
    images = []
    for i in range(img_count):
        img_url = input(f"图片{i+1}的URL: ")
        if img_url:
            images.append(img_url)
    video = input("视频URL (如无请留空): ")
    return {
        "title": title,
        "text": text,
        "images": images,
        "video": video if video else None
    }

def analyze_content(content):
    """
    分析帖子内容
    
    Args:
        content: 帖子内容字典
        
    Returns:
        dict: 包含关键词和相关热门帖子的字典
    """
    text = content["text"]
    title = content["title"]
    
    # 使用AI分析内容或使用规则分析
    if USE_DEEPSEEK:
        keywords, ai_analysis = analyze_with_deepseek(title, text)
    elif USE_OPENAI:
        keywords, ai_analysis = analyze_with_openai(title, text)
    else:
        # 规则分析
        keywords = extract_simple_keywords(title + " " + text)
        ai_analysis = {}
    
    # 如果AI分析失败，回退到规则分析
    if not keywords:
        keywords = extract_simple_keywords(title + " " + text)
    
    # 尝试爬取相关热门帖子
    try:
        top_posts = fetch_top_posts(keywords[0] if keywords else "好物推荐")
    except Exception as e:
        print(f"爬取热门帖子失败: {str(e)}")
        # 爬取失败时使用模拟数据
        top_posts = generate_mock_top_posts(keywords)
    
    # 分析图片和视频内容(如果可用)
    media_analysis = {}
    if MEDIA_ANALYSIS_AVAILABLE and (USE_DEEPSEEK or USE_OPENAI):
        try:
            # 分析图片
            if content.get("images"):
                try:
                    image_analyses = media_analyzer.batch_analyze_images(content["images"], max_images=3)
                    media_analysis["image_analyses"] = image_analyses
                    
                    # 从图片分析中提取额外关键词
                    for img_analysis in image_analyses:
                        if "keywords" in img_analysis and img_analysis["keywords"]:
                            # 添加来自图片的关键词（最多3个）
                            img_keywords = img_analysis["keywords"][:3]
                            keywords.extend([k for k in img_keywords if k not in keywords])
                            # 确保关键词总数不超过8个
                            if len(keywords) > 8:
                                keywords = keywords[:8]
                except Exception as e:
                    print(f"图片分析失败: {str(e)}，使用模拟分析结果")
                    # 使用模拟分析数据
                    image_analyses = [media_analyzer.generate_mock_image_analysis() for _ in range(min(3, len(content.get("images", []))))]
                    media_analysis["image_analyses"] = image_analyses
            
            # 分析视频
            if content.get("video"):
                try:
                    video_analysis = media_analyzer.analyze_video(content["video"])
                    media_analysis["video_analysis"] = video_analysis
                    
                    # 从视频分析中提取额外关键词
                    if "keywords" in video_analysis and video_analysis["keywords"]:
                        # 添加来自视频的关键词（最多2个）
                        video_keywords = video_analysis["keywords"][:2]
                        keywords.extend([k for k in video_keywords if k not in keywords])
                        # 确保关键词总数不超过8个
                        if len(keywords) > 8:
                            keywords = keywords[:8]
                except Exception as e:
                    print(f"视频分析失败: {str(e)}，使用模拟分析结果")
                    # 使用模拟分析数据
                    video_analysis = media_analyzer.generate_mock_video_analysis()
                    media_analysis["video_analysis"] = video_analysis
            
            # 生成媒体改进建议
            if "image_analyses" in media_analysis or "video_analysis" in media_analysis:
                try:
                    image_analyses = media_analysis.get("image_analyses", [])
                    video_analysis = media_analysis.get("video_analysis", {})
                    media_suggestions = media_analyzer.get_media_improvements(image_analyses, video_analysis)
                    media_analysis["suggestions"] = media_suggestions
                except Exception as e:
                    print(f"媒体改进建议生成失败: {str(e)}，使用基本建议")
                    # 提供基本建议
                    media_analysis["suggestions"] = [
                        "建议添加更多高质量图片，展示产品多角度细节",
                        "建议添加产品使用视频，展示实际效果",
                        "图片推荐使用自然光拍摄，增加清晰度"
                    ]
                
        except Exception as e:
            print(f"媒体分析整体失败: {str(e)}")
    
    result = {
        "keywords": keywords, 
        "top_posts": top_posts
    }
    
    # 如果有AI分析，添加到结果中
    if ai_analysis:
        result["ai_analysis"] = ai_analysis
    
    # 如果有媒体分析，添加到结果中
    if media_analysis:
        result["media_analysis"] = media_analysis
    
    return result

def analyze_with_openai(title, text):
    """使用OpenAI API进行内容分析"""
    if not USE_OPENAI:
        return [], {}
    
    prompt = f"""
    分析以下小红书帖子内容，提取关键词并进行内容分析：
    
    标题: {title}
    
    内容: {text}
    
    请提供:
    1. 5个与内容最相关的关键词（单词或短语）
    2. 内容分析结果，包括：
       - 帖子主题
       - 产品或服务类别
       - 写作风格
       - 目标受众
       - 情感基调
    
    以JSON格式返回，格式如下:
    {{
        "keywords": ["关键词1", "关键词2", ...],
        "analysis": {{
            "topic": "帖子主题",
            "category": "产品或服务类别",
            "style": "写作风格",
            "audience": "目标受众",
            "tone": "情感基调"
        }}
    }}
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个专业的内容分析专家，擅长分析小红书等社交平台的内容。"},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result["keywords"], result["analysis"]
    except Exception as e:
        print(f"OpenAI API调用失败: {str(e)}")
        return [], {}

def analyze_with_deepseek(title, text):
    """使用DeepSeek API进行内容分析"""
    if not USE_DEEPSEEK:
        return [], {}
    
    prompt = f"""
    分析以下小红书帖子内容，提取关键词并进行内容分析：
    
    标题: {title}
    
    内容: {text}
    
    请提供:
    1. 5个与内容最相关的关键词（单词或短语）
    2. 内容分析结果，包括：
       - 帖子主题
       - 产品或服务类别
       - 写作风格
       - 目标受众
       - 情感基调
    
    以JSON格式返回，格式如下:
    {{
        "keywords": ["关键词1", "关键词2", ...],
        "analysis": {{
            "topic": "帖子主题",
            "category": "产品或服务类别",
            "style": "写作风格",
            "audience": "目标受众",
            "tone": "情感基调"
        }}
    }}
    """
    
    try:
        # DeepSeek API调用（需要根据DeepSeek的具体API调整）
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一个专业的内容分析专家，擅长分析小红书等社交平台的内容。"},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"}
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        # 解析结果
        content = result["choices"][0]["message"]["content"]
        result_json = json.loads(content)
        return result_json["keywords"], result_json["analysis"]
    except Exception as e:
        print(f"DeepSeek API调用失败: {str(e)}")
        return [], {}

def extract_simple_keywords(text):
    """简单的关键词提取"""
    # 预定义可能的产品类别
    categories = ["面膜", "化妆品", "护肤", "美妆", "口红", "眼影", "粉底", "洗面奶", "精华", "防晒", 
                  "水乳", "香水", "美甲", "发型", "穿搭", "衣服", "鞋子", "包包", "饰品", "零食", 
                  "美食", "家居", "旅行", "健身", "减肥", "瑜伽"]
    
    found_keywords = []
    for category in categories:
        if category in text:
            found_keywords.append(category)
    
    # 提取产品名称（简单匹配产品+数字/字母的组合）
    product_pattern = r'([A-Za-z]+[0-9A-Za-z]*|[a-zA-Z\u4e00-\u9fa5]+[+]?)'
    potential_products = re.findall(product_pattern, text)
    
    # 过滤常见词
    stop_words = ["这个", "那个", "的", "了", "是", "我", "你", "他", "她", "它", "这", "那", "有", "和", "与"]
    filtered_products = [p for p in potential_products if len(p) > 1 and p not in stop_words]
    
    # 组合关键词，优先使用分类，然后添加产品名
    keywords = found_keywords + [p for p in filtered_products if p not in found_keywords]
    
    # 最多返回5个关键词
    return keywords[:5] if keywords else ["好物"]

def generate_optimized_content(content, analysis):
    """
    生成优化内容
    
    Args:
        content: 原始内容
        analysis: 分析结果
        
    Returns:
        dict: 优化后的标题、正文和建议
    """
    original_title = content["title"]
    original_text = content["text"]
    keywords = analysis["keywords"]
    top_posts = analysis["top_posts"]
    ai_analysis = analysis.get("ai_analysis", {})
    
    # 使用AI生成优化内容或使用规则生成
    if USE_DEEPSEEK:
        optimized_title, optimized_body = generate_with_deepseek(original_title, original_text, keywords, ai_analysis)
    elif USE_OPENAI:
        optimized_title, optimized_body = generate_with_openai(original_title, original_text, keywords, ai_analysis)
    else:
        # 使用规则生成
        keyword = keywords[0] if keywords else "好物"
        optimized_title = generate_title(keyword, original_title)
        optimized_body = generate_body(keyword, original_text, top_posts)
    
    # 如果AI生成失败，回退到规则生成
    if not optimized_title or not optimized_body:
        keyword = keywords[0] if keywords else "好物"
        optimized_title = generate_title(keyword, original_title)
        optimized_body = generate_body(keyword, original_text, top_posts)
    
    # 生成内容改进建议
    suggestions = generate_suggestions(content, ai_analysis)
    
    # 如果有媒体分析建议，添加到改进建议中
    if "media_analysis" in analysis and "suggestions" in analysis["media_analysis"]:
        media_suggestions = analysis["media_analysis"]["suggestions"]
        suggestions.extend(media_suggestions)
    
    return {
        "title": optimized_title,
        "body": optimized_body,
        "suggestions": suggestions
    }

def generate_with_openai(original_title, original_text, keywords, ai_analysis):
    """使用OpenAI API生成优化内容"""
    if not USE_OPENAI:
        return "", ""
    
    # 构建分析信息
    analysis_text = ""
    if ai_analysis:
        analysis_text = f"""
        分析信息:
        - 主题: {ai_analysis.get('topic', '未知')}
        - 产品类别: {ai_analysis.get('category', '未知')}
        - 写作风格: {ai_analysis.get('style', '未知')}
        - 目标受众: {ai_analysis.get('audience', '未知')}
        - 情感基调: {ai_analysis.get('tone', '未知')}
        """
    
    # 构建提示
    prompt = f"""
    根据以下小红书帖子内容和分析结果，生成一个SEO优化、更有吸引力的标题和正文：
    
    原标题: {original_title}
    
    原内容: {original_text}
    
    关键词: {', '.join(keywords)}
    
    {analysis_text}
    
    请生成:
    1. 一个吸引人的标题（不超过30个字）
    2. 一个完整的正文（保留原文的核心信息，但使其更具吸引力、更易阅读、更符合小红书平台风格）
    
    以JSON格式返回:
    {{
        "title": "优化标题",
        "body": "优化正文"
    }}
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个专业的社交媒体内容创作专家，擅长为小红书等平台创作吸引人的内容。"},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result["title"], result["body"]
    except Exception as e:
        print(f"OpenAI API调用失败: {str(e)}")
        return "", ""

def generate_with_deepseek(original_title, original_text, keywords, ai_analysis):
    """使用DeepSeek API生成优化内容"""
    if not USE_DEEPSEEK:
        return "", ""
    
    # 构建分析信息
    analysis_text = ""
    if ai_analysis:
        analysis_text = f"""
        分析信息:
        - 主题: {ai_analysis.get('topic', '未知')}
        - 产品类别: {ai_analysis.get('category', '未知')}
        - 写作风格: {ai_analysis.get('style', '未知')}
        - 目标受众: {ai_analysis.get('audience', '未知')}
        - 情感基调: {ai_analysis.get('tone', '未知')}
        """
    
    # 构建提示
    prompt = f"""
    根据以下小红书帖子内容和分析结果，生成一个SEO优化、更有吸引力的标题和正文：
    
    原标题: {original_title}
    
    原内容: {original_text}
    
    关键词: {', '.join(keywords)}
    
    {analysis_text}
    
    请生成:
    1. 一个吸引人的标题（不超过30个字）
    2. 一个完整的正文（保留原文的核心信息，但使其更具吸引力、更易阅读、更符合小红书平台风格）
    
    以JSON格式返回:
    {{
        "title": "优化标题",
        "body": "优化正文"
    }}
    """
    
    try:
        # DeepSeek API调用（需要根据DeepSeek的具体API调整）
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一个专业的社交媒体内容创作专家，擅长为小红书等平台创作吸引人的内容。"},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"}
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        # 解析结果
        content = result["choices"][0]["message"]["content"]
        result_json = json.loads(content)
        return result_json["title"], result_json["body"]
    except Exception as e:
        print(f"DeepSeek API调用失败: {str(e)}")
        return "", ""

def generate_title(keyword, original_title):
    """使用规则生成优化标题"""
    title_templates = [
        f"【{keyword}测评】这款产品真的有那么神奇吗？",
        f"2024必入手的{keyword}｜亲测有效的使用心得",
        f"震惊！这款{keyword}竟然让我的肌肤/生活发生了这些变化",
        f"学生党/上班族必备{keyword}，平价又好用",
        f"我用过最好的{keyword}，效果竟然这么明显"
    ]
    
    # 如果原标题包含数字，尝试保留
    numbers = re.findall(r'\d+', original_title)
    if numbers and len(title_templates) > 2:
        title_templates[2] = f"{numbers[0]}款值得入手的{keyword}，第{min(int(numbers[0])//2+1, 5)}款太惊艳了"
    
    # 从模板中随机选择一个作为新标题
    return random.choice(title_templates)

def generate_body(keyword, original_text, top_posts):
    """使用规则生成优化正文"""
    # 提取原文的关键信息
    sentences = original_text.split('。')
    
    # 构建优化正文
    intro = f"大家好，今天给大家分享一款超级好用的{keyword}产品体验。\n\n"
    
    # 保留原文中的有效信息
    content_part = ""
    for s in sentences:
        if len(s) > 10 and not any(x in s for x in ["哈哈", "嘻嘻", "啊啊", "哇哇"]):
            content_part += s + "。\n"
    
    # 如果原文太短，加入一些常见评价词
    if len(content_part) < 100:
        content_part += f"\n这款{keyword}质地非常舒适，使用感很轻盈，效果也很显著。我已经连续使用了两周，真的能看到明显变化！"
    
    # 结论部分
    conclusion = f"\n\n总的来说，这款{keyword}非常值得入手，性价比很高，推荐给所有需要的小伙伴们！如果你也在使用，欢迎在评论区留言分享你的体验~"
    
    # 热门标签
    tags = "\n\n#" + keyword + " #好物推荐 #实用分享 #剁手清单 #测评"
    
    return intro + content_part + conclusion + tags

def generate_suggestions(content, ai_analysis=None):
    """生成内容改进建议，可选使用AI分析结果"""
    suggestions = []
    
    # 图片数量建议
    image_count = len(content["images"]) if "images" in content else 0
    if image_count < 3:
        suggestions.append(f"建议增加图片数量到3-5张，当前只有{image_count}张")
    elif image_count > 9:
        suggestions.append(f"图片数量({image_count})过多，建议精选3-9张最能展示产品特点的图片")
    
    # 文字长度建议
    text_length = len(content["text"]) if "text" in content else 0
    if text_length < 200:
        suggestions.append(f"文字内容较短({text_length}字)，建议扩充到300字以上，增加产品使用体验和效果描述")
    elif text_length > 1000:
        suggestions.append(f"文字内容较长({text_length}字)，建议精简，突出重点")
    
    # 视频建议
    if not content.get("video"):
        suggestions.append("建议添加短视频展示产品使用过程，提高互动率")
    
    # 发布时间建议
    suggestions.append("建议在晚上7点-10点发布，这个时间段用户活跃度高")
    
    # 互动建议
    suggestions.append('在正文结尾增加互动引导，如"你们觉得这款产品怎么样？"或"你们有什么好用的推荐吗？"')
    
    # 如果有AI分析结果，添加更具针对性的建议
    if ai_analysis:
        audience = ai_analysis.get("audience", "")
        if audience and "学生" in audience:
            suggestions.append("针对学生群体，可增加性价比和实用性方面的描述")
        
        tone = ai_analysis.get("tone", "")
        if tone and not any(word in tone.lower() for word in ["活泼", "热情", "积极"]):
            suggestions.append("小红书内容风格偏向活泼，建议增加一些表情符号和生动的描述")
    
    return suggestions

def format_output(content, analysis, optimized):
    """
    格式化输出结果
    
    Args:
        content: 原始内容
        analysis: 分析结果
        optimized: 优化内容
        
    Returns:
        dict: 完整结果
    """
    result = {
        "original": content,
        "analysis": {
            "keywords": analysis["keywords"],
            "top_posts": [{"url": p["url"], "title": p["title"], "likes": p["likes"]} for p in analysis["top_posts"]]
        },
        "optimized": {
            "title": optimized["title"],
            "body": optimized["body"],
            "suggestions": optimized["suggestions"]
        }
    }
    
    # 如果有AI分析，添加到结果中
    if "ai_analysis" in analysis:
        result["analysis"]["ai_analysis"] = analysis["ai_analysis"]
    
    # 如果有媒体分析，添加到结果中
    if "media_analysis" in analysis:
        # 处理图片分析结果，移除base64编码以减小输出大小
        if "image_analyses" in analysis["media_analysis"]:
            simplified_img_analyses = []
            for img in analysis["media_analysis"]["image_analyses"]:
                if "error" in img:
                    simplified_img_analyses.append({"error": img["error"]})
                else:
                    simplified_img_analyses.append({
                        "content": img.get("content", ""),
                        "objects": img.get("objects", []),
                        "style": img.get("style", ""),
                        "quality": img.get("quality", 0),
                        "appeal": img.get("appeal", 0),
                        "keywords": img.get("keywords", []),
                        "ai_service": img.get("ai_service", "")
                    })
            result["analysis"]["media_analysis"] = {"image_analyses": simplified_img_analyses}
        
        # 处理视频分析结果
        if "video_analysis" in analysis["media_analysis"]:
            video = analysis["media_analysis"]["video_analysis"]
            if "error" in video:
                result["analysis"]["media_analysis"]["video_analysis"] = {"error": video["error"]}
            else:
                result["analysis"]["media_analysis"]["video_analysis"] = {
                    "content": video.get("content", ""),
                    "objects": video.get("objects", []),
                    "keywords": video.get("keywords", []),
                    "quality": video.get("quality", 0),
                    "appeal": video.get("appeal", 0),
                    "frame_count": video.get("frame_count", 0),
                    "ai_service": video.get("ai_service", "")
                }
    
    return result

def main(url=None):
    """
    主函数
    
    Args:
        url: 小红书帖子URL
        
    Returns:
        dict: 完整结果
    """
    if not url:
        url = input("请输入小红书帖子URL: ")
    
    # 显示AI集成状态
    if USE_DEEPSEEK:
        print("使用DeepSeek API进行内容分析和生成")
    elif USE_OPENAI:
        print("使用OpenAI API进行内容分析和生成")
    else:
        print("使用规则方法进行内容分析和生成")
    
    # 抓取内容
    content = fetch_post_content(url)
    
    # 分析内容
    analysis = analyze_content(content)
    
    # 生成优化内容
    optimized = generate_optimized_content(content, analysis)
    
    # 输出结果
    result = format_output(content, analysis, optimized)
    return result

def fetch_top_posts(keyword, max_posts=10):
    """
    爬取指定关键词的热门帖子
    
    Args:
        keyword: 搜索关键词
        max_posts: 最大爬取帖子数量
        
    Returns:
        list: 热门帖子列表
    """
    # 构建搜索URL，编码关键词
    encoded_keyword = quote(keyword)
    search_url = f"https://www.xiaohongshu.com/search_result?keyword={encoded_keyword}&source=web"
    
    headers = get_enhanced_headers(referer=search_url)
    cookies = get_cookies()  # Get default cookies
    
    try:
        # 添加随机延迟
        add_random_delay(1.5, 3.5)
        
        # 可选：使用代理
        # proxies = {"http": get_random_proxy(), "https": get_random_proxy()} if get_random_proxy() else None
        
        # 发起请求
        # response = requests.get(search_url, headers=headers, cookies=cookies, proxies=proxies, timeout=15)
        response = requests.get(search_url, headers=headers, cookies=cookies, timeout=15)
        response.raise_for_status()
        
        # 解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 尝试多种选择器找到帖子容器
        posts_container = soup.select('div.note-list section') or soup.select('div.items-wrapper div.item') or soup.select('div.feeds-container div.note-item')
        
        if not posts_container:
            # 如果找不到帖子，检查是否有反爬信息
            if "验证" in soup.text or "校验" in soup.text or "captcha" in soup.text.lower():
                print("检测到可能的反爬验证，使用备选方法...")
                # 尝试备选选择器
                posts_container = soup.select('div.search-container div.note-item') or soup.select('div.content div.note-item')
                
                if not posts_container:
                return fetch_top_posts_api(keyword, max_posts)
            else:
                print("未找到帖子容器，尝试使用备选方式...")
                # 尝试一次不同的UA和请求参数
                alternative_headers = get_enhanced_headers()
                alternative_headers["User-Agent"] = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
                
                add_random_delay(1, 3)
                alternative_url = f"https://www.xiaohongshu.com/search_result/xhs/search?keyword={encoded_keyword}&sort=general&page=1"
                alternative_response = requests.get(alternative_url, headers=alternative_headers, cookies=cookies, timeout=15)
                
                if alternative_response.status_code == 200:
                    alternative_soup = BeautifulSoup(alternative_response.text, 'html.parser')
                    posts_container = alternative_soup.select('div.note-list section') or alternative_soup.select('div.items-wrapper div.item')
                
                if not posts_container:
                return fetch_top_posts_api(keyword, max_posts)
        
        results = []
        for post in posts_container[:max_posts]:
            # 尝试不同选择器提取标题、链接和点赞数
            title_elem = post.select_one('div.note-info h3') or post.select_one('div.note-content div.title') or post.select_one('div.note-desc')
            link_elem = post.select_one('a') or post.select_one('div.note-content a')
            likes_elem = post.select_one('span.like-count') or post.select_one('div.note-metrics span.like')
            
            title = title_elem.text.strip() if title_elem else "未找到标题"
            post_url = "https://www.xiaohongshu.com" + link_elem['href'] if link_elem and 'href' in link_elem.attrs else "#"
            likes = int(likes_elem.text.replace('赞', '').strip()) if likes_elem else 0
            
            # 如果找不到点赞数，尝试使用顺序作为权重
            if likes == 0:
                likes = max_posts - len(results)
            
            results.append({
                "url": post_url,
                "title": title,
                "likes": likes
            })
            
        # 按点赞数排序
        results.sort(key=lambda x: x["likes"], reverse=True)
        return results[:max_posts]
    
    except Exception as e:
        print(f"直接爬取搜索结果失败: {str(e)}")
        # 尝试使用API方法
        return fetch_top_posts_api(keyword, max_posts)

def fetch_top_posts_api(keyword, max_posts=10):
    """
    使用小红书搜索API获取热门帖子
    
    Args:
        keyword: 搜索关键词
        max_posts: 最大爬取帖子数量
        
    Returns:
        list: 热门帖子列表
    """
    print("使用API方式获取热门帖子...")
    
    try:
        # 添加随机延迟
        add_random_delay(2, 4)
        
        # 获取cookies
        cookies = get_cookies()
        
        # 尝试使用新版API端点
        timestamp = int(time.time() * 1000)
        sign = hashlib.md5(f"keyword={keyword}&source=web&t={timestamp}".encode()).hexdigest()
        
        api_url = "https://www.xiaohongshu.com/api/sns/web/v1/search/notes"
        params = {
            "keyword": keyword,
            "source": "web",
            "t": timestamp,
            "sign": sign,
            "page": 1,
            "page_size": max_posts,
            "sort": "general",  # general, popularity, time
        }
        
        headers = get_enhanced_headers(referer=f"https://www.xiaohongshu.com/search_result?keyword={quote(keyword)}", is_api=True)
        
        # 可选：使用代理
        # proxies = {"http": get_random_proxy(), "https": get_random_proxy()} if get_random_proxy() else None
        # response = requests.get(api_url, params=params, headers=headers, cookies=cookies, proxies=proxies, timeout=15)
        
        response = requests.get(api_url, params=params, headers=headers, cookies=cookies, timeout=15)
        
        # 检查状态码，如果是500等服务器错误，尝试替代API接口
        if response.status_code >= 400:
            print(f"API请求失败，状态码: {response.status_code}，尝试备用API")
            
            # 尝试备用API接口
            add_random_delay(1, 2)
            alternative_api_url = "https://www.xiaohongshu.com/api/sns/web/v1/search/notes_category"
            alternative_params = {
                "keyword": keyword,
                "page": 1,
                "page_size": max_posts,
                "sort": "general",
                "t": int(time.time() * 1000)
            }
            
            # 使用不同的UA和请求头
            alternative_headers = get_enhanced_headers(is_api=True)
            alternative_headers["User-Agent"] = get_random_user_agent()
            
            alternative_response = requests.get(
                alternative_api_url, 
                params=alternative_params, 
                headers=alternative_headers,
                cookies=cookies,
                timeout=15
            )
            
            if alternative_response.status_code >= 400:
                print(f"备用API也请求失败，状态码: {alternative_response.status_code}，直接使用模拟数据")
            return generate_mock_top_posts(keyword if isinstance(keyword, list) else [keyword])
                
            response = alternative_response
            
        response.raise_for_status()
        data = response.json()
        
        if data.get("success") and data.get("data") and data["data"].get("notes"):
            results = []
            for note in data["data"]["notes"][:max_posts]:
                title = note.get("title", "未找到标题")
                post_id = note.get("id", "")
                post_url = f"https://www.xiaohongshu.com/discovery/item/{post_id}" if post_id else "#"
                likes = note.get("likes", 0) or note.get("liked_count", 0)
                
                # 如果找不到点赞数，尝试使用顺序作为权重
                if likes == 0:
                    likes = max_posts - len(results)
                
                results.append({
                    "url": post_url,
                    "title": title,
                    "likes": likes
                })
            
            # 按点赞数排序
            results.sort(key=lambda x: x["likes"], reverse=True)
            return results[:max_posts]
        else:
            print("API返回数据结构异常，使用模拟数据")
            return generate_mock_top_posts(keyword if isinstance(keyword, list) else [keyword])
            
    except Exception as e:
        print(f"API获取热门帖子失败: {str(e)}")
        # 直接返回模拟数据而不抛出异常
        return generate_mock_top_posts(keyword if isinstance(keyword, list) else [keyword])

def generate_mock_top_posts(keywords):
    """生成模拟热门帖子数据（当爬取失败时使用）"""
    keyword = keywords[0] if keywords and isinstance(keywords, list) else keywords
    if not isinstance(keyword, str):
        keyword = "好物"
    
    return [
        {"url": "https://www.xiaohongshu.com/discovery/item/example1", "title": f"2024年最受欢迎的{keyword}推荐", "likes": 5200},
        {"url": "https://www.xiaohongshu.com/discovery/item/example2", "title": f"测评|这些{keyword}到底值不值得买？", "likes": 4800},
        {"url": "https://www.xiaohongshu.com/discovery/item/example3", "title": f"「干货分享」我的{keyword}使用心得", "likes": 4300},
        {"url": "https://www.xiaohongshu.com/discovery/item/example4", "title": f"学生党必备{keyword}，真的太划算了", "likes": 3900},
        {"url": "https://www.xiaohongshu.com/discovery/item/example5", "title": f"入手三个月后，我对这款{keyword}的真实评价", "likes": 3600},
        {"url": "https://www.xiaohongshu.com/discovery/item/example6", "title": f"我用过最好用的{keyword}推荐给你们", "likes": 3200},
        {"url": "https://www.xiaohongshu.com/discovery/item/example7", "title": f"当代女生必入的{keyword}，第三个被安利疯了", "likes": 3000},
        {"url": "https://www.xiaohongshu.com/discovery/item/example8", "title": f"{keyword}大赏|这几款小众但超好用", "likes": 2800},
        {"url": "https://www.xiaohongshu.com/discovery/item/example9", "title": f"囤货季|这些{keyword}我已经买第三次了", "likes": 2500},
        {"url": "https://www.xiaohongshu.com/discovery/item/example10", "title": f"平价{keyword}推荐，绝对不踩雷", "likes": 2300}
    ]

if __name__ == "__main__":
    result = main()
    print(json.dumps(result, ensure_ascii=False, indent=2)) 