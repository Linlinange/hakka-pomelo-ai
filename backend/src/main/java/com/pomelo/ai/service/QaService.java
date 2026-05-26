package com.pomelo.ai.service;

import com.pomelo.ai.dto.QaRequest;
import com.pomelo.ai.dto.QaResponse;

/** 智能问答服务接口 */
public interface QaService {

    /**
     * 执行智能问答。
     * 流程：关键词提取 → 知识库检索 → 命中则直接返回，未命中则调用Python大模型 → 记录日志 → 返回
     */
    QaResponse answer(QaRequest request);
}
