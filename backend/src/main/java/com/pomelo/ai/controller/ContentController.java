package com.pomelo.ai.controller;

import com.pomelo.ai.common.Result;
import com.pomelo.ai.dto.ContentRequest;
import com.pomelo.ai.dto.ContentResponse;
import com.pomelo.ai.service.ContentService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

/**
 * 内容生成接口
 *
 * POST /api/content
 * 生成金柚电商详情页文案或朋友圈推广语
 */
@Slf4j
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class ContentController {

    private final ContentService contentService;

    @PostMapping("/content")
    public Result<ContentResponse> generate(@Valid @RequestBody ContentRequest request) {
        log.info("内容生成请求: scene={}, pomeloName={}", request.getScene(), request.getPomeloName());
        ContentResponse response = contentService.generate(request);
        return Result.ok(response);
    }
}
