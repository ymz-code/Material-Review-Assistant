import os
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
        # 输出格式: [ResponseReasoningItem, ResponseOutputMessage]
        # ResponseOutputMessage.content 是一个列表，包含 ResponseOutputText 对象
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

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
