import os
import re
import json
import time
import random
import requests
from bs4 import BeautifulSoup
import hashlib
from urllib.parse import quote
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('xiaohongshu_scraper.log', encoding='utf-8')
    ]
)
logger = logging.getLogger('xiaohongshu_scraper')

# 反爬工具类
class AntiCrawlUtils:
    # 用户代理列表
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
        "Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0"
    ]

    # 默认cookies (将在运行时更新)
    DEFAULT_COOKIES = {
        "webId": "6fae921e8ce000000000",
        "a1": "18f6513c3f8c4xdvf16t5v444mymj5jpj44231infx50000278721",
        "web_session": "_id.45kfd93j3k2fdsa"
    }

    # 代理列表 (取消注释并填入实际代理地址使用)
    PROXY_LIST = [
        # "http://proxy1.example.com:8080",
        # "http://proxy2.example.com:8080",
        # "http://proxy3.example.com:8080",
    ]

    # 存储cookies，多个域名分别存储
    _cookies_store = {
        "www.xiaohongshu.com": DEFAULT_COOKIES.copy()
    }

    # 上次请求时间记录，用于请求间隔控制
    _last_request_time = 0

    # 代理索引
    _proxy_index = -1
    
    # 重试计数
    _retry_count = {}

    @classmethod
    def get_random_user_agent(cls):
        """返回随机用户代理"""
        return random.choice(cls.USER_AGENTS)

    @classmethod
    def get_next_proxy(cls):
        """轮询方式获取下一个代理"""
        if not cls.PROXY_LIST:
            return None
            
        cls._proxy_index = (cls._proxy_index + 1) % len(cls.PROXY_LIST)
        return cls.PROXY_LIST[cls._proxy_index]

    @classmethod
    def get_proxies(cls):
        """获取代理设置"""
        proxy = cls.get_next_proxy()
        if not proxy:
            return None
        return {"http": proxy, "https": proxy}

    @classmethod
    def add_random_delay(cls, min_seconds=1.0, max_seconds=3.0, jitter=0.5):
        """添加随机延迟，避免被检测为机器人
        
        Args:
            min_seconds: 最小延迟秒数
            max_seconds: 最大延迟秒数
            jitter: 抖动范围 (0-1)，增加随机性
        """
        # 计算自上次请求以来的时间
        now = time.time()
        elapsed = now - cls._last_request_time
        
        # 如果距离上次请求时间太短，增加等待时间
        if elapsed < min_seconds:
            min_seconds = max(min_seconds, min_seconds - elapsed)
        else:
            # 已经等待足够长的时间，可以减少等待
            min_seconds = max(0.2, min_seconds * 0.8)
        
        # 添加抖动避免固定模式
        jitter_value = random.uniform(-jitter, jitter)
        max_with_jitter = max_seconds * (1 + jitter_value)
        min_with_jitter = min_seconds * (1 - jitter_value * 0.5)  # 最小值抖动较小
        
        delay = random.uniform(min_with_jitter, max_with_jitter)
        time.sleep(delay)
        
        # 更新最后请求时间
        cls._last_request_time = time.time()
        return delay

    @classmethod
    def get_enhanced_headers(cls, referer=None, is_api=False):
        """获取增强的请求头，更好地模拟真实浏览器
        
        Args:
            referer: 来源URL
            is_api: 是否为API请求
        """
        user_agent = cls.get_random_user_agent()
        
        # 通用请求头
        headers = {
            "User-Agent": user_agent,
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Microsoft Edge";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Site": "same-origin",
            "Cache-Control": "max-age=0",
            "Upgrade-Insecure-Requests": "1"
        }
        
        # 添加随机客户端提示
        if random.random() > 0.5:
            headers["Sec-CH-UA-Bitness"] = random.choice(["64"])
            headers["Sec-CH-UA-Model"] = '""'
            headers["Sec-CH-UA-Full-Version-List"] = random.choice([
                '"Microsoft Edge";v="120.0.2210.121", "Not?A_Brand";v="8.0.0.0", "Chromium";v="120.0.6099.119"',
                '"Google Chrome";v="120.0.6099.119", "Not?A_Brand";v="8.0.0.0", "Chromium";v="120.0.6099.119"'
            ])

        # 添加 DNT (Do Not Track) 随机值
        if random.random() > 0.7:
            headers["DNT"] = "1"
            
        # 添加Referer如果提供
        if referer:
            headers["Referer"] = referer
        else:
            headers["Referer"] = "https://www.xiaohongshu.com/"
        
        # API特定请求头
        if is_api:
            headers.update({
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json;charset=UTF-8",
                "Origin": "https://www.xiaohongshu.com",
                "X-Requested-With": "XMLHttpRequest",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors"
            })
        else:
            headers.update({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate"
            })
            
            # 随机添加其他浏览器会发送的请求头
            if random.random() > 0.6:
                headers["Accept-CH"] = "Sec-CH-UA-Arch, Sec-CH-UA-Bitness, Sec-CH-UA-Full-Version-List, Sec-CH-UA-Mobile, Sec-CH-UA-Model, Sec-CH-UA-Platform, Sec-CH-UA-Platform-Version"
                
        return headers

    @classmethod
    def parse_cookies_string(cls, cookies_str):
        """解析cookies字符串为字典"""
        if not cookies_str:
            return {}
        
        cookies = {}
        for item in cookies_str.split(';'):
            if '=' in item:
                name, value = item.strip().split('=', 1)
                cookies[name] = value
        return cookies

    @classmethod
    def get_cookies(cls, domain="www.xiaohongshu.com", custom_cookies_str=None):
        """获取cookies，结合默认和自定义cookies
        
        Args:
            domain: 域名
            custom_cookies_str: 自定义cookies字符串
        """
        # 确保域名存在于存储中
        if domain not in cls._cookies_store:
            cls._cookies_store[domain] = cls.DEFAULT_COOKIES.copy()
            
        cookies = cls._cookies_store[domain].copy()
        
        # 如果提供了自定义cookies，合并
        if custom_cookies_str:
            custom_cookies = cls.parse_cookies_string(custom_cookies_str)
            cookies.update(custom_cookies)
        
        return cookies

    @classmethod
    def update_cookies(cls, domain, response):
        """从响应中更新cookies
        
        Args:
            domain: 域名
            response: 请求响应对象
        """
        if not response or not response.cookies:
            return
            
        # 确保域名存在于存储中
        if domain not in cls._cookies_store:
            cls._cookies_store[domain] = cls.DEFAULT_COOKIES.copy()
            
        # 更新cookies
        for key, value in response.cookies.items():
            cls._cookies_store[domain][key] = value
            
        # 记录cookies更新
        logger.info(f"Updated cookies for {domain}, now has {len(cls._cookies_store[domain])} keys")

    @classmethod
    def make_request(cls, url, method="GET", params=None, data=None, json_data=None, 
                    headers=None, cookies=None, timeout=15, allow_redirects=True, 
                    max_retries=3, backoff_factor=2, retry_status_codes=None):
        """执行HTTP请求，包含指数退避重试
        
        Args:
            url: 请求URL
            method: 请求方法，GET/POST等
            params: URL参数
            data: 表单数据
            json_data: JSON数据
            headers: 请求头
            cookies: cookies
            timeout: 超时时间（秒）
            allow_redirects: 是否允许重定向
            max_retries: 最大重试次数
            backoff_factor: 退避因子
            retry_status_codes: 需要重试的HTTP状态码，默认[429, 500, 502, 503, 504]
        
        Returns:
            requests.Response对象
        """
        if retry_status_codes is None:
            retry_status_codes = [429, 500, 502, 503, 504]
            
        # 提取域名
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        # 如果没有提供cookies，使用存储的cookies
        if cookies is None:
            cookies = cls.get_cookies(domain)
            
        # 如果没有提供请求头，生成增强的请求头
        if headers is None:
            is_api = "api" in url or method != "GET"
            headers = cls.get_enhanced_headers(referer=url, is_api=is_api)
            
        # 获取代理（如已配置）
        proxies = cls.get_proxies()
        
        # 重试计数器键
        retry_key = f"{method}:{url}"
        if retry_key not in cls._retry_count:
            cls._retry_count[retry_key] = 0
        
        logger.info(f"Making {method} request to {url}")
        
        for attempt in range(max_retries):
            try:
                # 添加随机延迟，重试次数越多延迟越长
                jitter = 0.2 * (attempt + 1)
                delay_min = 1 + attempt * backoff_factor
                delay_max = 3 + attempt * backoff_factor * 1.5
                cls.add_random_delay(delay_min, delay_max, jitter)
                
                # 执行请求
                response = requests.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    json=json_data,
                    headers=headers,
                    cookies=cookies,
                    proxies=proxies,
                    timeout=timeout,
                    allow_redirects=allow_redirects
                )
                
                # 更新cookies
                cls.update_cookies(domain, response)
                
                # 如果状态码需要重试
                if response.status_code in retry_status_codes:
                    logger.warning(f"Attempt {attempt+1}/{max_retries}: Received status code {response.status_code}, retrying...")
                    
                    # 如果返回429 (Too Many Requests)，增加更长的延迟
                    if response.status_code == 429:
                        wait_time = 5 + attempt * 3
                        logger.warning(f"Rate limited (429). Waiting {wait_time} seconds before retry.")
                        time.sleep(wait_time)
                        
                        # 尝试切换用户代理和代理
                        headers["User-Agent"] = cls.get_random_user_agent()
                        if cls.PROXY_LIST:
                            proxies = cls.get_proxies()
                            
                    continue
                
                # 重置重试计数
                cls._retry_count[retry_key] = 0
                
                # 返回成功的响应
                return response
                
            except (requests.RequestException, IOError) as e:
                logger.error(f"Attempt {attempt+1}/{max_retries}: Request failed: {str(e)}")
                
                if attempt < max_retries - 1:
                    wait_time = (backoff_factor ** attempt) * 2
                    logger.info(f"Waiting {wait_time:.1f} seconds before retry")
                    time.sleep(wait_time)
                else:
                    # 增加重试计数
                    cls._retry_count[retry_key] += 1
                    
                    # 如果重试次数过多，清除重试计数并抛出异常
                    if cls._retry_count[retry_key] >= 3:
                        cls._retry_count[retry_key] = 0
                        raise Exception(f"Maximum retries exceeded for {url}")
                    
                    # 抛出异常
                    raise

