package com.pomelo.ai.service.impl;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.pomelo.ai.dto.QaRequest;
import com.pomelo.ai.dto.QaResponse;
import com.pomelo.ai.entity.GoldenPomeloKnowledge;
import com.pomelo.ai.entity.LlmInvokeLog;
import com.pomelo.ai.mapper.LlmInvokeLogMapper;
import com.pomelo.ai.mapper.PomeloKnowledgeMapper;
import com.pomelo.ai.service.QaService;
import com.pomelo.ai.utils.HttpUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

/**
 * 智能问答服务实现。
 *
 * 核心流程：
 * 1. 查 Redis 缓存
 * 2. 从知识库全文检索
 * 3. 若命中 → 直接拼接答案返回
 * 4. 若未命中 → 调用 Python AI 层大模型问答
 * 5. 记录日志 & 写缓存
 */
@Slf4j
@Service
public class QaServiceImpl implements QaService {

    private final PomeloKnowledgeMapper knowledgeMapper;
    private final LlmInvokeLogMapper llmInvokeLogMapper;
    private final HttpUtils httpUtils;
    private final ObjectMapper objectMapper;

    @Autowired(required = false)
    private RedisTemplate<String, Object> redisTemplate;

    public QaServiceImpl(PomeloKnowledgeMapper knowledgeMapper,
                         LlmInvokeLogMapper llmInvokeLogMapper,
                         HttpUtils httpUtils,
                         ObjectMapper objectMapper) {
        this.knowledgeMapper = knowledgeMapper;
        this.llmInvokeLogMapper = llmInvokeLogMapper;
        this.httpUtils = httpUtils;
        this.objectMapper = objectMapper;
    }

    @Value("${pomelo.cache.qa-ttl:3600}")
    private int cacheTtl;

    private static final String CACHE_KEY_PREFIX = "pomelo:qa:";
    private static final int KNOWLEDGE_MATCH_THRESHOLD = 3; // 知识库检索最低命中数

    @Override
    public QaResponse answer(QaRequest request) {
        long startTime = System.currentTimeMillis();
        String question = request.getQuestion().trim();
        String sessionId = Optional.ofNullable(request.getSessionId())
                .orElse(UUID.randomUUID().toString().substring(0, 8));
        String cacheKey = CACHE_KEY_PREFIX + Math.abs(question.hashCode());

        // ---- 1. Redis 缓存 ----
        if (redisTemplate != null) {
            Object cached = redisTemplate.opsForValue().get(cacheKey);
            if (cached instanceof Map<?, ?> map) {
                @SuppressWarnings("unchecked")
                QaResponse resp = objectMapper.convertValue(map, QaResponse.class);
                resp.setCostMs(System.currentTimeMillis() - startTime);
                log.info("问答命中缓存: question={}", question.substring(0, Math.min(question.length(), 30)));
                return resp;
            }
        }

        // ---- 2. 提取关键词 ----
        List<String> keywords = extractKeywords(question);

        // ---- 3. 知识库检索 ----
        List<GoldenPomeloKnowledge> matched = new ArrayList<>();
        try {
            for (String kw : keywords) {
                if (kw.length() < 2) continue;
                List<GoldenPomeloKnowledge> results = knowledgeMapper.searchByKeyword(kw, 5);
                for (GoldenPomeloKnowledge r : results) {
                    if (matched.stream().noneMatch(m -> m.getId().equals(r.getId()))) {
                        matched.add(r);
                    }
                }
            }
        } catch (Exception e) {
            log.warn("知识库检索失败（H2不支持全文搜索），回退到大模型回答: {}", e.getMessage());
        }
        log.info("知识库检索: keywords={}, matched={}", keywords, matched.size());

        // ---- 4. 命中 or 调用大模型 ----
        QaResponse response;
        if (matched.size() >= KNOWLEDGE_MATCH_THRESHOLD) {
            response = buildFromKnowledge(question, matched, sessionId);
        } else {
            response = buildFromLlm(question, matched, sessionId, request.getUserId());
        }

        response.setCostMs(System.currentTimeMillis() - startTime);
        if (redisTemplate != null) {
            redisTemplate.opsForValue().set(cacheKey, response, cacheTtl, TimeUnit.SECONDS);
        }
        return response;
    }

    // ---- 基于知识库直接回答 ----

