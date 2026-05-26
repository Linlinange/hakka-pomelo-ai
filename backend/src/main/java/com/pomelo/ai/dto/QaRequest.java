package com.pomelo.ai.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/** 智能问答请求 */
@Data
public class QaRequest {

    /** 用户问题 */
    @NotBlank(message = "问题不能为空")
    private String question;

    /** 用户ID */
    private Long userId;

    /** 会话ID */
    private String sessionId;
}
