package com.pomelo.ai.controller;

import com.pomelo.ai.common.Result;
import com.pomelo.ai.dto.RecommendRequest;
import com.pomelo.ai.dto.RecommendResponse;
import com.pomelo.ai.service.RecommendService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

/**
 * AI智荐接口
 *
 * POST /api/recommend
 * 接收用户 Query，调用 AI 融合推荐引擎，返回个性化金柚推荐列表及推荐理由。
 */
@Slf4j
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class RecommendController {

    private final RecommendService recommendService;

    /**
     * AI智荐推荐接口。
     *
     * 请求示例：
     * {
     *   "query": "200元预算中秋送客家亲友什么金柚好？",
     *   "userId": 1,
     *   "sessionId": "abc123",
     *   "skipCache": false
     * }
     */
    @PostMapping("/recommend")
    public Result<RecommendResponse> recommend(@Valid @RequestBody RecommendRequest request) {
        log.info("推荐请求: query={}, userId={}", request.getQuery().substring(0, Math.min(request.getQuery().length(), 40)),
                request.getUserId());
        RecommendResponse response = recommendService.recommend(request);
        return Result.ok(response);
    }
}
