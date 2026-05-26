# Changelog

## V1.1 (2026-05-26)

### 新增
- `.env.example` 统一三层环境变量配置文档
- `CLAUDE.md` AI 辅助开发指引
- `README.md` 项目首页说明
- `API.md` 完整接口文档（22 个接口）
- `ai_layer/db.py` 统一数据库连接模块
- `ai_layer/tests/` 46 个单元测试 + 7 个 LLM 集成测试
- `backend/src/test/` 10 个 Spring Boot 单元测试
- Spring Boot demo 模式（H2 + 零 Redis），一条命令零依赖启动
- 融合权重 `weight_fusion_rule` / `weight_fusion_llm` 入库，可在线调参
- `CHANGELOG.md`

### 修复
- Vite 代理目标从 Flask :5000 改为 Spring Boot :8080，修复 CRUD 接口 404
- `_load_knowledge_from_db()` 中 `get_config()` 未 import 导致 MySQL 路径永远失败的 bug
- Spring Boot demo 模式中 Redis mock 导致 NPE 的问题
- H2 schema 缺少 `weight_range`、`season_info` 等字段，补齐到与 Entity 一致
- QaServiceImpl 中 H2 不支持 `MATCH AGAINST` 全文搜索的问题，增加异常兜底

### 优化
- 删除 `style.css` 死代码，全部 CSS 统一到 `hakka-theme.css` 变量体系
- Jackson 全局 `SNAKE_CASE` 序列化，删除 Python 侧 20 字段 camelCase 映射字典
- 小程序 `apiBaseUrl` 外提到 `app.js globalData`，生产部署一键切换
- 删除 6 条静态知识库兜底数据，DB 不可用时返回空列表
- 所有前端 View 硬编码颜色替换为 `hakka-theme.css` 变量
- 小程序全部 wxss/wxml/json 颜色统一为围屋红主题
- `landing.html` 颜色更新至 hakka 主题
- 使用说明书更新至 V1.1（demo 模式、环境变量、测试命令、GitHub 链接）

### 测试
- Python：46 单元 + 7 集成 = 53 个测试，全通过
- Java：10 个单元测试，全通过

---

## V1.0 (2026-05-22)

### 初始版本
- 四层架构：Vue 3 Web + 微信小程序 + Spring Boot + Python Flask
- 意图识别：LLM 两层分类 + 关键词规则兜底
- 融合推荐排序：规则式三维度打分 + LLM 语义增强 50/50 融合
- 多模型适配器：DeepSeek / ChatGLM-4 / 讯飞星火
- 智能问答 + 文案生成
- JWT Token 认证 + Redis 缓存
- MySQL 5 张核心表 + 种子数据
- 管理后台：知识库 / Prompt / 算法参数 CRUD
