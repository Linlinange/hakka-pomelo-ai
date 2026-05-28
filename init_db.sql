-- ============================================================
-- 客家金柚特色农产品AI智荐系统 - MySQL数据库初始化脚本
-- 版本：V1.0
-- 说明：包含用户、金柚知识库、Prompt库、算法参数、大模型日志5张核心表
-- ============================================================

CREATE DATABASE IF NOT EXISTS `golden_pomelo_ai` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `golden_pomelo_ai`;

-- ============================================================
-- 1. 用户表（sys_user）
--    存储微信小程序用户基本信息，支持后续用户画像分析
-- ============================================================
DROP TABLE IF EXISTS `sys_user`;
CREATE TABLE `sys_user` (
    `id`                BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '用户主键ID',
    `openid`            VARCHAR(128)    NOT NULL                 COMMENT '微信小程序OpenID，唯一标识',
    `unionid`           VARCHAR(128)    DEFAULT NULL             COMMENT '微信开放平台UnionID',
    `nickname`          VARCHAR(64)     DEFAULT NULL             COMMENT '用户昵称',
    `avatar_url`        VARCHAR(512)    DEFAULT NULL             COMMENT '微信头像URL',
    `phone`             VARCHAR(20)     DEFAULT NULL             COMMENT '手机号码',
    `gender`            TINYINT(1)      DEFAULT 0                COMMENT '性别：0-未知 1-男 2-女',
    `province`          VARCHAR(32)     DEFAULT NULL             COMMENT '省份（用于客家地区用户分析）',
    `city`              VARCHAR(32)     DEFAULT NULL             COMMENT '城市',
    `last_login_time`   DATETIME        DEFAULT NULL             COMMENT '最近登录时间',
    `status`            TINYINT(1)      DEFAULT 1                COMMENT '用户状态：0-禁用 1-正常',
    `remark`            VARCHAR(512)    DEFAULT NULL             COMMENT '备注',
    `create_time`       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted`        TINYINT(1)      DEFAULT 0                COMMENT '逻辑删除：0-未删除 1-已删除',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_openid` (`openid`),
    KEY `idx_phone` (`phone`),
    KEY `idx_status` (`status`),
    KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统用户表';

-- ============================================================
-- 2. 金柚知识库表（golden_pomelo_knowledge）
--    存储梅州客家金柚的核心知识数据，是智能问答与推荐的数据基础
--    字段设计覆盖：产地、规格、种植工艺、客家文化关联、辨别保鲜、食用搭配等
-- ============================================================
DROP TABLE IF EXISTS `golden_pomelo_knowledge`;
CREATE TABLE `golden_pomelo_knowledge` (
    `id`                        BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '知识条目主键ID',
    `pomelo_name`               VARCHAR(128)    NOT NULL                 COMMENT '金柚品名（如"梅州沙田柚""蜜柚"）',
    `category`                  VARCHAR(32)     DEFAULT NULL             COMMENT '品类：沙田柚/蜜柚/文旦柚/金柚深加工品',
    `origin`                    VARCHAR(256)    NOT NULL                 COMMENT '产地（如"梅州市梅县区松口镇"）',
    `specification`             VARCHAR(128)    DEFAULT NULL             COMMENT '规格描述（如果径/果重/包装规格）',
    `weight_range`              VARCHAR(64)     DEFAULT NULL             COMMENT '单果重量范围（如"1.2kg-1.8kg"）',
    `price_range`               VARCHAR(64)     DEFAULT NULL             COMMENT '参考价格区间（如"30-80元/箱"）',
    `season_info`               VARCHAR(128)    DEFAULT NULL             COMMENT '上市季节与赏味期（如"11月至次年3月"）',
    `cultivation_process`       TEXT            DEFAULT NULL             COMMENT '种植工艺及特色（如有机种植、客家传统农法等）',
    `hakka_culture_relation`    TEXT            DEFAULT NULL             COMMENT '客家文化关联（如金柚与客家民俗、节庆、待客礼仪）',
    `identification_tips`       TEXT            DEFAULT NULL             COMMENT '辨别挑选方法（如皮色、果形、掂重、闻香）',
    `preservation_method`       TEXT            DEFAULT NULL             COMMENT '保鲜储藏方法',
    `edible_pairing`            TEXT            DEFAULT NULL             COMMENT '食用搭配建议（如金柚+蜂蜜、金柚入菜等）',
    `nutritional_value`         TEXT            DEFAULT NULL             COMMENT '营养价值说明',
    `taste_description`         VARCHAR(512)    DEFAULT NULL             COMMENT '口感描述（甜度、水分、化渣度）',
    `story_content`             TEXT            DEFAULT NULL             COMMENT '品牌故事/人文故事（用于内容生成）',
    `image_url`                 VARCHAR(512)    DEFAULT NULL             COMMENT '金柚图片URL（对象存储路径）',
    `tags`                      VARCHAR(512)    DEFAULT NULL             COMMENT '标签（逗号分隔，如"送礼,团圆,养生"）',
    `gift_scene_tags`           VARCHAR(256)    DEFAULT NULL             COMMENT '送礼场景标签（如"中秋送礼,春节年货,探亲访友"）',
    `score_requirement_match`   DECIMAL(3,2)    DEFAULT 5.00             COMMENT '需求匹配度基础评分（1-10分）',
    `score_scene_fit`           DECIMAL(3,2)    DEFAULT 5.00             COMMENT '场景适配度基础评分（1-10分）',
    `score_hakka_feature`       DECIMAL(3,2)    DEFAULT 5.00             COMMENT '客家特色贴合度基础评分（1-10分）',
    `view_count`                INT             DEFAULT 0                COMMENT '浏览次数',
    `rec_count`                 INT             DEFAULT 0                COMMENT '被推荐次数',
    `status`                    TINYINT(1)      DEFAULT 1                COMMENT '状态：0-下架 1-上架',
    `create_time`               DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`               DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted`                TINYINT(1)      DEFAULT 0                COMMENT '逻辑删除：0-未删除 1-已删除',
    PRIMARY KEY (`id`),
    KEY `idx_category` (`category`),
    KEY `idx_origin` (`origin`(64)),
    KEY `idx_tags` (`tags`(64)),
    KEY `idx_gift_scene_tags` (`gift_scene_tags`(64)),
    KEY `idx_status` (`status`),
    KEY `idx_score_requirement_match` (`score_requirement_match`),
    KEY `idx_score_scene_fit` (`score_scene_fit`),
    KEY `idx_score_hakka_feature` (`score_hakka_feature`),
    FULLTEXT KEY `ft_name_story` (`pomelo_name`, `story_content`, `cultivation_process`, `edible_pairing`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='金柚知识库表';

-- ============================================================
-- 3. 金柚Prompt库表（

-- FULLTEXT 索引：中文全文搜索（需要 MySQL 5.7.6+，InnoDB ngram parser）
ALTER TABLE `golden_pomelo_knowledge`
ADD FULLTEXT INDEX `ft_pomelo_search`
(`pomelo_name`, `taste_description`, `hakka_culture_relation`, `cultivation_process`, `edible_pairing`)
WITH PARSER ngram;

pomelo_prompt_library）
--    管理所有AI调用的Prompt模板，支持版本迭代与场景分类
--    场景分类：选购推荐 / 知识问答 / 内容生成
-- ============================================================
DROP TABLE IF EXISTS `pomelo_prompt_library`;
CREATE TABLE `pomelo_prompt_library` (
    `id`                BIGINT          NOT NULL AUTO_INCREMENT  COMMENT 'Prompt模板主键ID',
    `prompt_name`       VARCHAR(128)    NOT NULL                 COMMENT 'Prompt模板名称',
    `scene_category`    VARCHAR(32)     NOT NULL                 COMMENT '场景分类：BUY-选购推荐 QA-知识问答 GEN-内容生成',
    `applicable_scene`  VARCHAR(256)    NOT NULL                 COMMENT '具体适用场景描述（如"中秋送礼推荐""柚皮食疗问答"）',
    `prompt_template`   TEXT            NOT NULL                 COMMENT 'Prompt模板（含占位符，如{{user_input}}{{knowledge}}）',
    `variables_schema`  JSON            DEFAULT NULL             COMMENT '模板占位符变量定义（JSON格式：{变量名:说明}）',
    `system_role_desc`  VARCHAR(512)    DEFAULT NULL             COMMENT 'System角色设定描述（注入大模型）',
    `version`           VARCHAR(16)     NOT NULL DEFAULT '1.0.0' COMMENT '版本号（语义化版本）',
    `is_current`        TINYINT(1)      DEFAULT 0                COMMENT '是否为当前使用版本：0-否 1-是（同场景仅一条为1）',
    `priority`          INT             DEFAULT 0                COMMENT '优先级（同场景多版本时降级排序用）',
    `max_tokens`        INT             DEFAULT 1024             COMMENT '大模型最大返回Token数',
    `temperature`       DECIMAL(3,2)    DEFAULT 0.70             COMMENT '模型温度参数（0-1）',
    `status`            TINYINT(1)      DEFAULT 1                COMMENT '状态：0-停用 1-启用',
    `remark`            VARCHAR(512)    DEFAULT NULL             COMMENT '备注说明',
    `create_time`       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_name_version` (`prompt_name`, `version`),
    KEY `idx_scene_category` (`scene_category`),
    KEY `idx_is_current` (`is_current`),
    KEY `idx_status_priority` (`status`, `priority`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='金柚Prompt库表';

-- ============================================================
-- 4. 智荐算法参数表（algo_rule_params）
--    存储大模型+规则式融合推荐排序的多因子权重配置
--    核心维度：需求匹配度 / 场景适配度 / 客家特色贴合度
-- ============================================================
DROP TABLE IF EXISTS `algo_rule_params`;
CREATE TABLE `algo_rule_params` (
    `id`                BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '参数主键ID',
    `param_key`         VARCHAR(64)     NOT NULL                 COMMENT '参数键（唯一标识，如"weight_requirement_match"）',
    `param_name`        VARCHAR(128)    NOT NULL                 COMMENT '参数中文名称（如"需求匹配度权重"）',
    `param_value`       DECIMAL(5,3)    NOT NULL DEFAULT 0.000   COMMENT '参数数值',
    `param_type`        VARCHAR(32)     NOT NULL DEFAULT 'WEIGHT' COMMENT '参数类型：WEIGHT-权重 THRESHOLD-阈值 COEFFICIENT-系数',
    `param_group`       VARCHAR(64)     NOT NULL                 COMMENT '参数分组：REQUIREMENT_MATCH-需求匹配 / SCENE_FIT-场景适配 / HAKKA_FEATURE-客家特色 / LLM_ADAPT-大模型适配',
    `param_range`       VARCHAR(64)     DEFAULT NULL             COMMENT '参数取值范围说明（如"0.00-1.00"）',
    `description`       VARCHAR(512)    DEFAULT NULL             COMMENT '参数详细说明与调参指引',
    `status`            TINYINT(1)      DEFAULT 1                COMMENT '状态：0-停用 1-启用',
    `sort_order`        INT             DEFAULT 0                COMMENT '同分组内排序',
    `create_time`       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_param_key` (`param_key`),
    KEY `idx_param_group` (`param_group`),
    KEY `idx_param_type` (`param_type`),
    KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='智荐算法参数表';

-- ============================================================
-- 5. 大模型调用日志表（llm_invoke_log）
--    记录每次大模型调用的完整链路，用于Prompt迭代优化与效果分析
-- ============================================================
DROP TABLE IF EXISTS `llm_invoke_log`;
CREATE TABLE `llm_invoke_log` (
    `id`                    BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '日志主键ID',
    `user_id`               BIGINT          DEFAULT NULL             COMMENT '关联用户ID（未登录时为空）',
    `session_id`            VARCHAR(64)     NOT NULL                 COMMENT '会话ID（用于串联多轮对话）',
    `scene_category`        VARCHAR(32)     NOT NULL                 COMMENT '场景分类：BUY-选购推荐 QA-知识问答 GEN-内容生成',
    `intent_type`           VARCHAR(64)     DEFAULT NULL             COMMENT '意图识别结果（如"送礼选购""营养问答""柚皮菜谱"）',
    `intent_confidence`     DECIMAL(4,3)    DEFAULT NULL             COMMENT '意图识别置信度（0.000-1.000）',
    `original_input`        TEXT            NOT NULL                 COMMENT '用户原始输入文本',
    `extracted_keywords`    VARCHAR(512)    DEFAULT NULL             COMMENT '提取的关键词（JSON数组）',
    `extracted_constraints` VARCHAR(512)    DEFAULT NULL             COMMENT '提取的约束条件（JSON，如价格区间/场景/人群）',
    `prompt_template_id`    BIGINT          DEFAULT NULL             COMMENT '使用的Prompt模板ID（关联pomelo_prompt_library.id）',
    `prompt_version`        VARCHAR(16)     DEFAULT NULL             COMMENT '使用的Prompt版本号',
    `assembled_prompt`      TEXT            DEFAULT NULL             COMMENT '拼装后的完整Prompt（发给大模型的终版）',
    `model_name`            VARCHAR(64)     NOT NULL                 COMMENT '调用模型名称（如"chatglm-4-lite""spark-lite"）',
    `model_response`        MEDIUMTEXT      DEFAULT NULL             COMMENT '大模型原始返回结果',
    `parsed_result`         JSON            DEFAULT NULL             COMMENT '结构化解析后的结果（JSON格式，供前端消费）',
    `token_count_input`     INT             DEFAULT 0                COMMENT '输入消耗Token数',
    `token_count_output`    INT             DEFAULT 0                COMMENT '输出消耗Token数',
    `response_time_ms`      INT             DEFAULT 0                COMMENT '大模型响应耗时（毫秒）',
    `total_cost_ms`         INT             DEFAULT 0                COMMENT '本次调用总耗时（含Prompt拼接+网络+解析，毫秒）',
    `invoke_status`         TINYINT(1)      DEFAULT 1                COMMENT '调用状态：1-成功 2-失败 3-超时 4-限流',
    `error_message`         VARCHAR(1024)   DEFAULT NULL             COMMENT '失败/异常时的错误信息',
    `retry_count`           TINYINT         DEFAULT 0                COMMENT '重试次数',
    `user_feedback`         TINYINT(1)      DEFAULT NULL             COMMENT '用户反馈：0-无反馈 1-有用 2-无用',
    `feedback_remark`       VARCHAR(512)    DEFAULT NULL             COMMENT '用户反馈备注',
    `create_time`           DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间（即调用时间）',
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_session_id` (`session_id`),
    KEY `idx_scene_category` (`scene_category`),
    KEY `idx_intent_type` (`intent_type`),
    KEY `idx_model_name` (`model_name`),
    KEY `idx_invoke_status` (`invoke_status`),
    KEY `idx_prompt_template_id` (`prompt_template_id`),
    KEY `idx_create_time` (`create_time`),
    KEY `idx_user_feedback` (`user_feedback`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='大模型调用日志表';

-- ============================================================
-- 初始化：智荐算法参数默认配置数据
-- 三维度权重合计为1.0，融合权重(规则+LLM)合计为1.0，可在线动态调整
-- ============================================================

-- 需求匹配度维度
INSERT INTO `algo_rule_params` (`param_key`, `param_name`, `param_value`, `param_type`, `param_group`, `param_range`, `description`, `sort_order`) VALUES
('weight_requirement_match',   '需求匹配度权重',           0.40, 'WEIGHT',     'REQUIREMENT_MATCH', '0.00-1.00', '大模型语义理解后的关键词与金柚属性匹配权重',  1),
('weight_scene_fit',           '场景适配度权重',           0.35, 'WEIGHT',     'SCENE_FIT',         '0.00-1.00', '用户送礼/自用/宴请等场景与金柚的适配权重',     1),
('weight_hakka_feature',       '客家特色贴合度权重',       0.25, 'WEIGHT',     'HAKKA_FEATURE',     '0.00-1.00', '金柚与客家文化、地域特色的贴合度权重',         1),
('threshold_min_score',        '推荐最低评分阈值',         3.00, 'THRESHOLD',  'REQUIREMENT_MATCH', '0.00-10.00','低于此分数的金柚不进入推荐列表',              2),
('threshold_intent_confidence','意图识别最低置信度',       0.60, 'THRESHOLD',  'LLM_ADAPT',         '0.00-1.00', '意图识别置信度低于此值时触发二次确认',         1),
('coefficient_view_decay',     '浏览次数衰减系数',         0.15, 'COEFFICIENT','REQUIREMENT_MATCH', '0.00-1.00', '避免高浏览量金柚过度霸榜的衰减因子',           3),
('llm_timeout_ms',             '大模型调用超时阈值(ms)',   8000, 'THRESHOLD',  'LLM_ADAPT',         '1-30000',    '超过此时间未返回视为超时，触发降级逻辑',         2),
('llm_max_retry',              '大模型调用最大重试次数',    2,    'THRESHOLD',  'LLM_ADAPT',         '0-5',        '调用失败后的最大重试次数',                      3),
('weight_fusion_rule',         '融合排序-规则权重',         0.50, 'WEIGHT',     'FUSION',            '0.00-1.00', '融合公式中规则式打分的权重（与LLM权重相加应为1.0）', 1),
('weight_fusion_llm',          '融合排序-LLM权重',          0.50, 'WEIGHT',     'FUSION',            '0.00-1.00', '融合公式中大模型语义打分的权重（与规则权重相加应为1.0）', 2);

-- ============================================================
-- 初始化：金柚Prompt库示例数据
-- ============================================================

-- 选购推荐场景
INSERT INTO `pomelo_prompt_library` (`prompt_name`, `scene_category`, `applicable_scene`, `prompt_template`, `variables_schema`, `system_role_desc`, `version`, `is_current`, `priority`, `max_tokens`, `temperature`, `remark`) VALUES
('金柚选购推荐-标准版', 'BUY', '用户提供选购需求，系统推荐合适金柚',
 '你是一位精通梅州客家金柚的专业导购顾问。请根据以下用户需求推荐最合适的金柚产品：\n\n用户需求：{{user_input}}\n\n可选金柚数据：{{pomelo_list}}\n\n请按以下维度综合评分推荐（各维度满分10分）：\n1. 需求匹配度：金柚属性与用户需求的契合程度\n2. 场景适配度：金柚是否适配用户的送礼/自用场景\n3. 客家特色贴合度：金柚的客家文化内涵与地域特色\n\n请以JSON格式返回Top5推荐结果，每项包含：pomelo_id、推荐理由（80字内）、三维度各自评分。',
 '{"user_input":"用户原始输入","pomelo_list":"符合条件的候选金柚JSON数组"}',
 '你是梅州客家金柚文化传承人与专业导购，熟悉每个产区的金柚特色与客家民俗。回答需温暖、专业、有客家味。',
 '1.0.0', 1, 10, 1536, 0.70, '选购推荐主Prompt模板'),

-- 知识问答场景
('金柚知识问答-标准版', 'QA', '用户询问金柚相关知识（营养、保存、辨别等）',
 '你是客家金柚领域的资深专家。请基于以下知识库内容回答用户问题：\n\n用户问题：{{user_input}}\n\n相关知识：{{knowledge_context}}\n\n要求：\n1. 回答专业准确，融入客家文化元素\n2. 若知识库无法覆盖，请基于常识补充并注明"仅供参考"\n3. 回答字数控制在200字以内',
 '{"user_input":"用户问题","knowledge_context":"从知识库检索的相关条目"}',
 '你是梅州客家金柚非遗传承人与农业专家，精通金柚种植、保鲜、食疗、文化典故。',
 '1.0.0', 1, 10, 1024, 0.65, '知识问答主Prompt模板'),

-- 内容生成场景
('金柚内容生成-电商文案', 'GEN', '为指定金柚生成电商展示文案/朋友圈推广语',
 '请为以下梅州客家金柚生成一段吸引人的展示文案：\n\n金柚信息：{{pomelo_info}}\n使用场景：{{content_scene}}\n风格要求：{{style}}\n\n要求：\n1. 突出客家文化底蕴与产地特色\n2. 文案字数{{word_limit}}字以内\n3. 适合在{{platform}}平台展示',
 '{"pomelo_info":"金柚基本信息","content_scene":"使用场景（详情页/朋友圈/海报）","style":"文案风格","word_limit":"字数限制","platform":"展示平台（小程序/朋友圈/公众号）"}',
 '你是精通农产品电商文案的客家文化传播者，擅长将传统农产品与现代消费美学结合。',
 '1.0.0', 1, 10, 1024, 0.80, '内容生成主Prompt模板');

-- ============================================================
-- 完成

-- ============================================================
-- 6. 会话消息表（conversation_message）
--    存储用户对话历史，支持多轮对话恢复
-- ============================================================
DROP TABLE IF EXISTS `conversation_message`;
CREATE TABLE `conversation_message` (
    `id`                BIGINT          NOT NULL AUTO_INCREMENT  COMMENT '消息主键ID',
    `user_id`           BIGINT          DEFAULT NULL             COMMENT '用户ID（匿名用户为NULL）',
    `session_id`        VARCHAR(64)     NOT NULL                 COMMENT '会话ID，由前端生成',
    `role`              VARCHAR(16)     NOT NULL                 COMMENT '角色：user / ai',
    `msg_type`          VARCHAR(16)     DEFAULT 'text'           COMMENT '消息类型：text / recommend',
    `content`           TEXT                                     COMMENT '消息文本内容',
    `metadata_json`     JSON            DEFAULT NULL             COMMENT '扩展元数据（推荐结果JSON等）',
    `create_time`       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '消息创建时间',
    PRIMARY KEY (`id`),
    INDEX `idx_session_time` (`session_id`, `create_time`),
    INDEX `idx_user_time` (`user_id`, `create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会话消息表';
-- ============================================================
