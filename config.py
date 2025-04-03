"""
配置文件 - 用于存储API密钥和其他配置
"""

import os
from dotenv import load_dotenv

# 尝试加载.env文件
load_dotenv()

# API代理服务配置
# 优先从环境变量中获取，如果没有则使用默认值
API_KEYS = {
    # ScrapingAPI (https://www.scrapingapi.com/)
    "SCRAPINGAPI_KEY": os.environ.get("SCRAPINGAPI_KEY", ""),
    
    # ScrapingDog (https://www.scrapingdog.com/)
    "SCRAPINGDOG_KEY": os.environ.get("SCRAPINGDOG_KEY", ""),
    
    # ScrapeStack (https://scrapestack.com/)
    "SCRAPESTACK_KEY": os.environ.get("SCRAPESTACK_KEY", ""),
    
    # Bright Data (https://brightdata.com/)
    "BRIGHTDATA_USERNAME": os.environ.get("BRIGHTDATA_USERNAME", ""),
    "BRIGHTDATA_PASSWORD": os.environ.get("BRIGHTDATA_PASSWORD", ""),
    
    # ZenRows (https://www.zenrows.com/)
    "ZENROWS_API_KEY": os.environ.get("ZENROWS_API_KEY", ""),
    
    # ScraperAPI (https://www.scraperapi.com/)
    "SCRAPERAPI_KEY": os.environ.get("SCRAPERAPI_KEY", ""),
}

# AI服务配置
AI_API_KEYS = {
    # OpenAI API
    "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
    
    # DeepSeek API
    "DEEPSEEK_API_KEY": os.environ.get("DEEPSEEK_API_KEY", ""),
}

# 请求配置
REQUEST_CONFIG = {
    # 请求延迟范围（秒）
    "MIN_DELAY": float(os.environ.get("MIN_DELAY", "0.5")),
    "MAX_DELAY": float(os.environ.get("MAX_DELAY", "2.0")),
    
    # 最大重试次数
    "MAX_RETRIES": int(os.environ.get("MAX_RETRIES", "3")),
    
    # 请求超时（秒）
    "TIMEOUT": int(os.environ.get("TIMEOUT", "30")),
}

# 其他配置
APP_CONFIG = {
    # 是否启用调试模式
    "DEBUG": os.environ.get("DEBUG", "False").lower() == "true",
    
    # 是否默认使用API代理
    "USE_API_PROXY": os.environ.get("USE_API_PROXY", "True").lower() == "true",
    
    # 优先使用的API代理服务
    "PREFERRED_API_PROXY": os.environ.get("PREFERRED_API_PROXY", "scrapingapi"),
}

# API代理服务提供商配置
API_PROVIDERS = {
    "scrapingapi": {
        "base_url": "https://api.scrapingapi.com/scrape",
        "params": {
            "api_key": API_KEYS["SCRAPINGAPI_KEY"],
            "url": None,  # 在请求时填充
            "render_js": "true",
            "keep_cookies": "true"
        }
    },
    "scrapingdog": {
        "base_url": "https://api.scrapingdog.com/scrape",
        "params": {
            "api_key": API_KEYS["SCRAPINGDOG_KEY"], 
            "url": None,  # 在请求时填充
            "dynamic": "true"
        }
    },
    "scrapestack": {
        "base_url": "https://api.scrapestack.com/scrape",
        "params": {
            "access_key": API_KEYS["SCRAPESTACK_KEY"],
            "url": None,  # 在请求时填充
            "render_js": "1"
        }
    },
    "scraperapi": {
        "base_url": "https://api.scraperapi.com",
        "params": {
            "api_key": API_KEYS["SCRAPERAPI_KEY"],
            "url": None,  # 在请求时填充
            "render": "true"
        }
    },
    "zenrows": {
        "base_url": "https://api.zenrows.com/v1/",
        "params": {
            "apikey": API_KEYS["ZENROWS_API_KEY"],
            "url": None,  # 在请求时填充
            "js_render": "true",
            "premium_proxy": "true"
        }
    }
}

# 获取配置的辅助函数
def get_api_provider(provider_name=None):
    """获取指定的API提供商配置"""
    provider = provider_name or APP_CONFIG["PREFERRED_API_PROXY"]
    return API_PROVIDERS.get(provider) 