    private QaResponse buildFromKnowledge(String question, List<GoldenPomeloKnowledge> matched,
                                           String sessionId) {
        // 拼接知识库内容
        StringBuilder context = new StringBuilder();
        for (GoldenPomeloKnowledge k : matched) {
            context.append(String.format("【%s】%s；产地：%s；%s；%s\n",
                    k.getPomeloName(),
                    k.getTasteDescription() != null ? k.getTasteDescription() : "",
                    k.getOrigin(),
                    k.getPreservationMethod() != null ? k.getPreservationMethod() : "",
                    k.getEdiblePairing() != null ? k.getEdiblePairing() : ""
            ));
        }

        String answer = String.format(
                "根据客家金柚知识库，「%s」相关信息如下：\n\n%s\n\n如需更详细的解答，请进一步描述您的问题。",
                matched.get(0).getPomeloName(), context.toString().trim());

        List<QaResponse.KnowledgeRef> refs = matched.stream().map(k ->
                QaResponse.KnowledgeRef.builder()
                        .id(k.getId())
                        .pomeloName(k.getPomeloName())
                        .snippet(truncate(k.getTasteDescription(), 100))
                        .build()
        ).collect(Collectors.toList());

        return QaResponse.builder()
                .answer(answer)
                .source("KNOWLEDGE_BASE")
                .refs(refs)
                .sessionId(sessionId)
                .build();
    }

    // ---- 知识库未命中，调用大模型 ----

    private QaResponse buildFromLlm(String question, List<GoldenPomeloKnowledge> matched,
                                     String sessionId, Long userId) {
        // 拼接少量知识库内容作为上下文
        String knowledgeContext = matched.isEmpty() ? "" : matched.stream()
                .map(k -> String.format("「%s」%s - %s", k.getPomeloName(),
                        k.getOrigin(), k.getTasteDescription()))
                .collect(Collectors.joining("；"));

        Map<String, Object> aiData = httpUtils.callQa(question, knowledgeContext, sessionId);

        String answer = String.valueOf(aiData.getOrDefault("answer",
                "抱歉，暂时无法回答您的问题，请稍后再试。"));
        String source = String.valueOf(aiData.getOrDefault("source", "LLM"));

        // 记录日志
        @SuppressWarnings("unchecked")
        Map<String, Object> intentMap = (Map<String, Object>) aiData.getOrDefault("intent", Collections.emptyMap());
        try {
            LlmInvokeLog logEntity = new LlmInvokeLog();
            logEntity.setUserId(userId);
            logEntity.setSessionId(sessionId);
            logEntity.setSceneCategory("QA");
            logEntity.setIntentType(String.valueOf(intentMap.getOrDefault("intent", "")));
            logEntity.setOriginalInput(question);
            logEntity.setModelName("deepseek-chat");
            logEntity.setInvokeStatus(answer.length() > 10 ? 1 : 2);
            logEntity.setParsedResult(objectMapper.writeValueAsString(aiData));
            logEntity.setCreateTime(LocalDateTime.now());
            llmInvokeLogMapper.insert(logEntity);
        } catch (Exception e) {
            log.warn("保存QA调用日志失败: {}", e.getMessage());
        }

        return QaResponse.builder()
                .answer(answer)
                .source(source)
                .refs(Collections.emptyList())
                .sessionId(sessionId)
                .build();
    }

    // ---- 简单关键词提取（后续可替换为 jieba 分词或调用 AI 层） ----

    private List<String> extractKeywords(String question) {
        // 优先调用 Flask jieba 分词接口
        try {
            Map<String, Object> body = Map.of("text", question);
            Map<String, Object> result = httpUtils.callSegment(question);
            @SuppressWarnings("unchecked")
            List<String> keywords = (List<String>) result.getOrDefault("keywords", Collections.emptyList());
            if (!keywords.isEmpty()) {
                log.debug("jieba分词: {} → {}", question, keywords);
                return keywords;
            }
        } catch (Exception e) {
            log.debug("jieba分词不可用，回退到正则: {}", e.getMessage());
        }

        // 降级：原始正则分词
        String cleaned = question.replaceAll("[，。！？、；：\"'（）【】《》\\s]+", " ")
                .replace("怎么", " ").replace("如何", " ").replace("什么", " ")
                .replace("请问", " ").replace("一个", " ");
        return Arrays.stream(cleaned.split(" "))
                .map(String::trim)
                .filter(s -> s.length() >= 2)
                .distinct()
                .collect(Collectors.toList());
    }
    private static String truncate(String text, int maxLen) {
        if (text == null) return "";
        return text.length() <= maxLen ? text : text.substring(0, maxLen) + "...";
    }
}
