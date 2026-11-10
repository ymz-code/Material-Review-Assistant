import os
import sys
from volcenginesdkarkruntime import Ark

# 设置输出编码为UTF-8
sys.stdout.reconfigure(encoding='utf-8')

os.environ['ARK_API_KEY'] = 'ark-51a83c4d-a40e-45e2-aa3b-4078a0599e4a-7cbab'

client = Ark(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=os.environ['ARK_API_KEY']
)

print('Testing Ark SDK...')

response = client.responses.create(
    model="doubao-seed-2-0-pro-260215",
    input=[
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "你好"
                }
            ]
        }
    ]
)

print('Response object type:', type(response))
print('Output length:', len(response.output))

for i, item in enumerate(response.output):
    print(f'\n--- Output {i} ---')
    print(f'Type: {type(item).__name__}')
    print(f'Has text attr: {hasattr(item, "text")}')
    print(f'Has content attr: {hasattr(item, "content")}')
    print(f'Has type attr: {hasattr(item, "type")}')
    
    if hasattr(item, 'content'):
        print(f'Content: {item.content}')
    if hasattr(item, 'text'):
        print(f'Text: {item.text}')
    
    # 打印所有属性
    print('All attrs:', [attr for attr in dir(item) if not attr.startswith('_')])
