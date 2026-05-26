package com.pomelo.ai.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/** AI智荐请求 */
@Data
public class RecommendRequest {

    /** 用户原始输入 */
    @NotBlank(message = "查询内容不能为空")
    private String query;

    /** 用户ID（未登录时为空） */
    private Long userId;

    /** 会话ID，用于串联多轮对话 */
    private String sessionId;

    /** 是否跳过缓存，强制重新调用大模型 */
    private Boolean skipCache = false;
}
