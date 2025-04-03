import re
import os
import sys

def fix_syntax(filepath):
    print(f"正在修复文件: {filepath}")
    
    # 读取文件内容
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份原始文件
    backup_path = filepath + '.bak'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"已创建备份文件: {backup_path}")
    
    # 修复fetch_post_content_alternative函数缩进问题
    pattern1 = r'def fetch_post_content_alternative\(url\):(.*?)def'
    match = re.search(pattern1, content, re.DOTALL)
    
    if match:
        old_function = match.group(1)
        # 修复缩进问题
        new_function = """def fetch_post_content_alternative(url):
    \"\"\"备用抓取方法，使用移动端模拟或不同的请求方式\"\"\"
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
                except Exception:
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

def"""
        
        # 替换内容
        fixed_content = content.replace(match.group(0), new_function)
        
        # 写入修复后的文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
            
        print("文件修复完成!")
        return True
    else:
        print("未找到需要修复的函数，请手动修复文件")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        filepath = "xiaohongshu_ai_tool.py"
    
    if os.path.exists(filepath):
        fix_syntax(filepath)
    else:
        print(f"错误: 文件不存在 - {filepath}")
        sys.exit(1) 