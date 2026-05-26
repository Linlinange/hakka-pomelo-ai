package com.pomelo.ai.service;

import com.pomelo.ai.dto.ContentRequest;
import com.pomelo.ai.dto.ContentResponse;

/** 内容生成服务接口 */
public interface ContentService {
    ContentResponse generate(ContentRequest request);
}
