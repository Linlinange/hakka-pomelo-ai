package com.pomelo.ai.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.pomelo.ai.dto.PomeloRecommendItem;
import com.pomelo.ai.dto.RecommendRequest;
import com.pomelo.ai.dto.RecommendResponse;
import com.pomelo.ai.entity.GoldenPomeloKnowledge;
import com.pomelo.ai.entity.LlmInvokeLog;
import com.pomelo.ai.mapper.LlmInvokeLogMapper;
import com.pomelo.ai.mapper.PomeloKnowledgeMapper;
import com.pomelo.ai.service.RecommendService;
import com.pomelo.ai.utils.HttpUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.TimeUnit;

/**
 * AI智荐服务实现。
 *
 * 核心流程：
 * 1. 查 Redis 缓存（相同 query 30 分钟内不重复调用大模型）
 * 2. 从 MySQL 召回所有上架金柚作为候选
 * 3. 调用 Python AI 层融合推荐接口
 * 4. 解析返回结果，构建响应
 * 5. 写入 Redis 缓存 + 大模型调用日志
 */
@Slf4j
@Service
public class RecommendServiceImpl implements RecommendService {

    private final PomeloKnowledgeMapper knowledgeMapper;
    private final LlmInvokeLogMapper llmInvokeLogMapper;
    private final HttpUtils httpUtils;
    private final ObjectMapper objectMapper;

    @Autowired(required = false)
    private RedisTemplate<String, Object> redisTemplate;

    public RecommendServiceImpl(PomeloKnowledgeMapper knowledgeMapper,
                                LlmInvokeLogMapper llmInvokeLogMapper,
                                HttpUtils httpUtils,
                                ObjectMapper objectMapper) {
        this.knowledgeMapper = knowledgeMapper;
        this.llmInvokeLogMapper = llmInvokeLogMapper;
        this.httpUtils = httpUtils;
        this.objectMapper = objectMapper;
    }

    @Value("${pomelo.cache.recommend-ttl:1800}")
    private int cacheTtl;

    private static final String CACHE_KEY_PREFIX = "pomelo:recommend:";

    @Override
    public RecommendResponse recommend(RecommendRequest request) {
        long startTime = System.currentTimeMillis();
        String query = request.getQuery().trim();
        String sessionId = Optional.ofNullable(request.getSessionId())
                .orElse(UUID.randomUUID().toString().substring(0, 8));
        String cacheKey = CACHE_KEY_PREFIX + Math.abs(query.hashCode());

        // ---- 1. 尝试从 Redis 缓存读取 ----
        if (redisTemplate != null && !Boolean.TRUE.equals(request.getSkipCache())) {
            Object cached = redisTemplate.opsForValue().get(cacheKey);
            if (cached instanceof Map<?, ?> map) {
                @SuppressWarnings("unchecked")
                RecommendResponse resp = objectMapper.convertValue(map, RecommendResponse.class);
                resp.setFromCache(true);
                resp.setCostMs(System.currentTimeMillis() - startTime);
                log.info("推荐命中缓存: query={}", query.substring(0, Math.min(query.length(), 30)));
                return resp;
            }
        }

        // ---- 2. 从 MySQL 召回候选金柚 ----
        List<GoldenPomeloKnowledge> candidates = knowledgeMapper.selectAllActive();
        if (candidates.isEmpty()) {
            return RecommendResponse.builder()
                    .recommendations(Collections.emptyList())
                .count(0)
                    .sessionId(sessionId)
                    .costMs(System.currentTimeMillis() - startTime)
                    .build();
        }
        log.info("候选召回: count={}", candidates.size());

        // 更新浏览次数（H2 兼容：直接 set + updateById）
        for (GoldenPomeloKnowledge c : candidates) {
            c.setViewCount(c.getViewCount() != null ? c.getViewCount() + 1 : 1);
            knowledgeMapper.updateById(c);
        }

        // ---- 3. 调用 Python Flask AI 层融合推荐 ----
        Map<String, Object> aiData = httpUtils.callRecommend(query, candidates);
        @SuppressWarnings("unchecked")
        Map<String, Object> intentMap = (Map<String, Object>) aiData.getOrDefault("intent", Collections.emptyMap());
        List<PomeloRecommendItem> recommendations = parseRecommendItems(aiData);

        // ---- 4. 记录大模型调用日志 ----
        boolean aiSuccess = !aiData.isEmpty();
        saveInvokeLog(request.getUserId(), sessionId, "BUY", query, aiData, aiSuccess);

        // ---- 5. 构建响应 & 写缓存 ----
        int count = recommendations.size();
        RecommendResponse response = RecommendResponse.builder()
                .intent(intentMap)
                .recommendations(recommendations)
                .count(count)
                .fromCache(false)
                .sessionId(sessionId)
                .costMs(System.currentTimeMillis() - startTime)
                .build();

        if (redisTemplate != null) {
            redisTemplate.opsForValue().set(cacheKey, response, cacheTtl, TimeUnit.SECONDS);
        }
        log.info("推荐完成: query={} intent={} count={} costMs={}",
                query.substring(0, Math.min(query.length(), 30)),
                response.getIntentType(), count, response.getCostMs());

        return response;
    }

