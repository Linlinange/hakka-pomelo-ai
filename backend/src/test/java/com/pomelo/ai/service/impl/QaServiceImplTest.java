package com.pomelo.ai.service.impl;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.pomelo.ai.dto.QaRequest;
import com.pomelo.ai.dto.QaResponse;
import com.pomelo.ai.mapper.LlmInvokeLogMapper;
import com.pomelo.ai.mapper.PomeloKnowledgeMapper;
import com.pomelo.ai.utils.HttpUtils;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.core.JsonProcessingException;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class QaServiceImplTest {

    @Mock
    private PomeloKnowledgeMapper knowledgeMapper;
    @Mock
    private LlmInvokeLogMapper llmInvokeLogMapper;
    @Mock
    private HttpUtils httpUtils;
    @Mock
    private ObjectMapper objectMapper;

    private QaServiceImpl qaService;

    @BeforeEach
    void setUp() {
        qaService = new QaServiceImpl(knowledgeMapper, llmInvokeLogMapper, httpUtils, objectMapper);
    }

    @Test
    void answer_shouldCallLLM_whenNoKnowledgeMatch() throws JsonProcessingException {
        QaRequest request = new QaRequest();
        request.setQuestion("how to store pomelo fruit");
        request.setSessionId("s1");

        when(knowledgeMapper.searchByKeyword(anyString(), eq(5))).thenReturn(Collections.emptyList());
        when(httpUtils.callQa(eq("how to store pomelo fruit"), anyString(), eq("s1")))
                .thenReturn(Map.of(
                        "answer", "Store in a cool, dry place.",
                        "source", "llm",
                        "intent", Collections.emptyMap()));
        when(objectMapper.writeValueAsString(any())).thenReturn("{}");

        QaResponse response = qaService.answer(request);
        assertEquals("llm", response.getSource());
        assertTrue(response.getAnswer().length() > 0);
    }

    @Test
    void answer_shouldCallLLM_whenKnowledgeSearchFails() throws JsonProcessingException {
        QaRequest request = new QaRequest();
        request.setQuestion("test question");
        request.setSessionId("s1");

        when(knowledgeMapper.searchByKeyword(anyString(), eq(5)))
                .thenThrow(new RuntimeException("H2 fulltext not supported"));
        when(httpUtils.callQa(anyString(), anyString(), anyString()))
                .thenReturn(Map.of("answer", "AI fallback answer", "source", "llm",
                        "intent", Collections.emptyMap()));
        when(objectMapper.writeValueAsString(any())).thenReturn("{}");

        QaResponse response = qaService.answer(request);
        assertEquals("llm", response.getSource());
    }
}
