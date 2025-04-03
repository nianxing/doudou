import requests
import json
import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('undefined_error_diagnostics')

def diagnose_api(url):
    """Diagnose API response for undefined property errors"""
    logger.info(f"诊断API响应: {url}")
    
    # API endpoint
    api_url = "http://localhost:8080/analyze"
    
    # Request data
    data = {
        "url": url
    }
    
    try:
        logger.info("发送请求到API...")
        response = requests.post(api_url, json=data)
        
        if response.status_code == 200:
            logger.info("API请求成功!")
            
            # Store raw response text for analysis
            raw_text = response.text
            logger.debug(f"原始响应: {raw_text[:200]}...")
            
            # Try to parse JSON
            try:
                result = response.json()
                logger.info("JSON解析成功")
                
                # Check for explicit error message in response
                if "error" in result:
                    logger.error(f"API返回错误: {result['error']}")
                
                # Now perform deep validation of the structure
                validate_structure(result)
                
                # Fix anything that's undefined or misformatted
                fixed_result = fix_undefined_properties(result)
                
                # Save both original and fixed versions
                with open("original_response.json", "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                with open("fixed_response.json", "w", encoding="utf-8") as f:
                    json.dump(fixed_result, f, ensure_ascii=False, indent=2)
                
                logger.info("诊断完成！原始响应和修复后的响应已分别保存到original_response.json和fixed_response.json")
                
                return fixed_result
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {str(e)}")
                logger.error(f"无效的JSON响应: {raw_text[:200]}...")
                return None
        else:
            logger.error(f"API请求失败: HTTP {response.status_code}")
            logger.error(f"错误信息: {response.text}")
            return None
    
    except Exception as e:
        logger.error(f"请求过程中出错: {str(e)}")
        if "Cannot read properties of undefined" in str(e):
            logger.error("这是JavaScript中常见的'undefined'对象属性访问错误")
            logger.error("请确保在访问任何对象属性前检查对象是否存在")
        return None

def validate_structure(data, path="root"):
    """Validate and log issues with the JSON structure"""
    if data is None:
        logger.warning(f"在{path}位置发现null值")
        return
    
    if isinstance(data, dict):
        for key, value in data.items():
            new_path = f"{path}.{key}"
            
            if value is None:
                logger.warning(f"在{new_path}位置发现null值")
            elif isinstance(value, (dict, list)):
                validate_structure(value, new_path)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            new_path = f"{path}[{i}]"
            validate_structure(item, new_path)

def fix_undefined_properties(data):
    """Fix any undefined or null properties in the JSON structure"""
    if data is None:
        return {}
    
    if isinstance(data, dict):
        fixed_dict = {}
        
        # First ensure top-level structure is correct
        if "original" not in data:
            logger.warning("修复：添加缺失的'original'对象")
            data["original"] = {}
        
        if "analysis" not in data:
            logger.warning("修复：添加缺失的'analysis'对象")
            data["analysis"] = {}
        
        # Fix each property
        for key, value in data.items():
            if key == "original":
                # Ensure original has all required fields
                original = value if isinstance(value, dict) else {}
                
                if not isinstance(original, dict):
                    logger.warning("修复：'original'不是一个对象，创建新对象")
                    original = {}
                
                if "title" not in original or original["title"] is None:
                    logger.warning("修复：添加缺失的'title'字段")
                    original["title"] = "未找到标题"
                
                if "text" not in original or original["text"] is None:
                    logger.warning("修复：添加缺失的'text'字段")
                    original["text"] = "未找到内容"
                
                if "images" not in original or original["images"] is None:
                    logger.warning("修复：添加缺失的'images'字段")
                    original["images"] = []
                
                if "video" not in original or original["video"] is None:
                    logger.warning("修复：添加缺失的'video'字段")
                    original["video"] = None
                
                fixed_dict[key] = original
            
            elif key == "analysis":
                # Ensure analysis has all required fields
                analysis = value if isinstance(value, dict) else {}
                
                if not isinstance(analysis, dict):
                    logger.warning("修复：'analysis'不是一个对象，创建新对象")
                    analysis = {}
                
                if "keywords" not in analysis or analysis["keywords"] is None:
                    logger.warning("修复：添加缺失的'keywords'字段")
                    analysis["keywords"] = ["小红书", "好物", "推荐"]
                
                if "top_posts" not in analysis or analysis["top_posts"] is None:
                    logger.warning("修复：添加缺失的'top_posts'字段")
                    analysis["top_posts"] = []
                
                fixed_dict[key] = analysis
            
            else:
                # For other fields, apply general fix
                fixed_dict[key] = fix_undefined_properties(value)
        
        return fixed_dict
    
    elif isinstance(data, list):
        return [fix_undefined_properties(item) for item in data]
    
    else:
        # For primitive values, return as is
        return data

if __name__ == "__main__":
    # Accept URL from command line or use a default
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://www.xiaohongshu.com/discovery/item/65d57a0d0000000001026747"
    
    # Diagnose the API
    result = diagnose_api(url)
    
    if result:
        logger.info("诊断成功并修复了潜在问题")
    else:
        logger.error("诊断失败，无法修复API响应")
        sys.exit(1) 