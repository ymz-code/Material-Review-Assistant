# 豆包AI视频助手 - 使用说明

## 🎯 功能概览

这是一个基于豆包大模型的AI视频分析助手，支持：
- ✅ 视频内容分析
- ✅ 关键词检测与时间戳定位
- ✅ 自动解析视频链接（B站、YouTube等）
- ✅ 智能对话交互

## 📦 安装依赖

```bash
# 安装Python依赖
pip install fastapi uvicorn volcengine-python-sdk

# 可选：安装视频解析工具
pip install yt-dlp
```

## 🚀 启动服务

```bash
# 方法1：直接运行
python app.py

# 方法2：使用启动脚本（Windows）
start.bat
```

服务将在 http://localhost:8000 启动

## 📖 使用方法

### 1. 视频分析

#### 方法A：使用直接视频URL
1. 访问 http://localhost:8000/test.html
2. 输入视频直链URL（如 `https://example.com/video.mp4`）
3. 点击"加载视频"
4. 输入问题（如"请描述这个视频的内容"）
5. 点击"分析视频"

#### 方法B：自动解析视频链接
1. 输入B站或YouTube链接
2. 点击"🔄 自动解析"按钮
3. 系统自动获取直链并加载
4. 进行视频分析

#### 方法C：手动获取直链
1. 点击"📖 如何获取直链"按钮
2. 按照提示使用在线工具或命令行工具
3. 获取直链后粘贴到输入框

### 2. 关键词检测

1. 加载视频后
2. 输入关键词（用逗号分隔，如：`人工智能, Python, 机器学习`）
3. 点击"检测关键词"
4. 查看检测结果（包含时间戳和上下文）

## 🔧 API接口

### 视频分析
```http
POST /api/analyze-video
Content-Type: application/json

{
  "message": "请描述这个视频的内容",
  "video_url": "https://example.com/video.mp4"
}
```

### 关键词检测
```http
POST /api/detect-keywords
Content-Type: application/json

{
  "keywords": ["关键词1", "关键词2"],
  "video_url": "https://example.com/video.mp4"
}
```

### 视频链接解析
```http
POST /api/parse-video-url
Content-Type: application/json

{
  "url": "https://www.bilibili.com/video/BV1xx411c7mD"
}
```

## 🎬 支持的视频平台

### 直接支持（无需解析）
- 任何 `.mp4`, `.webm`, `.avi`, `.mov`, `.mkv` 结尾的URL
- 官方测试视频：`https://ark-project.tos-cn-beijing.volces.com/doc_video/r2v_tea_video1.mp4`

### 自动解析支持
- ✅ 哔哩哔哩（B站）
- ✅ YouTube
- ✅ 其他主流视频平台

## 🛠️ 获取视频直链的方法

### B站视频

#### 方法1：在线解析网站
- https://bilibili.iiilab.com/
- https://www.xbeibeix.com/api/bilibili/

**步骤：**
1. 复制B站视频链接
2. 打开解析网站，粘贴链接
3. 选择清晰度，点击解析
4. 复制生成的 `.mp4` 或 `.flv` 链接

#### 方法2：使用Python工具
```bash
# 安装工具
pip install you-get

# 获取视频信息
you-get -i 'https://www.bilibili.com/video/BV1xx411c7mD'

# 查看输出的视频URL
```

### YouTube视频

#### 方法1：在线解析网站
- https://www.y2mate.com/
- https://savefrom.net/

**步骤：**
1. 复制YouTube链接
2. 打开解析网站，粘贴链接
3. 选择格式和清晰度
4. 复制生成的下载链接

#### 方法2：使用Python工具
```bash
# 安装工具
pip install yt-dlp

# 获取视频URL
yt-dlp -f best --get-url 'https://www.youtube.com/watch?v=xxx'
```

## ⚠️ 注意事项

### 视频要求
- ✅ 视频URL必须可直接访问
- ✅ 视频格式：MP4, WebM, AVI, MOV, MKV
- ✅ 视频大小：建议 < 100MB
- ✅ 视频时长：建议 < 10分钟

### 链接要求
- ❌ 不支持需要登录的视频
- ❌ 不支持加密或DRM保护的视频
- ❌ 不支持直播流
- ✅ 支持HTTP/HTTPS协议

### 性能优化
- 使用较短的视频片段
- 选择合适的清晰度（不必最高）
- 避免高峰时段访问

## 🐛 常见问题

### Q1: 提示"API调用失败"
**原因：**
- 视频URL无法访问
- 视频格式不支持
- API密钥无效

**解决：**
1. 检查视频URL是否可直接在浏览器打开
2. 确认视频格式是否支持
3. 检查 `.env` 文件中的 `ARK_API_KEY` 是否正确

### Q2: 视频解析失败
**原因：**
- 未安装 `yt-dlp` 工具
- 视频需要登录
- 地区限制

**解决：**
1. 安装工具：`pip install yt-dlp`
2. 使用在线解析网站
3. 尝试其他视频源

### Q3: 关键词检测不准确
**原因：**
- 视频质量问题
- 关键词不明确
- AI理解偏差

**解决：**
1. 使用更具体的关键词
2. 提供更多上下文
3. 尝试不同的提问方式

## 📝 配置文件

### .env
```env
ARK_API_KEY=your_api_key_here
```

### requirements.txt
```
fastapi
uvicorn
volcengine-python-sdk
python-dotenv
yt-dlp  # 可选
```

## 📄 项目结构

```
project_1/
├── app.py              # FastAPI后端服务
├── static/
│   ├── index.html      # 主页面
│   └── test.html       # 测试页面
├── video_parser.py     # 视频解析工具
├── requirements.txt    # Python依赖
├── .env                # 环境变量配置
├── .env.example        # 配置示例
├── start.bat           # Windows启动脚本
└── README.md           # 使用说明
```

## 🔗 相关链接

- [豆包大模型官方文档](https://www.volcengine.com/docs/82379/1399008)
- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [yt-dlp项目地址](https://github.com/yt-dlp/yt-dlp)

## 📞 技术支持

如有问题，请查看：
1. 浏览器控制台（F12）的错误信息
2. 服务器终端的日志输出
3. 本文档的常见问题部分

---

**祝你使用愉快！** 🎉