# 使用工具类代替之前的工具函数
def get_random_user_agent():
    """返回随机用户代理"""
    return AntiCrawlUtils.get_random_user_agent()

def add_random_delay(min_seconds=1, max_seconds=3):
    """添加随机延迟，避免被检测"""
    return AntiCrawlUtils.add_random_delay(min_seconds, max_seconds)

def get_enhanced_headers(referer=None, is_api=False):
    """获取增强的请求头"""
    return AntiCrawlUtils.get_enhanced_headers(referer, is_api)

def parse_cookies_string(cookies_str):
    """解析cookies字符串为字典"""
    return AntiCrawlUtils.parse_cookies_string(cookies_str)

def get_cookies(custom_cookies_str=None):
    """获取cookies，结合默认和自定义cookies"""
    return AntiCrawlUtils.get_cookies(custom_cookies_str=custom_cookies_str)

# 尝试导入媒体分析模块
try:
    import media_analyzer
    MEDIA_ANALYSIS_AVAILABLE = True
except ImportError:
    MEDIA_ANALYSIS_AVAILABLE = False

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
                    except:
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
                    except:
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
                    except:
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
    try:
        # 模拟移动设备
        mobile_headers = get_enhanced_headers(referer=url, is_api=False)
        mobile_headers["User-Agent"] = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
        
        response = AntiCrawlUtils.make_request(
            url=url,
            headers=mobile_headers,
            timeout=15,
            max_retries=4
        )
        
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
        logger.error(f"备选方法抓取失败: {str(e)}，使用手动输入提示")
        # 如果备选方法也失败，直接返回空结果
        # 调用方应检查结果是否为空并提示用户手动输入
        return {
            "title": "未找到标题",
            "text": "未找到内容，请手动输入",
            "images": [],
            "video": None
        }

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
    
    try:
        # 使用增强的请求方法
        response = AntiCrawlUtils.make_request(
            url=search_url, 
            headers=headers,
            timeout=15
        )
        
        # 解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 尝试多种选择器找到帖子容器
        posts_container = soup.select('div.note-list section') or soup.select('div.items-wrapper div.item') or soup.select('div.feeds-container div.note-item')
        
        if not posts_container:
            # 如果找不到帖子，检查是否有反爬信息
            if "验证" in soup.text or "校验" in soup.text or "captcha" in soup.text.lower():
                logger.warning("检测到可能的反爬验证，使用备选方法...")
                # 尝试备选选择器
                posts_container = soup.select('div.search-container div.note-item') or soup.select('div.content div.note-item')
                
                if not posts_container:
                    return fetch_top_posts_api(keyword, max_posts)
            else:
                logger.warning("未找到帖子容器，尝试使用备选方式...")
                # 尝试一次不同的UA和请求参数
                alternative_headers = get_enhanced_headers()
                alternative_headers["User-Agent"] = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
                
                alternative_url = f"https://www.xiaohongshu.com/search_result/xhs/search?keyword={encoded_keyword}&sort=general&page=1"
                
                alternative_response = AntiCrawlUtils.make_request(
                    url=alternative_url,
                    headers=alternative_headers,
                    timeout=15
                )
                
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
        logger.error(f"直接爬取搜索结果失败: {str(e)}")
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
    logger.info("使用API方式获取热门帖子...")
    
    try:
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
        
        # 使用增强的请求方法
        response = AntiCrawlUtils.make_request(
            url=api_url,
            method="GET", 
            params=params,
            headers=headers,
            timeout=15
        )
        
        # 检查状态码，如果是500等服务器错误，尝试替代API接口
        if response.status_code >= 400:
            logger.warning(f"API请求失败，状态码: {response.status_code}，尝试备用API")
            
            # 尝试备用API接口
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
            
            alternative_response = AntiCrawlUtils.make_request(
                url=alternative_api_url,
                method="GET", 
                params=alternative_params,
                headers=alternative_headers,
                timeout=15,
                max_retries=4
            )
            
            if alternative_response.status_code >= 400:
                logger.warning(f"备用API也请求失败，状态码: {alternative_response.status_code}，直接使用模拟数据")
                return generate_mock_top_posts(keyword if isinstance(keyword, list) else [keyword])
                
            response = alternative_response
        
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
            logger.warning("API返回数据结构异常，使用模拟数据")
            return generate_mock_top_posts(keyword if isinstance(keyword, list) else [keyword])
            
    except Exception as e:
        logger.error(f"API获取热门帖子失败: {str(e)}")
        # 直接返回模拟数据而不抛出异常
        return generate_mock_top_posts(keyword if isinstance(keyword, list) else [keyword])

