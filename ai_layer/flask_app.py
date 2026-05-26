"""
Flask 应用工厂
创建并配置 Flask 实例，注册蓝图，初始化 AI 服务。
"""

import logging
from flask import Flask
from flask_cors import CORS

from .flask_routes import api_bp, init_services

# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# 抑制第三方库的 DEBUG 日志
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

# ---------------------------------------------------------------------------
# Flask 应用工厂
# ---------------------------------------------------------------------------


def create_app() -> Flask:
    """创建并配置 Flask 应用实例"""
    app = Flask(__name__)

    # CORS 跨域（允许 Spring Boot 后端调用）
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # 注册 API 蓝图
    app.register_blueprint(api_bp)

    # 初始化 AI 服务（在首次请求前完成，避免请求内重复创建）
    with app.app_context():
        init_services()
        logging.getLogger("pomelo_api").info("AI 服务初始化完成")

    return app


# ---------------------------------------------------------------------------
# 直接运行入口
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = create_app()
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
    )
