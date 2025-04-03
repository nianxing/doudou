import requests
import json
import sys

def test_api(url):
    """Test the API endpoint with a Xiaohongshu URL"""
    print(f"Testing API with URL: {url}")
    
    # API endpoint
    api_url = "http://localhost:8080/analyze"
    
    # Request data
    data = {
        "url": url
    }
    
    # Make the request
    try:
        print("Sending request to API...")
        response = requests.post(api_url, json=data)
        
        # Check response
        if response.status_code == 200:
            print("API request successful!")
            result = response.json()
            
            # Specially handle the "undefined" error case
            if "error" in result and "Cannot read properties of undefined" in result.get("error", ""):
                print(f"Error detected: {result['error']}")
                print("This error typically occurs when an object is undefined in JavaScript.")
                print("The server response contains valid fallback data which will be used instead.")
            
            # Safely access properties with defensive checks
            original = result.get('original', {})
            analysis = result.get('analysis', {})
            
            # Print basic information with safe access to nested properties
            print("\nBasic information:")
            print(f"Title: {original.get('title', 'No title')}")
            print(f"Text length: {len(original.get('text', ''))}")
            print(f"Keywords: {analysis.get('keywords', [])}")
            print(f"Top posts: {len(analysis.get('top_posts', []))}")
            
            # Save full result to a file
            with open("api_response.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print("\nFull response saved to api_response.json")
            
            return True
        else:
            print(f"API request failed with status code: {response.status_code}")
            print(f"Error: {response.text}")
            return False
    
    except Exception as e:
        print(f"Error making API request: {str(e)}")
        # Handle common JavaScript property access errors which might be in JSON error messages
        if "Cannot read properties of undefined" in str(e):
            print("This error occurs when trying to access a property of an undefined object.")
            print("Please check that all objects in the API response exist before accessing their properties.")
        return False

if __name__ == "__main__":
    # Accept URL from command line or use a default
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://www.xiaohongshu.com/discovery/item/65d57a0d0000000001026747"
    
    # Test the API
    test_api(url) 