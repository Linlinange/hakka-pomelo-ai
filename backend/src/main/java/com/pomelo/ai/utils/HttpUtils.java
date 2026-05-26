package com.pomelo.ai.utils;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Component;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestClientResponseException;
import org.springframework.web.client.RestTemplate;

import java.net.SocketTimeoutException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Collections;
import java.util.List;
import java.util.Map;

/**
 * SpringBoot 与 Python Flask AI 算法层之间的 HTTP 通信工具。
 *
 * 职责：
 * 1. 封装对 Python Flask API 的 HTTP 调用（/api/recommend, /api/qa, /api/intent）
 * 2. 自动解包 Flask 统一响应 {"code":200, "data":{...}, "message":"success"}
 * 3. 异常分类处理（网络超时 / 连接拒绝 / JSON 解析错误 / 业务错误码）
 * 4. 指数退避重试 + 结构化日志
 */
@Slf4j
@Component
public class HttpUtils {

    private static final DateTimeFormatter TIME_FMT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss.SSS");

    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;
    private final String aiLayerBaseUrl;

    public HttpUtils(RestTemplate restTemplate,
                     @Value("${pomelo.ai-layer.base-url}") String aiLayerBaseUrl) {
        this.restTemplate = restTemplate;
        this.aiLayerBaseUrl = aiLayerBaseUrl;
        this.objectMapper = new ObjectMapper()
                .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
    }

    /** 启动时检测 Python AI 层是否可达 */
    @PostConstruct
    public void init() {
        String time = LocalDateTime.now().format(TIME_FMT);
        if (healthCheck()) {
            log.info("[{}] AI层连接成功 | baseUrl={}", time, aiLayerBaseUrl);
        } else {
            log.warn("[{}] AI层连接失败 | baseUrl={} | 请确认 Flask 已启动", time, aiLayerBaseUrl);
        }
    }

    // ==================== 公开接口 ====================

    /**
     * 调用 Flask POST /api/recommend —— AI智荐推荐
     *
     * @param userQuery  用户输入（如 "200元中秋送礼客家亲友"）
     * @param candidates 从 MySQL 召回的金柚候选列表
     * @return 解包后的 data Map {intent, recommendations, count}
     */
    public Map<String, Object> callRecommend(String userQuery, List<?> candidates) {
        Map<String, Object> body = Map.of(
                "user_query", userQuery,
                "candidates", candidates != null ? candidates : Collections.emptyList()
        );
        return callApi("POST", "/api/recommend", body, userQuery);
    }

    /**
     * 调用 Flask POST /api/qa —— 智能问答
     *
     * @param question         用户问题
     * @param knowledgeContext 知识库检索上下文
     * @param sessionId        会话ID
     * @return 解包后的 data Map {answer, source, intent, session_id}
     */
    public Map<String, Object> callQa(String question, String knowledgeContext, String sessionId) {
        Map<String, Object> body = Map.of(
                "question", question,
                "knowledge_context", knowledgeContext != null ? knowledgeContext : "",
                "session_id", sessionId != null ? sessionId : ""
        );
        return callApi("POST", "/api/qa", body, question);
    }

    /**
     * 调用 Flask POST /api/intent —— 意图识别
     *
     * @param query 用户输入
     * @return 解包后的 data Map {intent, confidence, constraints, culture_tags, keywords}
     */
    public Map<String, Object> callIntentRecognize(String query) {
        Map<String, Object> body = Map.of("query", query);
        return callApi("POST", "/api/intent", body, query);
    }

    // ==================== 内容生成接口 ====================

    /**
     * 调用 Flask POST /api/content —— 金柚文案生成
     *
     * @param scene      场景: "ecommerce" | "social"
     * @param prompt     可选自定义要求
     * @param pomeloName 金柚品名
     * @param style      文案风格
     * @return 解包后的 data Map {content, scene, pomelo_name, created_at}
     */
    public Map<String, Object> callContent(String scene, String prompt,
                                            String pomeloName, String style) {
        Map<String, Object> body = Map.of(
                "scene", scene != null ? scene : "social",
                "prompt", prompt != null ? prompt : "",
                "pomelo_name", pomeloName != null ? pomeloName : "客家金柚",
                "style", style != null ? style : ""
        );
        return callApi("POST", "/api/content", body, "content:" + scene);
    }

    /**
     * 调用 Flask GET /api/health —— 健康检查
     */
    public boolean healthCheck() {
        try {
            ResponseEntity<String> resp = restTemplate.getForEntity(
                    aiLayerBaseUrl + "/api/health", String.class);
            return resp.getStatusCode().is2xxSuccessful();
        } catch (Exception e) {
            return false;
        }
    }

    // ==================== 核心调用逻辑 ====================

