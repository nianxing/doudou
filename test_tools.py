import requests
import time
import random
import json
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_tools')

# 用户代理列表
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15"
]

def get_random_user_agent():
    """返回随机用户代理"""
    return random.choice(USER_AGENTS)

def add_random_delay(min_seconds=1.0, max_seconds=3.0, jitter=0.5):
    """添加随机延迟，避免被检测为机器人"""
    # 添加抖动避免固定模式
    jitter_value = random.uniform(-jitter, jitter)
    max_with_jitter = max_seconds * (1 + jitter_value)
    min_with_jitter = min_seconds * (1 - jitter_value * 0.5)
    
    delay = random.uniform(min_with_jitter, max_with_jitter)
    logger.info(f"添加随机延迟 {delay:.2f} 秒")
    time.sleep(delay)
    return delay

def get_enhanced_headers(referer=None, is_api=False):
    """获取增强的请求头，更好地模拟真实浏览器"""
    user_agent = get_random_user_agent()
    
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
    
    return headers

def make_request(url, method="GET", params=None, headers=None, cookies=None, 
                timeout=15, max_retries=3, retry_delay=2):
    """安全的发送请求，处理重试和错误"""
    if headers is None:
        is_api = "api" in url
        headers = get_enhanced_headers(url, is_api)
    
    for attempt in range(max_retries):
        try:
            # 添加随机延迟，重试次数越多延迟越长
            add_random_delay(1 + attempt * 0.5, 3 + attempt)
            
            # 发送请求
            logger.info(f"发送请求: {url}")
            response = requests.request(
                method=method,
                url=url,
                params=params,
                headers=headers,
                cookies=cookies,
                timeout=timeout
            )
            
            # 处理429状态码 (Too Many Requests)
            if response.status_code == 429:
                wait_time = retry_delay * (2 ** attempt)
                logger.warning(f"收到429响应，等待{wait_time}秒后重试...")
                time.sleep(wait_time)
                headers["User-Agent"] = get_random_user_agent()  # 更换用户代理
                continue
            
            logger.info(f"收到响应: 状态码={response.status_code}")
            return response
            
        except requests.RequestException as e:
            logger.error(f"请求失败 (尝试 {attempt+1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                logger.info(f"等待{wait_time}秒后重试...")
                time.sleep(wait_time)
            else:
                raise

# 测试反爬功能
def test_anti_crawl():
    logger.info("测试反爬功能")
    
    # 测试请求
    url = "https://www.xiaohongshu.com"
    try:
        response = make_request(url)
        logger.info(f"测试请求成功: {response.status_code}")
    except Exception as e:
        logger.error(f"测试请求失败: {str(e)}")
    
    # 测试API请求
    url = "https://www.xiaohongshu.com/api/sns/web/v1/search/notes"
    try:
        response = make_request(url, params={"keyword": "美食", "page": 1})
        logger.info(f"测试API请求成功: {response.status_code}")
    except Exception as e:
        logger.error(f"测试API请求失败: {str(e)}")
    
    logger.info("反爬功能测试完成")

if __name__ == "__main__":
    test_anti_crawl() 