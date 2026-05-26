# 客家金柚AI智荐系统

> 大模型驱动 · 精准选柚 · 客家文化传承

基于 DeepSeek 大模型与规则式融合推荐算法的梅州客家金柚数字化展示与智能选品平台。聚焦 **AI 智荐推荐、智能问答、内容生成** 三大功能。

嘉应学院 · 大学生创新训练计划项目（2026.03 — 2027.03）

## 架构

```
Vue 3 Web (:3000) ──┐
                     ├──> Spring Boot (:8080) ──> Python Flask (:5000) ──> DeepSeek API
WeChat MiniApp ──────┘         │                        │
                          MySQL (:3306)            Intent Recognition
                          Redis (:6379)            Fusion Ranking
                                                   Content Generation
```

## 快速启动

### 演示模式（零外部依赖）

只需 JDK 17+ + Python 3.9+ + Node.js 18+：

```bash
# 终端 1：AI 算法层
export DEEPSEEK_API_KEY=sk-your-key    # 或 set DEEPSEEK_API_KEY=sk-xxx (Windows CMD)
pip install -r ai_layer/requirements.txt
python run.py

# 终端 2：后端（H2 内存数据库，无需 MySQL/Redis）
cd backend
mvn spring-boot:run -Dspring-boot.run.profiles=demo

# 终端 3：Web 前端
cd web
npm install
npm run dev
```

浏览器打开 http://localhost:3000

### 完整模式

需要 MySQL 8.0+ + Redis 7.0+。详见 [使用说明书](./使用说明书.md)。

## 测试

```bash
# 全部 46 个单元测试
python -m pytest ai_layer/tests/test_fusion_ranker.py ai_layer/tests/test_intent_recognizer.py -v

# LLM 集成测试（需要 DEEPSEEK_API_KEY）
python -m pytest ai_layer/tests/test_llm_integration.py -v
```

## 核心功能

| 功能 | 说明 |
|------|------|
| AI 智荐推荐 | 意图识别 + 大模型语义打分 + 规则式多因子评分融合排序 |
| 智能问答 | 金柚知识库检索 + LLM 生成回答，三层降级兜底 |
| 文案生成 | 电商详情页 / 朋友圈推文双场景 AI 创作 |
| 管理后台 | 知识库 / Prompt 模板 / 算法参数在线调优 |

## 技术栈

| 层 | 技术 |
|----|------|
| Web 前端 | Vue 3 · Vite · Vue Router · Pinia |
| 小程序 | 微信小程序原生框架 |
| 后端 | Spring Boot 3.2 · MyBatis-Plus · Redis |
| AI 层 | Python Flask · DeepSeek API · ChatGLM · 讯飞星火 |
| 数据库 | MySQL 8.0 · H2 (demo) |
| 算法 | 意图识别 · 融合排序 · 语义打分 · 推荐理由生成 |

## 项目结构

```
├── ai_layer/            # Python AI 算法层 (12 files + tests)
│   ├── fusion_ranker.py     # 融合推荐排序核心
│   ├── intent_recognizer.py # 意图识别
│   ├── llm_adapter.py       # 多模型适配器
│   └── tests/               # 46 单元 + 7 集成测试
├── backend/             # Spring Boot 后端 (42 files)
├── web/                 # Vue 3 Web 前端 (17 files)
├── miniapp/             # 微信小程序 (31 files)
├── init_db.sql          # 数据库建表 + 种子数据
├── .env.example          # 环境变量配置模板
└── 使用说明书.md          # 完整使用手册
```

## 文档

- [使用说明书](./使用说明书.md) — 完整安装、使用、管理指南
- [BRAND_GUIDELINES.md](./BRAND_GUIDELINES.md) — 品牌视觉规范
- [DESIGN_PHILOSOPHY.md](./DESIGN_PHILOSOPHY.md) — "金色围屋"设计哲学

## License

本项目为嘉应学院大学生创新训练计划项目，仅供学习交流使用。