    /**
     * 统一 POST 调用入口。
     *
     * @param method   HTTP 方法（POST）
     * @param path     API 路径（如 /api/recommend）
     * @param body     请求体
     * @param queryTag 用于日志摘要的用户 Query（截断后）
     * @return 解包后的 data Map，失败返回空 Map
     */
    @SuppressWarnings("unchecked")
    private Map<String, Object> callApi(String method, String path,
                                         Map<String, Object> body, String queryTag) {
        long t0 = System.currentTimeMillis();
        String requestTime = LocalDateTime.now().format(TIME_FMT);
        String url = aiLayerBaseUrl + path;
        String summaryTag = queryTag != null && queryTag.length() > 60
                ? queryTag.substring(0, 60) + "..."
                : queryTag;

        // 请求日志
        log.info("[{}] >> {} {} | query={}", requestTime, method, path, summaryTag);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(body, headers);

        int maxRetries = 2;
        Exception lastException = null;

        for (int attempt = 0; attempt <= maxRetries; attempt++) {
            try {
                ResponseEntity<String> resp = restTemplate.postForEntity(url, entity, String.class);
                long elapsed = System.currentTimeMillis() - t0;

                // HTTP 状态码异常
                if (!resp.getStatusCode().is2xxSuccessful()) {
                    log.warn("[{}] << HTTP {} | path={} | status={} | {}ms",
                            LocalDateTime.now().format(TIME_FMT),
                            method, path, resp.getStatusCodeValue(), elapsed);
                    return Collections.emptyMap();
                }

                // JSON 解析
                String respBody = resp.getBody();
                if (respBody == null) {
                    log.warn("[{}] << 响应体为空 | path={} | {}ms",
                            LocalDateTime.now().format(TIME_FMT), path, elapsed);
                    return Collections.emptyMap();
                }

                Map<String, Object> fullResp = objectMapper.readValue(respBody,
                        new TypeReference<Map<String, Object>>() {});

                // 解包 Flask 统一响应
                Integer code = (Integer) fullResp.get("code");
                if (code != null && code == 200) {
                    Object data = fullResp.get("data");
                    String responseSummary = buildResponseSummary(path, data);

                    log.info("[{}] << {} {} | code=200 | {}ms | {}",
                            LocalDateTime.now().format(TIME_FMT),
                            method, path, elapsed, responseSummary);

                    if (data instanceof Map<?, ?> m) {
                        return (Map<String, Object>) m;
                    }
                    return Collections.emptyMap();
                }

                // Flask 返回业务错误码
                String msg = String.valueOf(fullResp.getOrDefault("message", "unknown"));
                log.error("[{}] << 业务错误 | path={} | code={} | message={} | {}ms",
                        LocalDateTime.now().format(TIME_FMT), path, code, msg, elapsed);
                return Collections.emptyMap();

            } catch (ResourceAccessException e) {
                lastException = e;
                // 细分：SocketTimeoutException（超时） vs ConnectException（拒绝）
                String errorType = e.getCause() instanceof SocketTimeoutException ? "超时" : "连接失败";
                log.warn("[{}] << {} | path={} | attempt={}/{} | {}ms",
                        LocalDateTime.now().format(TIME_FMT),
                        errorType, path, attempt + 1, maxRetries + 1,
                        System.currentTimeMillis() - t0);
                if (attempt < maxRetries) sleepBackoff(attempt);

            } catch (RestClientResponseException e) {
                lastException = e;
                log.error("[{}] << HTTP {} | path={} | status={} | body={}",
                        LocalDateTime.now().format(TIME_FMT),
                        method, path, e.getStatusCode().value(),
                        e.getResponseBodyAsString().substring(0, Math.min(200, e.getResponseBodyAsString().length())));
                return Collections.emptyMap(); // 4xx/5xx 响应不重试

            } catch (JsonProcessingException e) {
                lastException = e;
                log.error("[{}] << JSON解析失败 | path={} | {} | attempt={}/{}",
                        LocalDateTime.now().format(TIME_FMT), path, e.getOriginalMessage(),
                        attempt + 1, maxRetries + 1);
                if (attempt >= maxRetries) break;

            } catch (Exception e) {
                lastException = e;
                log.error("[{}] << 未知异常 | path={} | {} | attempt={}/{}",
                        LocalDateTime.now().format(TIME_FMT), path, e.getClass().getSimpleName(),
                        attempt + 1, maxRetries + 1);
                if (attempt >= maxRetries) break;
            }
        }

        long totalElapsed = System.currentTimeMillis() - t0;
        log.error("[{}] << 最终失败 | path={} | retries={} | {}ms | lastError={}",
                LocalDateTime.now().format(TIME_FMT), path, maxRetries, totalElapsed,
                lastException != null ? lastException.getClass().getSimpleName() : "unknown");
        return Collections.emptyMap();
    }

    /** 构建响应摘要，用于日志 */
    @SuppressWarnings("unchecked")
    private String buildResponseSummary(String path, Object data) {
        if (!(data instanceof Map)) return "data=null";
        Map<String, Object> m = (Map<String, Object>) data;
        if (path.contains("recommend")) {
            Object intent = m.get("intent");
            String intentType = "";
            if (intent instanceof Map) {
                intentType = String.valueOf(((Map<String, Object>) intent).getOrDefault("intent", ""));
            }
            return String.format("intent=%s count=%s", intentType, m.get("count"));
        }
        if (path.contains("qa")) {
            String answer = String.valueOf(m.getOrDefault("answer", ""));
            String snippet = answer.length() > 50 ? answer.substring(0, 50) + "..." : answer;
            return "answer=" + snippet;
        }
        if (path.contains("intent")) {
            return "intent=" + m.getOrDefault("intent", "?");
        }
        if (path.contains("content")) {
            String c = String.valueOf(m.getOrDefault("content", ""));
            return "len=" + c.length();
        }
        return "ok";
    }

    /** 指数退避：500ms / 1000ms */
    private void sleepBackoff(int attempt) {
        try {
            Thread.sleep((long) Math.pow(2, attempt) * 500);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
