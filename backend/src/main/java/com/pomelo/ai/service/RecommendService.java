package com.pomelo.ai.service;

import com.pomelo.ai.dto.RecommendRequest;
import com.pomelo.ai.dto.RecommendResponse;

/** AI智荐服务接口 */
public interface RecommendService {

    /**
     * 执行AI智荐推荐。
     * 流程：意图识别 → 候选召回 → 调用Python融合推荐 → 缓存结果 → 记录日志 → 返回
     */
    RecommendResponse recommend(RecommendRequest request);
}
