# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

客家金柚特色农产品AI智荐系统 (Hakka Golden Pomelo AI Recommendation System) — a university innovation project (嘉应学院). A digital showcase and intelligent recommendation platform for Meizhou Hakka golden pomelos, built around AI-powered recommendations, Q&A, and content generation. No commercial transactions or payments.

## Commands

All environment variables are documented in `.env.example`.

### Python AI Layer (port 5000)

```bash
# Install deps
pip install -r ai_layer/requirements.txt

# Dev server
set DEEPSEEK_API_KEY=sk-<key>   # Windows CMD
python run.py

# Production
gunicorn -w 2 -b 0.0.0.0:5000 "run:app"

# Run fusion ranking demo (no API key needed)
python -m ai_layer.demo_fusion
```

### Spring Boot Backend (port 8080)

```bash
cd backend
mvn spring-boot:run
```

Environment: JDK 17+, Maven 3.6+, MySQL 8.0, Redis 7.0. Default MySQL connection expects `root` with empty password on `127.0.0.1:3306`. Edit `backend/src/main/resources/application.properties` if different.

### Vue 3 Web Frontend (port 3000)

```bash
cd web
npm install        # first time only
npm run dev        # dev server
npm run build      # production build
```

### Database

```bash
mysql -u root -p < init_db.sql
```

Creates database `golden_pomelo_ai` with 5 tables: `sys_user`, `golden_pomelo_knowledge`, `pomelo_prompt_library`, `algo_rule_params`, `llm_invoke_log`.

## Architecture

```
Vue 3 Web (:3000) ──┐
                     ├──> Spring Boot (:8080) ──> Python Flask (:5000) ──> DeepSeek API
WeChat MiniApp ──────┘         │                        │
                          MySQL (:3306)            Intent Recognition
                          Redis (:6379)            Fusion Ranking
                                                   Content Generation
```

**Dev routing**: The Vite dev server (`vite.config.js`) proxies `/api` to Spring Boot on port 8080, which then calls Flask on port 5000 for AI features. Both must be running for full functionality.

### Layers

**`ai_layer/`** — Python Flask AI algorithm layer. 11 files. Core modules:
- `intent_recognizer.py` — Two-tier intent classification: LLM-based (reads prompt templates from `pomelo_prompt_library` table, falls back to built-in defaults) + keyword-weighted rule-based fallback when LLM is unavailable. Classifies input as BUY or QA and extracts constraints (budget, scene, recipient, etc.).
- `fusion_ranker.py` — Hybrid recommendation engine: rule-based 3-factor scoring (price match × 0.40 + scene fit × 0.35 + Hakka feature × 0.25, weights loaded from `algo_rule_params` table) combined with LLM semantic scoring (50/50 fusion). Top-N pre-filtered by rule score before LLM evaluation. Top-3 get personalized recommendation reasons.
- `llm_adapter.py` — Multi-provider LLM abstraction: `DeepSeekAdapter`, `ChatGLM4Adapter`, `SparkAdapter` all implement `LLMAdapter.invoke()` with exponential backoff retry. `create_adapter()` factory selects by model name. Default: DeepSeek.
- `config.py` — All config via environment variables. `DEEPSEEK_API_KEY` is the only required one for full functionality. DB credentials for AI layer's direct MySQL reads also from env vars.
- `flask_routes.py` — 6 endpoints: `/api/recommend`, `/api/qa`, `/api/intent`, `/api/content`, `/api/knowledge` (read-only, with static fallback data), `/api/health`. Content generation uses higher temperature (0.85) for creative output.

**`backend/`** — Spring Boot 3.2.5 Java backend (42 files). Standard layered architecture:
- `controller/` — REST controllers: Recommend, Qa, Content, Knowledge, Prompt, AlgoParams, User
- `service/impl/` — RecommendServiceImpl (Redis caching with 30-min TTL, MySQL candidate recall, delegates to Flask for AI), QaServiceImpl, ContentServiceImpl
- `mapper/` — MyBatis-Plus mappers for 5 tables
- `utils/HttpUtils.java` — HTTP client to Flask with retry (2 attempts, exponential backoff), structured logging, and response unwrapping from Flask's `{code, data, message}` envelope
- `config/SecurityConfig.java` — JWT token-based auth via Redis token storage
- Redis used for: recommend result caching, token storage

**`web/`** — Vue 3 + Vite + Vue Router + Pinia (17 source files):
- `src/router/index.js` — 7 routes: home, chat (AI recommend), content (copy generation), detail/:id, login, profile, admin
- `src/api/request.js` — Unified fetch wrapper, auto-attaches Bearer token, unwraps `{code: 200, data}` envelope
- `src/stores/user.js` — Pinia store for auth state (token/userId/nickname), persisted to localStorage
- `src/views/` — 7 page components, ChatView.vue is the core recommend/QA interface

**`miniapp/`** — WeChat Mini Program (31 files). Mirrors web functionality: index (home), recommend (chat bubbles with buy/QA mode), content (copy generation), mine (profile + history), plus login, admin, detail pages. Tab bar: 首页, AI智荐, 文案, 我的. Uses `wx.request` via `utils/request.js`.

### Database schema (init_db.sql)

5 tables in `golden_pomelo_ai`:
- `sys_user` — WeChat OAuth users (openid, unionid, profile fields)
- `golden_pomelo_knowledge` — Pomelo knowledge base with 3 pre-scored dimensions (requirement_match, scene_fit, hakka_feature), gift scene tags, cultural descriptions, cultivation/preservation/nutrition text fields
- `pomelo_prompt_library` — Versioned LLM prompt templates by scene_category (INTENT, RECOMMEND, QA), with `is_current` and `priority` for A/B switching
- `algo_rule_params` — Runtime-tunable algorithm parameters (3 weight dimensions, editable from admin UI)
- `llm_invoke_log` — Audit log for every LLM call

### Brand & Design

The project has a formal design system defined in `BRAND_GUIDELINES.md` and `DESIGN_PHILOSOPHY.md`. Key tokens:
- Primary: 金柚金 `#d4a843`, 客家米白 `#f6f3ea` (page bg), 柚皮红 `#e8684a` (accent), 客家棕 `#3d3226` (text)
- Typography: PingFang SC / Microsoft YaHei, rpx-based sizing (38/30/28/24)
- Design metaphor: Hakka "围龙屋" (dragon-roundhouse) — circular, layered spatial logic, "round within square"
- CSS variables defined in `web/src/assets/style.css` (`:root`) and `miniapp/app.wxss`

### Admin system

Default `userId=1` has admin privileges. Admin UI (web: `/admin`, miniapp: `pages/admin`) manages knowledge entries, Prompt templates, and algorithm parameters — all hot-reloaded (AI layer reads from DB with 5-min cache TTL).

### Key dependencies

- Flask routes: `requests`, `pymysql`, `flask`, `flask-cors`, `gunicorn`
- Spring Boot: spring-boot-starter-web, mybatis-plus 3.5.6, mysql-connector, redis (jedis), lombok, jackson
- Web: vue 3.4, vue-router 4.3, pinia 2.1, vite 5.4
- External: DeepSeek API (required), ChatGLM and 讯飞星火 (optional)