def generate_mock_top_posts(keywords):
    """生成模拟的热门帖子数据"""
    mock_data = []
    
    # 确保有关键词可用
    if not keywords or len(keywords) == 0:
        keywords = ["小红书", "好物", "推荐"]
    
    # 如果是字符串，转换为列表
    if isinstance(keywords, str):
        keywords = [keywords]
    
    # 获取主要关键词（第一个）和次要关键词
    main_keyword = keywords[0]
    secondary_keywords = keywords[1:] if len(keywords) > 1 else ["推荐", "分享"]
    
    # 生成相关的、个性化的热门帖子标题
    titles = [
        f"{main_keyword}必看｜分享我的{secondary_keywords[0] if len(secondary_keywords) > 0 else '使用'}心得",
        f"我试过最好的{main_keyword}，推荐给每个{secondary_keywords[-1] if len(secondary_keywords) > 0 else '朋友'}",
        f"震惊！这个{main_keyword}居然这么{secondary_keywords[0] if len(secondary_keywords) > 0 else '好用'}",
        f"{main_keyword}使用攻略｜从小白到专家",
        f"年度必入｜{main_keyword}种草清单",
        f"我为什么推荐{main_keyword}给所有人",
        f"{main_keyword}｜让你的生活更美好",
        f"破解{main_keyword}的秘密，这篇就够了"
    ]
    
    # 根据关键词随机选择一些标题
    import random
    selected_titles = random.sample(titles, min(5, len(titles)))
    
    # 生成不同的点赞数
    for i, title in enumerate(selected_titles):
        likes = random.randint(800, 10000)
        
        mock_data.append({
            "url": f"https://www.xiaohongshu.com/explore/example{i+1}",
            "title": title,
            "likes": likes
        })
    
    # 按点赞数排序
    mock_data.sort(key=lambda x: x["likes"], reverse=True)
    
    return mock_data

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
    
    # 使用关键词生成优化标题
    keyword = keywords[0] if keywords else "好物"
    optimized_title = generate_title(keyword, original_title)
    
    # 优化正文
    optimized_body = generate_body(keyword, original_text, top_posts)
    
    # 生成内容改进建议
    suggestions = generate_suggestions(content, top_posts)
    
    # 如果有媒体分析建议，添加到改进建议中
    if "media_analysis" in analysis and "suggestions" in analysis["media_analysis"]:
        media_suggestions = analysis["media_analysis"]["suggestions"]
        suggestions.extend(media_suggestions)
    
    return {
        "title": optimized_title,
        "body": optimized_body,
        "suggestions": suggestions
    }

