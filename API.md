# API 接口文档

Base URL: `http://localhost:8080/api`

所有接口统一响应格式：

```json
{
  "code": 200,
  "data": { ... },
  "message": "success"
}
```

| code | 说明 |
|:----:|------|
| 200  | 成功 |
| 400  | 参数错误 |
| 401  | 未认证 |
| 403  | 权限不足 |
| 404  | 资源不存在 |
| 500  | 服务器错误 |

---

## 1. 健康检查

```
GET /api/health
```

**无需认证**

**响应** `data.status = "running"`

---

## 2. AI 智荐推荐

```
POST /api/recommend
```

**无需认证**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| query | string | ✓ | 用户选购需求，如"200元中秋送礼" |
| userId | number | | 用户ID |
| sessionId | string | | 会话ID，用于多轮对话 |
| skipCache | boolean | | 跳过Redis缓存 |

**响应 data：**

| 字段 | 类型 | 说明 |
|------|------|------|
| intent.intent | string | BUY / QA |
| intent.confidence | number | 置信度 0-1 |
| intent.constraints | object | 预算/场景/送礼对象 |
| recommendations[] | array | 推荐金柚列表 |
| recommendations[].pomelo_name | string | 品名 |
| recommendations[].final_score | number | 融合分数 |
| recommendations[].reason | string | 推荐理由 |
| count | number | 推荐数量 |
| costMs | number | 耗时(ms) |
| fromCache | boolean | 是否来自缓存 |

**示例：**

```bash
curl -X POST http://localhost:8080/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"query":"200元中秋送礼客家亲友"}'
```

---

## 3. 智能问答

```
POST /api/qa
```

**无需认证**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| question | string | ✓ | 用户问题 |
| userId | number | | 用户ID |
| sessionId | string | | 会话ID |

**响应：**

| 字段 | 说明 |
|------|------|
| answer | 回答内容 |
| source | "knowledge_base" / "llm" / "fallback" |
| intent | 意图识别结果 |
| refs[] | 知识库引用（仅 knowledge_base 来源） |

---

## 4. 文案生成

```
POST /api/content
```

**无需认证**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| scene | string | ✓ | "ecommerce" 或 "social" |
| pomeloName | string | | 金柚品名，默认"客家金柚" |
| prompt | string | | 自定义要求 |
| style | string | | 文案风格 |

**响应：**

| 字段 | 说明 |
|------|------|
| content | 生成的文案 |
| scene | 场景类型 |
| pomelo_name | 金柚品名 |
| created_at | 生成时间 |

---

## 5. 意图识别（独立）

```
POST /api/intent
```

**无需认证**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| query | string | ✓ | 用户输入 |

**响应 data：**

| 字段 | 说明 |
|------|------|
| intent | BUY / QA |
| confidence | 置信度 0-1 |
| constraints | 预算/场景/送礼对象等 |
| is_confident | 是否需要二次确认 |
| keywords[] | 提取的关键词 |

---

## 6. 用户系统

### 登录

```
POST /api/login
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| code | string | ✓ | 微信 wx.login() 返回的 code |

**响应：** `{ token, userId, nickname, avatarUrl }`

### 获取个人信息

```
GET /api/user
Authorization: Bearer <token>
```

### 修改个人信息

```
PUT /api/user
Authorization: Bearer <token>
```

| 参数 | 类型 | 说明 |
|------|------|------|
| nickname | string | 昵称 |
| avatarUrl | string | 头像URL |
| phone | string | 手机号 |

### 浏览历史

```
GET /api/user/history
Authorization: Bearer <token>
```

---

## 7. 知识库管理

### 获取列表

```
GET /api/knowledge
GET /api/knowledge?category=沙田柚&keyword=梅县
```

### 获取单条

```
GET /api/knowledge/{id}
```

### 新增（管理员）

```
POST /api/knowledge
Authorization: Bearer <admin-token>
```

**Body：** `{ pomeloName, category, origin, priceRange, tasteDescription, ... }`

### 修改（管理员）

```
PUT /api/knowledge/{id}
Authorization: Bearer <admin-token>
```

### 删除（管理员）

```
DELETE /api/knowledge/{id}
Authorization: Bearer <admin-token>
```

---

## 8. Prompt 模板管理

```
GET    /api/prompt              # 获取列表
GET    /api/prompt?scene=BUY    # 按场景筛选
POST   /api/prompt              # 新增（Admin）
PUT    /api/prompt/{id}         # 修改（Admin）
DELETE /api/prompt/{id}         # 删除（Admin）
```

---

## 9. 算法参数管理

```
GET /api/algo-params            # 获取全部参数
GET /api/algo-params?group=WEIGHT # 按分组筛选
PUT /api/algo-params/{id}       # 修改参数值（Admin）
```

**已有参数：**

| param_key | 默认值 | 分组 | 说明 |
|-----------|:-----:|------|------|
| weight_requirement_match | 0.40 | REQUIREMENT_MATCH | 需求匹配度权重 |
| weight_scene_fit | 0.35 | SCENE_FIT | 场景适配度权重 |
| weight_hakka_feature | 0.25 | HAKKA_FEATURE | 客家特色贴合度权重 |
| weight_fusion_rule | 0.50 | FUSION | 融合公式-规则分权重 |
| weight_fusion_llm | 0.50 | FUSION | 融合公式-LLM分权重 |
