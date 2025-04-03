import time
import json
import random
import logging
import traceback
from urllib.parse import quote
from datetime import datetime
import re
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

from bs4 import BeautifulSoup
import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='xiaohongshu_browser.log',
    filemode='a'
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)
logger = logging.getLogger('xiaohongshu_browser')

# 常量
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
]

# 辅助函数
def get_random_user_agent():
    return random.choice(USER_AGENTS)

def add_random_delay(min_seconds=1.0, max_seconds=3.0):
    """添加随机延迟，降低被检测为机器人的概率"""
    delay = random.uniform(min_seconds, max_seconds)
    logger.debug(f"添加随机延迟: {delay:.2f}秒")
    time.sleep(delay)

def scroll_to_bottom(driver, scroll_count=3, scroll_pause=1.0):
    """滚动到页面底部以加载更多内容"""
    for i in range(scroll_count):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause)

def extract_note_id(url):
    """从URL中提取笔记ID"""
    patterns = [
        r'xiaohongshu\.com/discovery/item/([a-zA-Z0-9]+)',
        r'xiaohongshu\.com/explore/([a-zA-Z0-9]+)',
        r'xhslink\.com/([a-zA-Z0-9]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def normalize_url(url):
    """将各种小红书链接格式标准化"""
    note_id = extract_note_id(url)
    if note_id:
        return f"https://www.xiaohongshu.com/discovery/item/{note_id}"
    return url

# 主要功能
def fetch_post_content_selenium(url):
    """使用Selenium爬取小红书帖子内容"""
    logger.info(f"使用Selenium抓取内容: {url}")
    
    normalized_url = normalize_url(url)
    logger.info(f"标准化URL: {normalized_url}")
    
    options = Options()
    
    # 无头模式 (取消注释以启用)
    # options.add_argument("--headless=new")
    
    # 禁用自动化检测
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # 随机用户代理
    user_agent = get_random_user_agent()
    options.add_argument(f"user-agent={user_agent}")
    
    # 添加其他配置以避免检测
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-browser-side-navigation")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-features=VizDisplayCompositor")
    
    try:
        # 初始化Selenium WebDriver
        logger.info("初始化WebDriver...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # 修改JavaScript环境以避免检测
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                window.navigator.chrome = {
                    runtime: {}
                };
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
            """
        })
        
        # 打开URL
        logger.info(f"访问URL: {normalized_url}")
        driver.get(normalized_url)
        
        # 等待页面加载
        add_random_delay(3.0, 5.0)
        
        # 滚动页面以加载全部内容
        scroll_to_bottom(driver, scroll_count=2)
        
        # 检查是否有需要登录的弹窗，如果有则尝试关闭
        try:
            close_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.modal button.close"))
            )
            close_button.click()
            logger.info("关闭了弹窗")
            add_random_delay(1.0, 2.0)
        except:
            logger.debug("没有检测到弹窗或无法关闭")
        
        # 尝试多种选择器来获取内容
        try:
            # 等待标题加载
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1.title, .note-content .title, .content .title"))
            )
            
            # 提取标题
            title_selectors = [
                "h1.title", 
                ".note-content .title", 
                ".content .title",
                ".note-top .title"
            ]
            
            title = None
            for selector in title_selectors:
                try:
                    title_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    title = title_elem.text.strip()
                    if title:
                        break
                except:
                    continue
            
            # 提取内容文本
            content_selectors = [
                ".note-content .content", 
                ".content .desc", 
                ".note-content .desc",
                ".note-content"
            ]
            
            text = None
            for selector in content_selectors:
                try:
                    content_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    text = content_elem.text.strip()
                    if text:
                        break
                except:
                    continue
            
            # 提取图片
            image_selectors = [
                ".note-content img", 
                ".slide-item img", 
                ".image-container img",
                ".carousel img"
            ]
            
            images = []
            for selector in image_selectors:
                try:
                    img_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for img in img_elements:
                        src = img.get_attribute("src")
                        if src and src.startswith("http") and src not in images:
                            images.append(src)
                except:
                    continue
            
            # 提取视频
            video_selectors = [
                "video source", 
                "video"
            ]
            
            video = None
            for selector in video_selectors:
                try:
                    video_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    video = video_elem.get_attribute("src")
                    if video:
                        break
                except:
                    continue
            
            # 整理结果
            result = {
                "title": title if title else "未找到标题",
                "text": text if text else "未找到内容",
                "images": images,
                "video": video,
                "original_url": url,
                "source": "selenium"
            }
            
            logger.info(f"成功抓取内容: 标题={result['title'][:20]}... 内容长度={len(result['text'])} 图片数={len(images)}")
            return result
            
        except TimeoutException:
            logger.error("页面加载超时")
            # 保存页面源代码以便调试
            with open("timeout_page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            logger.info("已保存页面源代码到timeout_page_source.html")
            
        except Exception as e:
            logger.error(f"提取内容时出错: {str(e)}")
            logger.error(traceback.format_exc())
        
        # 如果正常提取失败，尝试从页面源码直接解析
        try:
            logger.info("尝试从页面源码解析内容...")
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # 尝试查找JSON数据
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'name' in data and 'description' in data:
                        logger.info("从JSON数据中提取到内容")
                        return {
                            "title": data.get('name', '未找到标题'),
                            "text": data.get('description', '未找到内容'),
                            "images": [data.get('image', '')] if data.get('image') else [],
                            "video": data.get('video', None),
                            "original_url": url,
                            "source": "json_ld"
                        }
                except:
                    continue
            
            # 基础解析
            title = soup.find('h1') or soup.find('title')
            title = title.text.strip() if title else "未找到标题"
            
            # 查找主要内容
            main_content = soup.find('article') or soup.find('main') or soup.find('div', class_='content')
            text = main_content.text.strip() if main_content else "未找到内容"
            
            # 查找图片
            images = []
            for img in soup.find_all('img'):
                src = img.get('src')
                if src and src.startswith('http') and src not in images:
                    images.append(src)
            
            logger.info(f"从页面源码提取到内容: 标题={title[:20]}... 内容长度={len(text)} 图片数={len(images)}")
            return {
                "title": title,
                "text": text,
                "images": images,
                "video": None,
                "original_url": url,
                "source": "html_source"
            }
            
        except Exception as e:
            logger.error(f"从页面源码解析内容失败: {str(e)}")
            logger.error(traceback.format_exc())
    
    except Exception as e:
        logger.error(f"Selenium抓取失败: {str(e)}")
        logger.error(traceback.format_exc())
    
    finally:
        try:
            # 关闭浏览器
            driver.quit()
            logger.info("已关闭WebDriver")
        except:
            pass
    
    return None

def manual_input(url):
    """允许用户手动输入内容"""
    print("\n" + "="*50)
    print(f"自动抓取失败: {url}")
    print("请手动输入内容:")
    print("="*50)
    
    title = input("标题: ")
    print("内容 (输入END结束):")
    
    lines = []
    while True:
        line = input()
        if line == "END":
            break
        lines.append(line)
    
    text = "\n".join(lines)
    
    print("图片URL (每行一个，输入END结束):")
    images = []
    while True:
        img_url = input()
        if img_url == "END":
            break
        if img_url.strip():
            images.append(img_url)
    
    return {
        "title": title,
        "text": text,
        "images": images,
        "video": None,
        "original_url": url,
        "source": "manual_input"
    }

def batch_input(urls):
    """批量手动输入多个URL的内容"""
    results = {}
    for url in urls:
        print(f"\n处理URL: {url}")
        choice = input("自动抓取(A)还是手动输入(M)? [A/M]: ").strip().upper()
        
        if choice == 'M':
            results[url] = manual_input(url)
        else:
            print("尝试自动抓取...")
            result = fetch_post_content(url, allow_manual=False)
            if result and result.get('text') != '未找到内容':
                results[url] = result
                print("自动抓取成功!")
            else:
                print("自动抓取失败，切换到手动输入")
                results[url] = manual_input(url)
    
    return results

def fetch_post_content(url, allow_manual=True):
    """
    抓取小红书帖子内容的主函数
    
    Args:
        url: 小红书帖子URL
        allow_manual: 是否允许手动输入
    
    Returns:
        dict: 帖子内容
    """
    logger.info(f"开始抓取: {url}")
    
    try:
        # 第一步：尝试使用Selenium抓取
        content = fetch_post_content_selenium(url)
        
        # 检查内容是否有效
        if content and content.get("text") and content.get("text") != "未找到内容":
            logger.info("Selenium抓取成功")
            return content
        
        logger.warning("Selenium抓取内容为空或无效")
        
        # 如果允许手动输入，则提示用户手动输入
        if allow_manual:
            logger.info("切换到手动输入模式")
            return manual_input(url)
        else:
            # 返回空结果
            logger.warning("返回空结果")
            return {
                "title": "未找到标题",
                "text": "未找到内容",
                "images": [],
                "video": None,
                "original_url": url,
                "source": "failed"
            }
    
    except Exception as e:
        logger.error(f"抓取过程中出错: {str(e)}")
        logger.error(traceback.format_exc())
        
        # 如果允许手动输入，则提示用户手动输入
        if allow_manual:
            logger.info("由于错误切换到手动输入模式")
            return manual_input(url)
        else:
            # 返回空结果
            return {
                "title": "未找到标题",
                "text": "未找到内容",
                "images": [],
                "video": None,
                "original_url": url,
                "source": "error"
            }

def extract_simple_keywords(text, max_keywords=5):
    """从文本中提取关键词（简单实现）"""
    # 过滤掉常见的停用词
    stopwords = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
    
    # 按标点符号分割文本
    segments = re.split(r'[,，.。!！?？:：;；\s]+', text)
    
    # 统计词频
    word_count = {}
    for segment in segments:
        if len(segment) > 1 and segment not in stopwords:
            word_count[segment] = word_count.get(segment, 0) + 1
    
    # 按词频排序
    sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
    
    # 提取前N个关键词
    keywords = [word for word, count in sorted_words[:max_keywords]]
    
    # 如果没有提取到任何关键词，使用标题
    if not keywords and text.strip():
        # 取前两个词作为关键词
        words = text.split()
        keywords = [words[0][:10]] if words else ["小红书"]
    
    return keywords

def generate_mock_top_posts(keywords):
    """生成模拟的热门帖子数据"""
    mock_data = []
    
    keyword = keywords[0] if keywords else "小红书"
    
    mock_data.append({
        "url": "https://example.com/post1",
        "title": f"{keyword}推荐1",
        "likes": 1000
    })
    
    mock_data.append({
        "url": "https://example.com/post2",
        "title": f"{keyword}推荐2",
        "likes": 800
    })
    
    mock_data.append({
        "url": "https://example.com/post3",
        "title": f"{keyword}测评",
        "likes": 600
    })
    
    return mock_data

def analyze_content(content):
    """
    分析小红书帖子内容
    
    Args:
        content: 帖子内容字典
    
    Returns:
        dict: 包含关键词和相关热门帖子的字典
    """
    if not content:
        return {
            "keywords": ["小红书", "好物", "推荐"],
            "top_posts": generate_mock_top_posts(["好物推荐"])
        }
    
    text = content.get("text", "")
    title = content.get("title", "")
    
    # 提取关键词
    combined_text = f"{title} {text}"
    keywords = extract_simple_keywords(combined_text)
    
    # 模拟热门帖子数据
    top_posts = generate_mock_top_posts(keywords)
    
    return {
        "keywords": keywords,
        "top_posts": top_posts
    }

def main(url=None):
    """
    主函数
    
    Args:
        url: 小红书帖子URL
    
    Returns:
        dict: 完整分析结果
    """
    if not url:
        url = input("请输入小红书帖子URL: ")
    
    # 抓取内容
    content = fetch_post_content(url)
    
    # 分析内容
    analysis = analyze_content(content)
    
    # 返回结果
    result = {
        "original": content,
        "analysis": analysis
    }
    
    # 打印结果
    print("\n" + "="*50)
    print(f"标题: {content['title']}")
    print(f"内容: {content['text'][:100]}..." if len(content['text']) > 100 else f"内容: {content['text']}")
    print(f"图片数: {len(content['images'])}")
    print(f"关键词: {', '.join(analysis['keywords'])}")
    print(f"推荐帖子数: {len(analysis['top_posts'])}")
    print("="*50)
    
    return result

if __name__ == "__main__":
    # 如果直接运行脚本
    url = input("请输入小红书帖子URL: ")
    result = main(url)
    
    # 保存结果到文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"result_{timestamp}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存到 result_{timestamp}.json") 