import os
import requests
import tempfile
import json
import base64
from io import BytesIO
from urllib.parse import urlparse, unquote
from pathlib import Path

# 检查是否安装了OpenAI和DeepSeek库
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# 检查是否安装了Pillow图像处理库
try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

# 尝试导入视频处理库(可选)
try:
    import cv2
    import pytube
    VIDEO_PROCESSING_AVAILABLE = True
except ImportError:
    VIDEO_PROCESSING_AVAILABLE = False

# 定义API密钥和默认配置
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

# 如果有OpenAI API密钥，则配置客户端
if OPENAI_API_KEY and OPENAI_AVAILABLE:
    openai.api_key = OPENAI_API_KEY

# 使用哪个AI服务，优先DeepSeek，其次OpenAI
USE_DEEPSEEK = DEEPSEEK_API_KEY != ""
USE_OPENAI = not USE_DEEPSEEK and OPENAI_API_KEY != "" and OPENAI_AVAILABLE

def analyze_image(image_url):
    """
    分析图片内容，提取关键元素、场景、风格等
    
    Args:
        image_url: 图片URL
        
    Returns:
        dict: 图片分析结果
    """
    # 检查依赖和API密钥
    if not (USE_DEEPSEEK or USE_OPENAI):
        return {"error": "未配置AI API密钥，无法分析图片内容"}
    
    if not PILLOW_AVAILABLE:
        return {"error": "未安装Pillow库，无法处理图片"}
    
    try:
        # 下载图片
        response = requests.get(image_url, stream=True, timeout=10)
        response.raise_for_status()
        
        # 使用DeepSeek或OpenAI进行图片分析
        if USE_DEEPSEEK:
            return analyze_image_with_deepseek(response.content)
        elif USE_OPENAI:
            return analyze_image_with_openai(response.content)
        else:
            return {"error": "无法使用AI服务分析图片"}
    
    except Exception as e:
        return {"error": f"图片分析失败: {str(e)}"}

def analyze_image_with_openai(image_data):
    """使用OpenAI Vision API分析图片"""
    try:
        # 将图片编码为base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # 发送请求到OpenAI
        response = openai.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "请详细分析这张图片，包括：1) 主体内容和场景描述 2) 物品或产品识别 3) 视觉风格和色调 4) 图片质量评估 5) 受众吸引力分析。以JSON格式返回，包含以下字段：content(主体内容), objects(识别到的物品), style(风格), quality(质量评分1-10), appeal(受众吸引力评分1-10), keywords(关键词数组)"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=800,
            response_format={"type": "json_object"}
        )
        
        # 解析结果
        result = json.loads(response.choices[0].message.content)
        return {
            "content": result.get("content", "未识别到内容"),
            "objects": result.get("objects", []),
            "style": result.get("style", "未识别到风格"),
            "quality": result.get("quality", 0),
            "appeal": result.get("appeal", 0),
            "keywords": result.get("keywords", []),
            "ai_service": "OpenAI"
        }
    except Exception as e:
        return {"error": f"OpenAI图片分析失败: {str(e)}"}

def analyze_image_with_deepseek(image_data):
    """使用DeepSeek API分析图片"""
    try:
        # 将图片编码为base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # 构建API请求
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        data = {
            "model": "deepseek-vision",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "请详细分析这张图片，包括：1) 主体内容和场景描述 2) 物品或产品识别 3) 视觉风格和色调 4) 图片质量评估 5) 受众吸引力分析。以JSON格式返回，包含以下字段：content(主体内容), objects(识别到的物品), style(风格), quality(质量评分1-10), appeal(受众吸引力评分1-10), keywords(关键词数组)"},
                        {
                            "type": "image",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "response_format": {"type": "json_object"}
        }
        
        # 发送请求
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        
        # 解析结果
        if "choices" in response_data and len(response_data["choices"]) > 0:
            result = json.loads(response_data["choices"][0]["message"]["content"])
            return {
                "content": result.get("content", "未识别到内容"),
                "objects": result.get("objects", []),
                "style": result.get("style", "未识别到风格"),
                "quality": result.get("quality", 0),
                "appeal": result.get("appeal", 0),
                "keywords": result.get("keywords", []),
                "ai_service": "DeepSeek"
            }
        else:
            return {"error": "DeepSeek返回空结果"}
    except Exception as e:
        return {"error": f"DeepSeek图片分析失败: {str(e)}"}

