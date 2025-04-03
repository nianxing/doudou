import os
import sys
import json
import logging
import traceback  # Add traceback for detailed error info

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('xiaohongshu_wrapper')

# First try to import the minimal version
try:
    import xiaohongshu_ai_tool_minimal as scraper
    logger.info("Successfully imported xiaohongshu_ai_tool_minimal")
except ImportError as e:
    # If minimal version not available, use the basic tool
    logger.warning(f"Failed to import xiaohongshu_ai_tool_minimal: {str(e)}")
    try:
        import xiaohongshu_tool as scraper
        logger.info("Using basic xiaohongshu_tool")
    except ImportError as e:
        logger.error(f"Failed to import xiaohongshu_tool: {str(e)}")
        logger.error("No scraper module available!")
        sys.exit(1)

def fetch_content(url):
    """
    Fetches content from a Xiaohongshu post URL using the minimal tool
    
    Args:
        url: The URL of the Xiaohongshu post
        
    Returns:
        dict: The scraped content
    """
    logger.info(f"Fetching content from: {url}")
    
    try:
        # Try to fetch the content
        content = scraper.fetch_post_content(url)
        logger.info(f"Successfully fetched content. Title: {content.get('title', 'No title')[:30]}")
        
        # If the content is empty, use a mock content
        if not content.get("text") or content.get("text") == "未找到内容，请手动输入":
            logger.warning("Failed to fetch content, using mock data")
            content = create_mock_content(url)
            
        return content
    except Exception as e:
        logger.error(f"Error fetching content: {str(e)}")
        logger.error(traceback.format_exc())
        return create_mock_content(url)

def analyze_post(url):
    """
    Analyzes a Xiaohongshu post
    
    Args:
        url: The URL of the Xiaohongshu post
        
    Returns:
        dict: Analysis results
    """
    logger.info(f"Analyzing post: {url}")
    
    try:
        # Fetch content first
        content = fetch_content(url)
        
        # Make sure content is not None and has required fields
        if content is None:
            logger.error("Content is None, using mock data instead")
            content = create_mock_content(url)
        
        # Ensure content has all required fields
        if not isinstance(content, dict):
            logger.error(f"Content is not a dictionary: {type(content)}, using mock data")
            content = create_mock_content(url)
        
        # Ensure content has required fields
        content['title'] = content.get('title', '未找到标题')
        content['text'] = content.get('text', '未找到内容')
        content['images'] = content.get('images', [])
        content['video'] = content.get('video', None)
        
        # Then analyze it
        logger.info("Analyzing content...")
        try:
            analysis = scraper.analyze_content(content)
            logger.info(f"Analysis complete. Keywords: {analysis.get('keywords', [])}")
        except Exception as e:
            logger.error(f"Error in analyze_content: {str(e)}")
            logger.error(traceback.format_exc())
            # Fallback to basic analysis
            analysis = {
                "keywords": ["小红书", "好物", "推荐"],
                "top_posts": scraper.generate_mock_top_posts(["好物"])
            }
        
        # Ensure analysis has required fields
        if not isinstance(analysis, dict):
            logger.error(f"Analysis is not a dictionary: {type(analysis)}, using mock data")
            analysis = {
                "keywords": ["小红书", "好物", "推荐"],
                "top_posts": scraper.generate_mock_top_posts(["好物"])
            }
        
        # Ensure analysis has required fields
        analysis['keywords'] = analysis.get('keywords', ["小红书", "好物", "推荐"])
        analysis['top_posts'] = analysis.get('top_posts', scraper.generate_mock_top_posts(["好物"]))
        
        # Return the complete result
        result = {
            "original": content,
            "analysis": analysis
        }
        
        return result
    except Exception as e:
        logger.error(f"Error analyzing post: {str(e)}")
        logger.error(traceback.format_exc())
        # Return a basic result with mock data
        return {
            "original": create_mock_content(url),
            "analysis": {
                "keywords": ["小红书", "好物", "推荐"],
                "top_posts": scraper.generate_mock_top_posts(["好物"])
            }
        }

def create_mock_content(url):
    """Creates mock content when scraping fails"""
    return {
        "title": "小红书内容 (模拟数据)",
        "text": "这是一个模拟的小红书内容，因为无法从原始URL获取数据。这可能是由于反爬虫措施或者网络问题导致的。请稍后再试或者手动输入内容。",
        "images": ["https://example.com/image1.jpg"],
        "video": None,
        "original_url": url
    }

if __name__ == "__main__":
    try:
        # If run directly, accept a URL as command line argument
        if len(sys.argv) > 1:
            url = sys.argv[1]
            logger.info(f"Using URL from command line: {url}")
        else:
            url = input("请输入小红书帖子URL: ")
            logger.info(f"Using URL from input: {url}")
        
        # Analyze the post
        logger.info("Starting analysis...")
        result = analyze_post(url)
        
        # Print the result as JSON
        logger.info("Analysis complete, printing results:")
        json_result = json.dumps(result, ensure_ascii=False, indent=2)
        print("\n" + "="*50 + "\nRESULTS:\n" + "="*50)
        print(json_result)
        print("="*50)
        
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1) 