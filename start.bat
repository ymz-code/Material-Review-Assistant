@echo off
echo 正在安装依赖...
pip install --upgrade "openai>=1.0"
pip install -r requirements.txt

echo 依赖安装完成，启动服务...
python app.py
