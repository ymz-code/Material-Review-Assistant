import os
import json
import re
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from volcenginesdkarkruntime import Ark

load_dotenv()

app = FastAPI()

api_key = os.getenv('ARK_API_KEY')

def get_client():
    if not api_key:
        raise ValueError("ARK_API_KEY environment variable not set")
    return Ark(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key=api_key
    )

class ChatRequest(BaseModel):
    message: str

class VideoAnalyzeRequest(BaseModel):
    message: str
    video_url: str

class KeywordDetectRequest(BaseModel):
    keywords: list
    video_url: str

class ChatResponse(BaseModel):
    response: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        client = get_client()
        
        response = client.responses.create(
            model="doubao-seed-2-0-pro-260215",
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": request.message
                        }
                    ]
                }
            ]
        )
        
        # 提取响应文本
        answer = ""
        for item in response.output:
            if hasattr(item, 'content'):
                for content_item in item.content:
                    if hasattr(content_item, 'text'):
                        answer += content_item.text
        
        return ChatResponse(response=answer)
        
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-video")
async def analyze_video(request: VideoAnalyzeRequest):
    try:
        client = get_client()
        
        print(f"[DEBUG] 开始分析视频: {request.video_url}")
        print(f"[DEBUG] 问题: {request.message}")
        
        # 使用 chat.completions.create 而不是 responses.create
        # 参考官方文档格式
        try:
            response = client.chat.completions.create(
                model="doubao-seed-2-0-pro-260215",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "video_url",
                                "video_url": {
                                    "url": request.video_url
                                }
                            },
                            {
                                "type": "text",
                                "text": request.message
                            }
                        ]
                    }
                ]
            )
            
            # 提取响应文本
            answer = response.choices[0].message.content
            print(f"[DEBUG] API响应成功: {answer[:100]}...")
            
            return ChatResponse(response=answer)
            
        except Exception as api_error:
            error_msg = str(api_error)
            print(f"[ERROR] API调用失败: {error_msg}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=400,
                detail=f"API调用失败。错误详情: {error_msg}\n\n可能原因：\n1. 视频URL无法直接访问（B站、YouTube等需要解析）\n2. 视频格式不支持\n3. API密钥无效\n\n建议：使用可直接访问的视频URL，如 https://example.com/video.mp4"
            )
            
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/detect-keywords")
async def detect_keywords(request: KeywordDetectRequest):
    try:
        keyword_list = request.keywords
        
        if not keyword_list or len(keyword_list) == 0:
            raise HTTPException(status_code=400, detail="请提供至少一个关键词")
        
        client = get_client()
        
        # 构建关键词检测的提示词
        keywords_str = "、".join(keyword_list)
        prompt = f"""请分析这个视频，检测以下关键词的出现位置：
关键词：{keywords_str}

对于每个检测到的关键词，请提供：
1. 出现的大致时间点
2. 出现的上下文内容

请使用以下JSON格式返回结果：
{{
    "results": [
        {{
            "keyword": "关键词",
            "matches": [
                {{
                    "timestamp": "时间点",
                    "context": "上下文内容"
                }}
            ]
        }}
    ],
    "total_matches": 总匹配次数
}}

注意：
- 如果某个关键词未检测到，该关键词的matches数组为空
- 时间点请使用 MM:SS 或 HH:MM:SS 格式
- 如果无法准确判断时间点，请说明原因
- 只返回JSON格式，不要有其他文字"""
        
        try:
            response = client.chat.completions.create(
                model="doubao-seed-2-0-pro-260215",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "video_url",
                                "video_url": {
                                    "url": request.video_url
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            
            # 提取响应文本
            answer = response.choices[0].message.content
            
            # 尝试解析JSON响应
            try:
                # 尝试提取JSON部分
                json_match = re.search(r'\{[\s\S]*\}', answer)
                if json_match:
                    result = json.loads(json_match.group())
                    return result
                else:
                    # 如果无法解析为JSON，返回原始文本
                    return {
                        "results": [{
                            "keyword": "检测结果",
                            "matches": [{
                                "timestamp": "N/A",
                                "context": answer
                            }]
                        }],
                        "total_matches": 1,
                        "raw_response": answer
                    }
            except json.JSONDecodeError:
                # JSON解析失败，返回原始文本
                return {
                    "results": [{
                        "keyword": "检测结果",
                        "matches": [{
                            "timestamp": "N/A",
                            "context": answer
                        }]
                    }],
                    "total_matches": 1,
                    "raw_response": answer
                }
            
        except Exception as api_error:
            error_msg = str(api_error)
            raise HTTPException(
                status_code=400,
                detail=f"API调用失败。可能原因：\n1. 视频URL无法访问\n2. 视频格式不支持\n3. API密钥无效\n\n错误详情: {error_msg}"
            )
            
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/parse-video-url")
async def parse_video_url(request: dict):
    """
    解析视频网页链接，获取直接视频URL
    支持：B站、YouTube等主流平台
    """
    try:
        url = request.get("url")
        if not url:
            raise HTTPException(status_code=400, detail="请提供视频链接")
        
        print(f"[DEBUG] 解析视频链接: {url}")
        
        # 检查是否已经是直链
        if url.endswith(('.mp4', '.webm', '.avi', '.mov', '.mkv')):
            print(f"[DEBUG] 已经是直链，无需解析")
            return {"direct_url": url, "platform": "direct"}
        
        # 尝试使用 yt-dlp 解析
        try:
            import subprocess
            import json as json_lib
            
            # 检查是否安装了 yt-dlp
            try:
                subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
            except:
                return {
                    "error": "需要安装 yt-dlp 工具",
                    "install_command": "pip install yt-dlp",
                    "alternative": "使用在线解析网站：\n• B站: https://bilibili.iiilab.com/\n• YouTube: https://www.y2mate.com/"
                }
            
            # 使用 yt-dlp 获取视频URL
            cmd = [
                "yt-dlp",
                "-f", "best[ext=mp4]/best",
                "--get-url",
                "--no-warnings",
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                direct_url = result.stdout.strip()
                print(f"[DEBUG] 解析成功: {direct_url[:100]}...")
                
                # 判断平台
                platform = "unknown"
                if "bilibili.com" in url or "b23.tv" in url:
                    platform = "bilibili"
                elif "youtube.com" in url or "youtu.be" in url:
                    platform = "youtube"
                
                return {
                    "direct_url": direct_url,
                    "platform": platform,
                    "original_url": url
                }
            else:
                error_msg = result.stderr.strip()
                print(f"[ERROR] yt-dlp 解析失败: {error_msg}")
                return {
                    "error": f"解析失败: {error_msg}",
                    "alternative": "使用在线解析网站：\n• B站: https://bilibili.iiilab.com/\n• YouTube: https://www.y2mate.com/"
                }
                
        except subprocess.TimeoutExpired:
            return {
                "error": "解析超时，视频可能过大或网络问题",
                "alternative": "使用在线解析网站：\n• B站: https://bilibili.iiilab.com/\n• YouTube: https://www.y2mate.com/"
            }
        except Exception as e:
            print(f"[ERROR] 解析过程出错: {str(e)}")
            return {
                "error": f"解析失败: {str(e)}",
                "alternative": "使用在线解析网站：\n• B站: https://bilibili.iiilab.com/\n• YouTube: https://www.y2mate.com/"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
