package com.pomelo.ai.service.impl;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.pomelo.ai.dto.PomeloRecommendItem;
import com.pomelo.ai.dto.RecommendRequest;
import com.pomelo.ai.dto.RecommendResponse;
import com.pomelo.ai.entity.GoldenPomeloKnowledge;
import com.pomelo.ai.mapper.LlmInvokeLogMapper;
import com.pomelo.ai.mapper.PomeloKnowledgeMapper;
import com.pomelo.ai.utils.HttpUtils;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.util.*;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.core.JsonProcessingException;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class RecommendServiceImplTest {

    @Mock
    private PomeloKnowledgeMapper knowledgeMapper;
    @Mock
    private LlmInvokeLogMapper llmInvokeLogMapper;
    @Mock
    private HttpUtils httpUtils;
    @Mock
    private ObjectMapper objectMapper;

    private RecommendServiceImpl recommendService;

    @BeforeEach
    void setUp() {
        recommendService = new RecommendServiceImpl(knowledgeMapper, llmInvokeLogMapper,
                httpUtils, objectMapper);
    }

    @Test
    void recommend_shouldReturnEmpty_whenNoCandidates() {
        RecommendRequest request = new RecommendRequest();
        request.setQuery("test query");

        when(knowledgeMapper.selectAllActive()).thenReturn(Collections.emptyList());

        RecommendResponse response = recommendService.recommend(request);
        assertEquals(0, response.getCount());
        assertTrue(response.getRecommendations().isEmpty());
    }

    @Test
    void recommend_shouldReturnSortedResults_whenCandidatesExist() throws JsonProcessingException {
        RecommendRequest request = new RecommendRequest();
        request.setQuery("200元中秋送礼");

        List<GoldenPomeloKnowledge> candidates = List.of(
                buildKnowledge(1L, "梅县沙田柚", "88-128元/箱"));

        Map<String, Object> aiData = buildAiRecommendData();
        when(knowledgeMapper.selectAllActive()).thenReturn(candidates);
        when(httpUtils.callRecommend(eq("200元中秋送礼"), eq(candidates))).thenReturn(aiData);
        when(objectMapper.writeValueAsString(any())).thenReturn("{}");

        RecommendResponse response = recommendService.recommend(request);
        assertEquals(1, response.getCount());
        assertEquals("BUY", response.getIntentType());
    }

    @Test
    void recommend_shouldNotCallAI_whenCandidatesEmpty() {
        RecommendRequest request = new RecommendRequest();
        request.setQuery("any query");

        when(knowledgeMapper.selectAllActive()).thenReturn(Collections.emptyList());

        recommendService.recommend(request);
        verify(httpUtils, never()).callRecommend(anyString(), anyList());
    }

    // ---- helpers ----

    private GoldenPomeloKnowledge buildKnowledge(Long id, String name, String priceRange) {
        GoldenPomeloKnowledge k = new GoldenPomeloKnowledge();
        k.setId(id);
        k.setPomeloName(name);
        k.setPriceRange(priceRange);
        k.setOrigin("梅州市梅县区");
        k.setViewCount(0);
        return k;
    }

    private Map<String, Object> buildAiRecommendData() {
        Map<String, Object> item = new LinkedHashMap<>();
        item.put("id", 1);
        item.put("pomelo_name", "梅县沙田柚");
        item.put("category", "沙田柚");
        item.put("origin", "梅县");
        item.put("price_range", "88-128元/箱");
        item.put("taste_description", "清甜");
        item.put("hakka_culture_relation", "客家");
        item.put("gift_scene_tags", "中秋送礼");
        item.put("tags", "金奖");
        item.put("image_url", "");
        item.put("score_price_match", 8.5);
        item.put("score_scene_fit", 9.0);
        item.put("score_hakka_feature", 9.5);
        item.put("rule_total", 8.9);
        item.put("llm_score", 85.0);
        item.put("final_score", 87.0);
        item.put("reason", "客家文化深厚，送礼佳品");

        Map<String, Object> intent = Map.of("intent", "BUY", "confidence", 0.95);

        Map<String, Object> aiData = new LinkedHashMap<>();
        aiData.put("intent", intent);
        aiData.put("recommendations", List.of(item));
        aiData.put("count", 1);

        return aiData;
    }
}