def generate_title(keyword, original_title):
    """生成优化标题"""
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
    """生成优化正文"""
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

def generate_suggestions(content, top_posts):
    """生成内容改进建议"""
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
    
    # 如果有媒体分析，添加到结果中
    if "media_analysis" in analysis:
        result["analysis"]["media_analysis"] = analysis["media_analysis"]
    
    return result

def manual_input():
    """用户手动输入内容"""
    logger.info("抓取失败，提示用户手动输入内容")
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
    
    # 记录开始分析
    logger.info(f"开始分析内容: 标题={title[:20]}...")
    
    # 简单关键词提取
    keywords = extract_simple_keywords(title + " " + text)
    logger.info(f"提取关键词: {keywords}")
    
    # 尝试爬取相关热门帖子
    try:
        top_posts = fetch_top_posts(keywords[0] if keywords else "好物推荐")
    except Exception as e:
        logger.error(f"爬取热门帖子失败: {str(e)}")
        # 爬取失败时使用模拟数据
        top_posts = generate_mock_top_posts(keywords)
    
    # 创建结果字典
    result = {
        "keywords": keywords, 
        "top_posts": top_posts
    }
    
    # 分析图片和视频内容(如果可用)
    if MEDIA_ANALYSIS_AVAILABLE:
        logger.info("媒体分析模块可用，开始分析媒体内容")
        # 使用增强的媒体分析
        try:
            # 图片分析
            media_analysis = {}
            
            # 对图片进行分析
            if content.get("images"):
                images = content["images"]
                image_count = len(images)
                logger.info(f"分析 {image_count} 张图片")
                
                # 图片数量建议
                media_suggestions = []
                if image_count < 3:
                    media_suggestions.append(f"当前仅有{image_count}张图片，建议增加到3-9张，展示更多产品细节")
                elif image_count > 9:
                    media_suggestions.append(f"图片数量({image_count})偏多，建议精选3-9张最具代表性的图片")
                
                # 尝试执行更深入的图片分析
                try:
                    # 限制分析图片数量，避免过度请求
                    max_analyze_images = min(image_count, 3)
                    image_results = []
                    
                    # 使用媒体分析模块分析图片
                    for i in range(max_analyze_images):
                        img_url = images[i]
                        logger.info(f"分析图片 {i+1}/{max_analyze_images}: {img_url[:50]}...")
                        
                        try:
                            # 分析图片内容
                            img_analysis = media_analyzer.analyze_image(img_url)
                            
                            # 如果分析失败，使用基本分析结果
                            if "error" in img_analysis:
                                logger.warning(f"图片 {i+1} 分析失败: {img_analysis['error']}")
                                continue
                                
                            image_results.append(img_analysis)
                        except Exception as img_err:
                            logger.error(f"图片 {i+1} 分析异常: {str(img_err)}")
                    
                    # 如果至少有一张图片分析成功
                    if image_results:
                        # 提取图片质量评分和吸引力评分
                        avg_quality = sum(result.get("quality", 0) for result in image_results) / len(image_results)
                        avg_appeal = sum(result.get("appeal", 0) for result in image_results) / len(image_results)
                        
                        # 提取共同关键词
                        image_keywords = set()
                        for result in image_results:
                            if "keywords" in result:
                                image_keywords.update(result["keywords"])
                        
                        # 只保留顶部5个关键词
                        top_image_keywords = list(image_keywords)[:5]
                        
                        # 添加图片质量建议
                        if avg_quality < 6:
                            media_suggestions.append(f"图片质量评分较低 ({avg_quality:.1f}/10)，建议提高图片清晰度和光线")
                        if avg_appeal < 6:
                            media_suggestions.append(f"图片吸引力评分较低 ({avg_appeal:.1f}/10)，建议优化构图和主题突出度")
                        
                        # 保存图片分析结果
                        media_analysis["image_analysis"] = {
                            "quality": round(avg_quality, 1),
                            "appeal": round(avg_appeal, 1),
                            "keywords": top_image_keywords
                        }
                except Exception as image_analysis_err:
                    logger.error(f"高级图片分析失败: {str(image_analysis_err)}")
            else:
                media_suggestions = ["未检测到图片，建议添加产品图片以增强内容可视化效果"]
            
            # 视频分析
            if content.get("video"):
                video_url = content["video"]
                logger.info(f"开始分析视频: {video_url[:50]}...")
                
                try:
                    # 分析视频内容
                    video_analysis = media_analyzer.analyze_video(video_url)
                    
                    # 如果分析成功
                    if "quality" in video_analysis:
                        # 添加视频质量建议
                        if video_analysis["quality"] < 6:
                            media_suggestions.append(f"视频质量评分较低 ({video_analysis['quality']}/10)，建议提高视频清晰度和稳定性")
                        if video_analysis["appeal"] < 6:
                            media_suggestions.append(f"视频吸引力评分较低 ({video_analysis['appeal']}/10)，建议优化内容叙事和视觉效果")
                            
                        # 添加视频关键词
                        if "keywords" in video_analysis:
                            # 获取所有关键词
                            all_keywords = set(keywords)
                            video_keywords = set(video_analysis.get("keywords", []))
                            
                            # 找出视频关键词中未包含在文本关键词中的
                            new_keywords = video_keywords - all_keywords
                            if new_keywords:
                                media_suggestions.append(f"视频包含额外关键词: {', '.join(new_keywords)}，建议在正文中适当提及")
                        
                        # 保存视频分析结果
                        media_analysis["video_analysis"] = {
                            "quality": video_analysis["quality"],
                            "appeal": video_analysis["appeal"],
                            "keywords": video_analysis.get("keywords", [])[:5],
                            "frame_count": video_analysis.get("frame_count", 0)
                        }
                except Exception as video_err:
                    logger.error(f"视频分析失败: {str(video_err)}")
                    media_suggestions.append("检测到视频但无法解析，请确保视频格式正确并可公开访问")
            else:
                media_suggestions.append("未检测到视频，建议添加产品使用视频，可以展示实际效果和使用方法")
            
            # 添加综合建议
            if len(content.get("images", [])) > 0 and not content.get("video"):
                media_suggestions.append("建议将最具特色的一张图片制作成短视频，增加内容多样性")
            
            # 添加分析结果
            media_analysis["suggestions"] = media_suggestions
            result["media_analysis"] = media_analysis
            
        except Exception as media_err:
            logger.error(f"媒体分析总体失败: {str(media_err)}")
            # 基础分析作为备用
            media_suggestions = []
            
            # 图片基础分析
            if content.get("images"):
                image_count = len(content["images"])
                if image_count < 3:
                    media_suggestions.append(f"当前仅有{image_count}张图片，建议增加到3-9张，展示更多产品细节")
                elif image_count > 9:
                    media_suggestions.append(f"图片数量({image_count})偏多，建议精选3-9张最具代表性的图片")
            else:
                media_suggestions.append("未检测到图片，建议添加产品图片以增强内容可视化效果")
            
            # 视频基础分析
            if not content.get("video"):
                media_suggestions.append("未检测到视频，建议添加产品使用视频，可以展示实际效果和使用方法")
            
            result["media_analysis"] = {
                "suggestions": media_suggestions
            }
    else:
        logger.warning("媒体分析模块不可用，跳过媒体分析")
    
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
    
    # 抓取内容
    content = fetch_post_content(url)
    
    # 分析内容
    analysis = analyze_content(content)
    
    # 生成优化内容
    optimized = generate_optimized_content(content, analysis)
    
    # 输出结果
    result = format_output(content, analysis, optimized)
    return result

if __name__ == "__main__":
    result = main()
    print(json.dumps(result, ensure_ascii=False, indent=2)) 