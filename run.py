"""
客家金柚AI智荐系统 — Python AI 算法层 HTTP API 服务入口

启动方式:
    # 开发模式
    python run.py

    # 生产模式（gunicorn）
    gunicorn -w 2 -b 0.0.0.0:5000 "run:app"

环境变量:
    DEEPSEEK_API_KEY     DeepSeek API Key（必需）
    CHATGLM_API_KEY      ChatGLM API Key（可选）
    SPARK_APP_ID         讯飞星火 AppId（可选）
    DB_HOST/PORT/USER/PASSWORD/NAME  MySQL 连接（可选，不设则用默认值回退）
"""

import sys
import os

# 确保 ai_layer 包可导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_layer.flask_app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
    )
