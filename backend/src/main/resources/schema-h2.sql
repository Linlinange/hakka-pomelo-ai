-- H2 内存数据库初始化脚本（演示环境）
CREATE TABLE IF NOT EXISTS sys_user (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    openid VARCHAR(128) NOT NULL,
    nickname VARCHAR(64),
    avatar_url VARCHAR(512),
    phone VARCHAR(20),
    gender TINYINT DEFAULT 0,
    status TINYINT DEFAULT 1,
    last_login_time TIMESTAMP,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted TINYINT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS golden_pomelo_knowledge (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    pomelo_name VARCHAR(128) NOT NULL,
    category VARCHAR(32),
    origin VARCHAR(256),
    specification VARCHAR(128),
    price_range VARCHAR(64),
    taste_description VARCHAR(512),
    hakka_culture_relation TEXT,
    gift_scene_tags VARCHAR(256),
    tags VARCHAR(256),
    image_url VARCHAR(512),
    score_requirement_match DECIMAL(3,2) DEFAULT 5.00,
    score_scene_fit DECIMAL(3,2) DEFAULT 5.00,
    score_hakka_feature DECIMAL(3,2) DEFAULT 5.00,
    view_count INT DEFAULT 0,
    status TINYINT DEFAULT 1,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted TINYINT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pomelo_prompt_library (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    prompt_name VARCHAR(128) NOT NULL,
    scene_category VARCHAR(32) NOT NULL,
    applicable_scene VARCHAR(256),
    prompt_template TEXT NOT NULL,
    system_role_desc VARCHAR(512),
    version VARCHAR(16) DEFAULT '1.0.0',
    is_current TINYINT DEFAULT 0,
    priority INT DEFAULT 0,
    max_tokens INT DEFAULT 1024,
    temperature DECIMAL(3,2) DEFAULT 0.70,
    status TINYINT DEFAULT 1,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS algo_rule_params (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    param_key VARCHAR(64) NOT NULL,
    param_name VARCHAR(128) NOT NULL,
    param_value DECIMAL(5,3) DEFAULT 0.000,
    param_type VARCHAR(32) DEFAULT 'WEIGHT',
    param_group VARCHAR(64) NOT NULL,
    param_range VARCHAR(64),
    description VARCHAR(512),
    status TINYINT DEFAULT 1,
    sort_order INT DEFAULT 0,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS llm_invoke_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT,
    session_id VARCHAR(64) NOT NULL,
    scene_category VARCHAR(32) NOT NULL,
    intent_type VARCHAR(64),
    original_input TEXT NOT NULL,
    parsed_result TEXT,
    model_name VARCHAR(64) DEFAULT 'deepseek-chat',
    invoke_status TINYINT DEFAULT 1,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 初始数据：金柚知识库
INSERT INTO golden_pomelo_knowledge (pomelo_name, category, origin, price_range, taste_description, hakka_culture_relation, gift_scene_tags, tags, score_requirement_match, score_scene_fit, score_hakka_feature) VALUES
('梅县松口沙田柚·金奖优选', '沙田柚', '梅州市梅县区松口镇', '88-128元/箱', '清甜化渣、蜜香浓郁、回甘持久', '松口是客家人下南洋的起点，沙田柚随客家人远渡重洋名扬海外，中秋赏月必备', '中秋送礼,春节年货,团圆家宴,探亲访友', '金奖,送礼首选,非遗工艺,松口古镇', 8.5, 9.0, 9.5),
('大埔蜜柚·生态红肉', '蜜柚', '梅州市大埔县', '45-68元/箱', '果肉绯红、酸甜适口、汁水丰盈', '大埔是客家香格里拉，红肉蜜柚象征客家人热情好客的红心', '日常送礼,尝鲜自用,家庭分享', '高性价比,红肉,生态种植,大埔', 7.0, 6.5, 7.0),
('梅州金柚·客家情礼盒', '沙田柚', '梅州市梅江区', '68-98元/盒', '果肉晶莹、蜜甜无渣、香气馥郁', '梅江是客家文化发祥地，金柚承载客家人以柚待客的千年礼仪传统', '商务送礼,中秋送礼,高端伴手礼', '精品,客家礼仪,商务,梅江', 9.0, 8.5, 9.0),
('蕉岭富硒柚·长寿之乡', '沙田柚', '梅州市蕉岭县', '78-118元/箱', '清甜爽脆、回味悠长', '蕉岭是世界长寿乡，富硒金柚被客家人视为长寿果', '孝敬长辈,养生送礼,中秋送礼', '富硒,长寿乡,养生,蕉岭', 8.5, 8.5, 9.0),
('五华高山柚·有机认证', '沙田柚', '梅州市五华县', '108-168元/箱', '高山清泉灌溉、果肉细腻、冰糖甜', '五华是石匠之乡，高山柚吸收云雾精华，客家人称其为山珍柚', '高端送礼,养生送礼,中秋送礼', '有机,高山,送礼,五华', 8.0, 8.0, 8.5),
('平远慈柚·客家福果', '沙田柚', '梅州市平远县', '68-98元/箱', '果肉蜜甜、入口即化、柚香绵长', '平远客家人称金柚为慈柚，寓意慈母之爱、福运绵长', '孝敬父母,感恩送礼,家庭团聚,中秋', '慈柚,福果,感恩,平远', 8.0, 9.0, 9.5),
('丰顺温泉柚·温润佳品', '蜜柚', '梅州市丰顺县', '58-88元/箱', '温泉滋养、果肉柔嫩、清甜温润', '丰顺温泉闻名粤东，柚树得温泉地热滋养，客家人认为此柚有暖身养气之效', '养生送礼,日常自用,孝敬长辈', '温泉,养生,孝敬,丰顺', 7.0, 7.5, 7.5);

-- 初始数据：算法参数
INSERT INTO algo_rule_params (param_key, param_name, param_value, param_type, param_group, param_range, description, sort_order) VALUES
('weight_requirement_match', '需求匹配度权重', 0.40, 'WEIGHT', 'REQUIREMENT_MATCH', '0.00-1.00', '大模型语义理解后的关键词与金柚属性匹配权重', 1),
('weight_scene_fit', '场景适配度权重', 0.35, 'WEIGHT', 'SCENE_FIT', '0.00-1.00', '用户送礼/自用/宴请等场景与金柚的适配权重', 1),
('weight_hakka_feature', '客家特色贴合度权重', 0.25, 'WEIGHT', 'HAKKA_FEATURE', '0.00-1.00', '金柚与客家文化、地域特色的贴合度权重', 1);

-- 初始数据：Prompt模板
INSERT INTO pomelo_prompt_library (prompt_name, scene_category, applicable_scene, prompt_template, system_role_desc, is_current, priority) VALUES
('金柚选购推荐-标准版', 'BUY', '用户提供选购需求，系统推荐合适金柚', '你是一位精通梅州客家金柚的专业导购顾问。请根据以下用户需求推荐最合适的金柚产品：\n\n用户需求：{{user_input}}\n\n可选金柚数据：{{pomelo_list}}\n\n请以JSON格式返回推荐结果。', '你是梅州客家金柚文化传承人与专业导购', 1, 10),
('金柚知识问答-标准版', 'QA', '用户询问金柚相关知识', '你是客家金柚领域的资深专家。请基于以下知识库内容回答用户问题：\n\n用户问题：{{user_input}}\n\n相关知识：{{knowledge_context}}', '你是梅州客家金柚非遗传承人与农业专家', 1, 10),
('金柚内容生成-电商文案', 'GEN', '为指定金柚生成电商展示文案', '请为以下梅州客家金柚生成一段吸引人的展示文案：\n\n金柚信息：{{pomelo_info}}', '你是精通农产品电商文案的客家文化传播者', 1, 10);
