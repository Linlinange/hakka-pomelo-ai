package com.pomelo.ai.service.impl;

import com.pomelo.ai.dto.ContentRequest;
import com.pomelo.ai.dto.ContentResponse;
import com.pomelo.ai.service.ContentService;
import com.pomelo.ai.utils.HttpUtils;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.Map;

/** 内容生成服务实现 */
@Slf4j
@Service
@RequiredArgsConstructor
public class ContentServiceImpl implements ContentService {

    private final HttpUtils httpUtils;

    @Override
    public ContentResponse generate(ContentRequest request) {
        String scene = request.getScene() != null ? request.getScene() : "social";
        String prompt = request.getPrompt() != null ? request.getPrompt() : "";
        String pomeloName = request.getPomeloName() != null ? request.getPomeloName() : "客家金柚";

        Map<String, Object> aiData = httpUtils.callContent(scene, prompt, pomeloName,
                request.getStyle() != null ? request.getStyle() : "");

        String content = String.valueOf(aiData.getOrDefault("content", "生成失败，请稍后再试。"));
        String createdAt = String.valueOf(aiData.getOrDefault("created_at", ""));

        return ContentResponse.builder()
                .content(content)
                .scene(String.valueOf(aiData.getOrDefault("scene", scene)))
                .pomeloName(String.valueOf(aiData.getOrDefault("pomelo_name", pomeloName)))
                .createdAt(createdAt)
                .build();
    }
}
