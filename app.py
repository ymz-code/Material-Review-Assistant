import os
import uuid
import json
import asyncio
import aiofiles
import logging
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from volcenginesdkarkruntime import AsyncArk

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建上传目录
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 配置
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB
REQUEST_TIMEOUT = 300  # 5分钟

api_key = os.getenv('ARK_API_KEY')

# 健康检查
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

# 创建异步客户端
client = None

def get_client():
    global client
    if not api_key:
        raise ValueError("ARK_API_KEY environment variable not set")
    if client is None:
        client = AsyncArk(
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key=api_key
        )
    return client

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        client = get_client()
        
        # 使用异步客户端调用
        response = await client.responses.create(
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

@app.post("/api/detect-keywords")
async def detect_keywords(
    keywords: str = Form(...),
    video: UploadFile = File(...)
):
    logger.info(f"开始关键词检测: {video.filename}")
    
    try:
        import json
        keyword_list = json.loads(keywords)
        
        if not keyword_list or len(keyword_list) == 0:
            raise HTTPException(status_code=400, detail="请提供至少一个关键词")
        
        # 检查文件大小
        content = await video.read()
        file_size = len(content)
        
        if file_size > MAX_VIDEO_SIZE:
            raise HTTPException(status_code=413, detail=f"文件大小超过限制（最大 {MAX_VIDEO_SIZE//(1024*1024)}MB）")
        
        # 保存上传的视频文件
        file_ext = os.path.splitext(video.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # 异步写入文件
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        logger.info(f"视频文件已保存: {file_path}")
        
        client = get_client()
        
        # 使用官方推荐的 Files API 异步上传视频
        logger.info("开始上传视频到火山引擎")
        with open(file_path, 'rb') as video_file:
            # 上传视频文件
            uploaded_file = await client.files.create(
                file=video_file,
                purpose="user_data",
                preprocess_configs={
                    "video": {
                        "fps": 1  # 定义视频采样帧率，默认1.0
                    }
                }
            )
            logger.info(f"文件上传成功: {uploaded_file.id}")
            
            # 等待文件处理完成（官方推荐方法）
            logger.info("等待文件处理完成...")
            await client.files.wait_for_processing(uploaded_file.id)
            logger.info(f"文件处理完成: {uploaded_file.id}")
        
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
        
        # 使用 file_id 调用豆包API分析视频
        logger.info("开始调用豆包API检测关键词")
        response = await client.responses.create(
            model="doubao-seed-2-0-pro-260215",
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_video",
                            "file_id": uploaded_file.id  # 使用 file_id
                        },
                        {
                            "type": "input_text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        logger.info("关键词检测完成")
        
        # 提取响应文本
        answer = ""
        for item in response.output:
            if hasattr(item, 'content'):
                for content_item in item.content:
                    if hasattr(content_item, 'text'):
                        answer += content_item.text
        
        # 尝试解析JSON响应
        try:
            # 尝试提取JSON部分
            import re
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
            
    except HTTPException as e:
        logger.error(f"HTTP错误: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"关键词检测错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"关键词检测失败: {str(e)}")

@app.post("/api/review-video")
async def review_video(
    requirements: str = Form(...),
    video: UploadFile = File(...)
):
    logger.info(f"开始视频合规检测: {video.filename}")
    
    try:
        # 检查文件大小
        content = await video.read()
        file_size = len(content)
        
        if file_size > MAX_VIDEO_SIZE:
            raise HTTPException(status_code=413, detail=f"文件大小超过限制（最大 {MAX_VIDEO_SIZE//(1024*1024)}MB）")
        
        # 保存上传的视频文件
        file_ext = os.path.splitext(video.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # 异步写入文件
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        logger.info(f"视频文件已保存: {file_path}")
        
        client = get_client()
        
        # 使用官方推荐的 Files API 异步上传视频
        logger.info("开始上传视频到火山引擎")
        with open(file_path, 'rb') as video_file:
            # 上传视频文件
            uploaded_file = await client.files.create(
                file=video_file,
                purpose="user_data",
                preprocess_configs={
                    "video": {
                        "fps": 1  # 定义视频采样帧率，默认1.0
                    }
                }
            )
            logger.info(f"文件上传成功: {uploaded_file.id}")
            
            # 等待文件处理完成（官方推荐方法）
            logger.info("等待文件处理完成...")
            await client.files.wait_for_processing(uploaded_file.id)
            logger.info(f"文件处理完成: {uploaded_file.id}")
        
        # 构建合规检测的提示词
        prompt = f"""请分析这个视频，根据以下要求进行评估：
        
        检测要求：
        {requirements}
        
        请按照以下要求进行分析：
        1. 判断视频是否满足上述所有要求
        2. 如果视频满足要求，返回"通过"
        3. 如果视频不满足要求，返回"不通过"，并列出具体问题
        4. 提供详细的评估理由
        
        请使用以下JSON格式返回结果：
        {{
            "pass": true/false,
            "result": "评估结果描述",
            "reasons": ["符合要求的理由1", "符合要求的理由2", ...],
            "issues": ["问题1", "问题2", ...]
        }}
        
        注意：
        - pass字段必须是布尔值
        - 如果pass为true，issues数组可以为空
        - 如果pass为false，reasons数组可以为空
        - 只返回JSON格式，不要有其他文字"""
        
        # 使用 file_id 调用豆包API分析视频
        logger.info("开始调用豆包API进行合规检测")
        response = await client.responses.create(
            model="doubao-seed-2-0-pro-260215",
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_video",
                            "file_id": uploaded_file.id  # 使用 file_id
                        },
                        {
                            "type": "input_text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        logger.info("视频合规检测完成")
        
        # 提取响应文本
        answer = ""
        for item in response.output:
            if hasattr(item, 'content'):
                for content_item in item.content:
                    if hasattr(content_item, 'text'):
                        answer += content_item.text
        
        # 尝试解析JSON响应
        try:
            import re
            json_match = re.search(r'\{[\s\S]*\}', answer)
            if json_match:
                result = json.loads(json_match.group())
                return result
            else:
                # 如果无法解析为JSON，返回原始文本
                return {
                    "pass": False,
                    "result": answer,
                    "reasons": [],
                    "issues": ["无法解析AI响应"],
                    "raw_response": answer
                }
        except json.JSONDecodeError:
            # JSON解析失败，返回原始文本
            return {
                "pass": False,
                "result": answer,
                "reasons": [],
                "issues": ["无法解析AI响应"],
                "raw_response": answer
            }
            
    except HTTPException as e:
        logger.error(f"HTTP错误: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"视频合规检测错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"视频检测失败: {str(e)}")

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