    // ---- 解析 Flask AI 层返回的推荐列表 ----

    @SuppressWarnings("unchecked")
    @SuppressWarnings("unchecked")
    private List<PomeloRecommendItem> parseRecommendItems(Map<String, Object> aiData) {
        // Flask 返回: data.recommendations = [ {pomelo_name, product_type, final_score, reason, ...}, ... ]
        List<Map<String, Object>> rawItems = (List<Map<String, Object>>)
                aiData.getOrDefault("recommendations", Collections.emptyList());
        List<PomeloRecommendItem> items = new ArrayList<>();
        for (Map<String, Object> item : rawItems) {
            try {
                items.add(PomeloRecommendItem.builder()
                        .id(toLong(item.get("id")))
                        .productType(String.valueOf(item.getOrDefault("product_type", "pomelo")))
                        .pomeloName(String.valueOf(item.getOrDefault("pomelo_name", "")))
                        .category(String.valueOf(item.getOrDefault("category", "")))
                        .origin(String.valueOf(item.getOrDefault("origin", "")))
                        .specification(String.valueOf(item.getOrDefault("specification", "")))
                        .priceRange(String.valueOf(item.getOrDefault("price_range", "")))
                        .tasteDescription(String.valueOf(item.getOrDefault("taste_description", "")))
                        .hakkaCultureRelation(String.valueOf(item.getOrDefault("hakka_culture_relation", "")))
                        .productDescription(String.valueOf(item.getOrDefault("product_description", "")))
                        .imageUrl(String.valueOf(item.getOrDefault("image_url", "")))
                        .giftSceneTags(String.valueOf(item.getOrDefault("gift_scene_tags", "")))
                        .tags(String.valueOf(item.getOrDefault("tags", "")))
                        .scorePriceMatch(toBigDecimal(item.get("score_price_match")))
                        .scoreSceneFit(toBigDecimal(item.get("score_scene_fit")))
                        .scoreHakkaFeature(toBigDecimal(item.get("score_hakka_feature")))
                        .scoreProductFeature(toBigDecimal(item.get("score_product_feature")))
                        .ruleTotal(toBigDecimal(item.get("rule_total")))
                        .llmScore(toBigDecimal(item.get("llm_score")))
                        .finalScore(toBigDecimal(item.get("final_score")))
                        .reason(String.valueOf(item.getOrDefault("reason", "")))
                        .build());
            } catch (Exception e) {
                log.warn("解析推荐条目失败: id={} err={}", item.get("id"), e.getMessage());
            }
        }
        return items;
    }

    // ---- 记录大模型调用日志 ----

    private void saveInvokeLog(Long userId, String sessionId, String scene, String query,
                               Map<String, Object> aiData, boolean success) {
        try {
            LlmInvokeLog logEntity = new LlmInvokeLog();
            logEntity.setUserId(userId);
            logEntity.setSessionId(sessionId);
            logEntity.setSceneCategory(scene);
            logEntity.setOriginalInput(query);
            logEntity.setModelName("deepseek-chat");
            logEntity.setInvokeStatus(success ? 1 : 2);

            @SuppressWarnings("unchecked")
            Map<String, Object> intentMap = (Map<String, Object>) aiData.getOrDefault("intent", Collections.emptyMap());
            logEntity.setIntentType(String.valueOf(intentMap.getOrDefault("intent", "")));
            logEntity.setParsedResult(objectMapper.writeValueAsString(aiData));
            logEntity.setCreateTime(LocalDateTime.now());

            llmInvokeLogMapper.insert(logEntity);
        } catch (Exception e) {
            log.warn("保存调用日志失败: {}", e.getMessage());
        }
    }

    // ---- 安全类型转换 ----

    private static Long toLong(Object obj) {
        if (obj instanceof Number n) return n.longValue();
        if (obj instanceof String s) {
            try { return Long.parseLong(s); } catch (NumberFormatException ignored) {}
        }
        return 0L;
    }

    private static Double toDouble(Object obj) {
        if (obj instanceof Number n) return n.doubleValue();
        if (obj instanceof String s) {
            try { return Double.parseDouble(s); } catch (NumberFormatException ignored) {}
        }
        return 0.0;
    }

    private static BigDecimal toBigDecimal(Object obj) {
        if (obj instanceof BigDecimal b) return b;
        if (obj instanceof Number n) return BigDecimal.valueOf(n.doubleValue());
        if (obj instanceof String s) {
            try { return new BigDecimal(s); } catch (NumberFormatException ignored) {}
        }
        return BigDecimal.ZERO;
    }
}
