package com.pomelo.ai.dto;

import lombok.Data;
import lombok.Builder;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import java.util.List;
import java.util.Map;

/**
 * AI智荐响应 — 与 Python Flask API 返回格式对齐。
 *
 * Python 返回结构:
 * {
 *   "code": 200,
 *   "data": {
 *     "intent": {"intent":"BUY","confidence":0.95,"constraints":{...},...},
 *     "recommendations": [{pomelo_name, final_score, reason, ...}, ...],
 *     "count": 3
 *   }
 * }
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RecommendResponse {

    /** 意图识别结果（结构化对象，对齐 Python IntentResult.to_dict()） */
    private Map<String, Object> intent;

    /** 推荐列表，字段名对齐 Python API 的 "recommendations" */
    private List<PomeloRecommendItem> recommendations;

    /** 推荐结果数量 */
    private Integer count;

    /** 本次请求是否来自 Redis 缓存 */
    private Boolean fromCache;

    /** 会话ID */
    private String sessionId;

    /** 处理耗时（ms） */
    private Long costMs;

    // ---- 便捷方法，兼容旧代码 ----

    /** @deprecated 使用 getRecommendations() */
    @Deprecated
    public List<PomeloRecommendItem> getItems() {
        return recommendations;
    }

    public String getIntentType() {
        if (intent == null) return "BUY";
        return String.valueOf(intent.getOrDefault("intent", "BUY"));
    }

    public Double getIntentConfidence() {
        if (intent == null) return 0.0;
        Object c = intent.get("confidence");
        return c instanceof Number n ? n.doubleValue() : 0.0;
    }

    public Boolean getNeedsConfirm() {
        if (intent == null) return false;
        Object nc = intent.get("needs_confirm");
        return nc instanceof Boolean b ? b : false;
    }
}