def analyze_video(video_url):
    """
    分析视频内容，提取关键帧、主题、风格等
    
    Args:
        video_url: 视频URL
        
    Returns:
        dict: 视频分析结果
    """
    # 检查依赖和API密钥
    if not VIDEO_PROCESSING_AVAILABLE:
        return {"error": "未安装视频处理库(OpenCV和PyTube)，无法分析视频"}
    
    if not (USE_DEEPSEEK or USE_OPENAI):
        return {"error": "未配置AI API密钥，无法分析视频内容"}
    
    try:
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 下载视频
            yt = None
            video_path = None
            
            # 判断是否为YouTube视频
            if "youtube.com" in video_url or "youtu.be" in video_url:
                yt = pytube.YouTube(video_url)
                stream = yt.streams.filter(progressive=True, file_extension='mp4').first()
                video_path = stream.download(output_path=temp_dir)
            else:
                # 非YouTube视频，直接下载
                local_filename = unquote(os.path.basename(urlparse(video_url).path))
                if not local_filename.endswith('.mp4'):
                    local_filename += '.mp4'
                
                video_path = os.path.join(temp_dir, local_filename)
                response = requests.get(video_url, stream=True)
                response.raise_for_status()
                with open(video_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            # 提取视频关键帧
            frames = extract_keyframes(video_path)
            
            # 分析关键帧
            frame_analyses = []
            for i, frame in enumerate(frames[:3]):  # 只分析前3个关键帧
                # 将帧保存为临时文件
                frame_path = os.path.join(temp_dir, f"frame_{i}.jpg")
                cv2.imwrite(frame_path, frame)
                
                # 读取帧数据
                with open(frame_path, 'rb') as f:
                    frame_data = f.read()
                
                # 分析帧
                if USE_DEEPSEEK:
                    frame_analysis = analyze_image_with_deepseek(frame_data)
                else:
                    frame_analysis = analyze_image_with_openai(frame_data)
                
                frame_analyses.append(frame_analysis)
            
            # 合并分析结果
            return consolidate_video_analysis(frame_analyses, yt)
    
    except Exception as e:
        return {"error": f"视频分析失败: {str(e)}"}

def extract_keyframes(video_path, max_frames=3):
    """提取视频关键帧"""
    # 打开视频
    cap = cv2.VideoCapture(video_path)
    
    # 获取视频信息
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = frame_count / fps
    
    # 计算采样点
    keyframe_positions = [
        int(duration * 0.1 * fps),  # 视频开始10%处
        int(duration * 0.5 * fps),  # 视频中间处
        int(duration * 0.8 * fps)   # 视频80%处
    ]
    
    # 提取关键帧
    frames = []
    for position in keyframe_positions:
        cap.set(cv2.CAP_PROP_POS_FRAMES, position)
        ret, frame = cap.read()
        if ret:
            frames.append(frame)
    
    # 释放资源
    cap.release()
    
    return frames

def consolidate_video_analysis(frame_analyses, yt_info=None):
    """合并多个帧分析结果"""
    # 初始化合并结果
    all_objects = []
    all_keywords = []
    qualities = []
    appeals = []
    
    # 收集所有分析结果
    for analysis in frame_analyses:
        if "error" in analysis:
            continue
        
        # 收集物品
        if "objects" in analysis:
            all_objects.extend(analysis["objects"])
        
        # 收集关键词
        if "keywords" in analysis:
            all_keywords.extend(analysis["keywords"])
        
        # 收集质量分数
        if "quality" in analysis:
            qualities.append(analysis["quality"])
        
        # 收集吸引力分数
        if "appeal" in analysis:
            appeals.append(analysis["appeal"])
    
    # 去除重复项
    unique_objects = list(set(all_objects))
    unique_keywords = list(set(all_keywords))
    
    # 计算平均分数
    avg_quality = sum(qualities) / len(qualities) if qualities else 0
    avg_appeal = sum(appeals) / len(appeals) if appeals else 0
    
    # 构建合并结果
    result = {
        "content": "视频含有多个场景，" + (frame_analyses[0].get("content", "") if frame_analyses else ""),
        "objects": unique_objects,
        "keywords": unique_keywords,
        "quality": round(avg_quality, 1),
        "appeal": round(avg_appeal, 1),
        "frame_count": len(frame_analyses),
        "ai_service": frame_analyses[0].get("ai_service", "未知") if frame_analyses else "未知"
    }
    
    # 添加YouTube信息(如果有)
    if yt_info:
        try:
            result["title"] = yt_info.title
            result["duration"] = yt_info.length
            result["author"] = yt_info.author
            result["views"] = yt_info.views
        except:
            pass
    
    return result

def batch_analyze_images(image_urls, max_images=3):
    """
    批量分析多张图片
    
    Args:
        image_urls: 图片URL列表
        max_images: 最大分析图片数量
        
    Returns:
        list: 图片分析结果列表
    """
    results = []
    
    # 限制处理图片数量
    urls_to_analyze = image_urls[:max_images]
    
    for url in urls_to_analyze:
        result = analyze_image(url)
        results.append(result)
    
    return results

def get_media_improvements(image_analyses, video_analysis):
    """
    基于媒体分析结果生成改进建议
    
    Args:
        image_analyses: 图片分析结果列表
        video_analysis: 视频分析结果
        
    Returns:
        list: 改进建议列表
    """
    suggestions = []
    
    # 图片相关建议
    if image_analyses:
        # 检查图片质量
        low_quality_count = sum(1 for img in image_analyses if img.get("quality", 0) < 7)
        if low_quality_count > 0:
            suggestions.append(f"有{low_quality_count}张图片质量较低，建议使用更清晰的图片")
        
        # 检查图片吸引力
        low_appeal_count = sum(1 for img in image_analyses if img.get("appeal", 0) < 7)
        if low_appeal_count > 0:
            suggestions.append(f"有{low_appeal_count}张图片吸引力不足，建议优化构图或使用更吸引人的图片")
        
        # 图片风格建议
        styles = [img.get("style", "") for img in image_analyses]
        if len(set(styles)) > 1:
            suggestions.append("图片风格不统一，建议保持一致的视觉风格")
    
    # 视频相关建议
    if video_analysis and "error" not in video_analysis:
        # 检查视频质量
        if video_analysis.get("quality", 0) < 7:
            suggestions.append("视频质量较低，建议使用更高清的视频")
        
        # 检查视频吸引力
        if video_analysis.get("appeal", 0) < 7:
            suggestions.append("视频吸引力不足，建议优化内容或使用更吸引人的场景")
    
    # 媒体组合建议
    if not video_analysis or "error" in video_analysis:
        suggestions.append("建议添加产品使用视频，可以展示实际效果和使用方法")
    
    if not image_analyses:
        suggestions.append("建议添加高质量图片展示产品细节和多个角度")
    elif len(image_analyses) < 3:
        suggestions.append(f"当前仅有{len(image_analyses)}张图片，建议增加到3-9张，展示更多产品细节")
    
    return suggestions

# 导出要使用的函数
__all__ = [
    'analyze_image', 
    'analyze_video', 
    'batch_analyze_images', 
    'get_media_improvements'
]

if __name__ == "__main__":
    # 测试代码
    test_image_url = "https://via.placeholder.com/500x300"
    result = analyze_image(test_image_url)
    print(json.dumps(result, indent=2, ensure_ascii=False)) 