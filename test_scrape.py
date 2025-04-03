import json
import sys
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_scraper')

# Try to import our wrapper
try:
    import use_minimal as scraper
    logger.info("Successfully imported the wrapper")
except ImportError:
    logger.error("Failed to import the wrapper. Make sure use_minimal.py exists.")
    sys.exit(1)

def test_url(url):
    """Test scraping a single URL"""
    logger.info(f"Testing URL: {url}")
    
    try:
        # First test fetching content
        logger.info("Testing fetch_content...")
        start_time = time.time()
        content = scraper.fetch_content(url)
        fetch_time = time.time() - start_time
        
        if content.get("title") and content.get("text"):
            logger.info(f"✓ Content fetched successfully in {fetch_time:.2f}s")
            logger.info(f"  Title: {content.get('title')[:30]}...")
            logger.info(f"  Text length: {len(content.get('text', ''))} chars")
            logger.info(f"  Images: {len(content.get('images', []))} found")
            success = True
        else:
            logger.warning("✗ Content fetch failed or returned empty content")
            logger.info(f"  Title: {content.get('title')}")
            logger.info(f"  Text: {content.get('text')}")
            success = False
        
        # Then test full analysis
        logger.info("Testing full analysis...")
        start_time = time.time()
        result = scraper.analyze_post(url)
        analyze_time = time.time() - start_time
        
        if result.get("analysis") and result["analysis"].get("keywords"):
            logger.info(f"✓ Analysis completed successfully in {analyze_time:.2f}s")
            logger.info(f"  Keywords: {result['analysis'].get('keywords')}")
            logger.info(f"  Top posts: {len(result['analysis'].get('top_posts', []))} found")
            success = success and True
        else:
            logger.warning("✗ Analysis failed or returned empty results")
            success = False
        
        return success
    
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        return False

if __name__ == "__main__":
    # Accept URLs from command line or use test URLs
    if len(sys.argv) > 1:
        urls = sys.argv[1:]
    else:
        # Test URLs (replace with actual Xiaohongshu URLs)
        urls = [
            "https://www.xiaohongshu.com/explore/6421c7100000000013039d47",  # Example URL
            "https://www.xiaohongshu.com/discovery/item/6421c7100000000013039d47"  # Example URL
        ]
    
    # Test each URL
    success_count = 0
    for url in urls:
        if test_url(url):
            success_count += 1
    
    # Print summary
    logger.info(f"Test complete: {success_count}/{len(urls)} URLs successfully scraped")
    
    if success_count == 0:
        logger.error("All tests failed!")
        sys.exit(1)
    elif success_count < len(urls):
        logger.warning("Some tests failed!")
        sys.exit(2)
    else:
        logger.info("All tests passed!")
        sys.exit(0) 