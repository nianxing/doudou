import os
import sys
import traceback

print("Starting debug script...")

# Try importing the modules directly
try:
    print("Attempting to import xiaohongshu_ai_tool_minimal...")
    import xiaohongshu_ai_tool_minimal
    print("SUCCESS: Imported xiaohongshu_ai_tool_minimal")
    print(f"Module location: {xiaohongshu_ai_tool_minimal.__file__}")
    
    # List attributes
    print("\nAttributes in xiaohongshu_ai_tool_minimal:")
    for attr in dir(xiaohongshu_ai_tool_minimal):
        if not attr.startswith("__"):
            print(f"- {attr}")
    
    # Try to use the module
    print("\nTesting fetch_post_content function...")
    url = "https://www.xiaohongshu.com/discovery/item/65d57a0d0000000001026747"
    try:
        content = xiaohongshu_ai_tool_minimal.fetch_post_content(url)
        print(f"Content fetched: Title = {content.get('title', 'No title')}")
        print(f"Text length: {len(content.get('text', ''))}")
    except Exception as e:
        print(f"ERROR calling fetch_post_content: {str(e)}")
        traceback.print_exc()
    
except ImportError as e:
    print(f"FAILED to import xiaohongshu_ai_tool_minimal: {str(e)}")
    
try:
    print("\nAttempting to import xiaohongshu_tool...")
    import xiaohongshu_tool
    print("SUCCESS: Imported xiaohongshu_tool")
    print(f"Module location: {xiaohongshu_tool.__file__}")
    
    # List attributes
    print("\nAttributes in xiaohongshu_tool:")
    for attr in dir(xiaohongshu_tool):
        if not attr.startswith("__"):
            print(f"- {attr}")
    
    # Try to use the module
    print("\nTesting fetch_post_content function...")
    url = "https://www.xiaohongshu.com/discovery/item/65d57a0d0000000001026747"
    try:
        content = xiaohongshu_tool.fetch_post_content(url)
        print(f"Content fetched: Title = {content.get('title', 'No title')}")
        print(f"Text length: {len(content.get('text', ''))}")
    except Exception as e:
        print(f"ERROR calling fetch_post_content: {str(e)}")
        traceback.print_exc()
        
except ImportError as e:
    print(f"FAILED to import xiaohongshu_tool: {str(e)}")

# System info
print("\nSystem information:")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print("Files in current directory:")
for f in os.listdir('.'):
    if "xiaohongshu" in f:
        print(f"- {f}")

print("\nDebug script completed") 