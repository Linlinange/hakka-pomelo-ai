package com.pomelo.ai.dto;

import lombok.Data;
import lombok.Builder;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import java.util.List;

/** 智能问答响应 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class QaResponse {

    /** 回答内容 */
    private String answer;

    /** 答案来源：KNOWLEDGE_BASE / LLM / FALLBACK */
    private String source;

    /** 关联的知识库条目 */
    private List<KnowledgeRef> refs;

    /** 会话ID */
    private String sessionId;

    /** 处理耗时（ms） */
    private Long costMs;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class KnowledgeRef {
        private Long id;
        private String pomeloName;
        private String snippet;  // 匹配到的文本片段
    }
}
