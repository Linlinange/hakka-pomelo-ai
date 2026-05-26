package com.pomelo.ai.controller;

import com.pomelo.ai.common.Result;
import com.pomelo.ai.dto.QaRequest;
import com.pomelo.ai.dto.QaResponse;
import com.pomelo.ai.service.QaService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

/**
 * 智能问答接口
 *
 * POST /api/qa
 * 接收用户问题，优先检索金柚知识库，未命中则调用大模型生成回答。
 */
@Slf4j
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class QaController {

    private final QaService qaService;

    /**
     * 智能问答接口。
     *
     * 请求示例：
     * {
     *   "question": "金柚皮怎么制作客家菜？",
     *   "userId": 1,
     *   "sessionId": "abc123"
     * }
     */
    @PostMapping("/qa")
    public Result<QaResponse> qa(@Valid @RequestBody QaRequest request) {
        log.info("问答请求: question={}, userId={}",
                request.getQuestion().substring(0, Math.min(request.getQuestion().length(), 40)),
                request.getUserId());
        QaResponse response = qaService.answer(request);
        return Result.ok(response);
    }
}
