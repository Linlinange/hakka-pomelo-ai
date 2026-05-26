package com.pomelo.ai.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

/** 大模型调用日志实体 */
@Data
@TableName("llm_invoke_log")
public class LlmInvokeLog {

    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private String sessionId;
    private String sceneCategory;
    private String intentType;
    private java.math.BigDecimal intentConfidence;
    private String originalInput;
    private String extractedKeywords;
    private String extractedConstraints;
    private Long promptTemplateId;
    private String promptVersion;
    private String assembledPrompt;
    private String modelName;
    private String modelResponse;
    private String parsedResult;
    private Integer tokenCountInput;
    private Integer tokenCountOutput;
    private Integer responseTimeMs;
    private Integer totalCostMs;
    private Integer invokeStatus;       // 1-成功 2-失败 3-超时 4-限流
    private String errorMessage;
    private Integer retryCount;
    private Integer userFeedback;       // 0-无 1-有用 2-无用
    private String feedbackRemark;
    private LocalDateTime createTime;
}
