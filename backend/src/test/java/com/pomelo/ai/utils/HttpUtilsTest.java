package com.pomelo.ai.utils;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;

import java.util.Collections;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class HttpUtilsTest {

    @Mock
    private RestTemplate restTemplate;

    private HttpUtils httpUtils;

    @BeforeEach
    void setUp() {
        httpUtils = new HttpUtils(restTemplate, "http://127.0.0.1:5000");
    }

    @Test
    void healthCheck_shouldReturnTrue_whenFlaskResponds200() {
        when(restTemplate.getForEntity(eq("http://127.0.0.1:5000/api/health"), eq(String.class)))
                .thenReturn(new ResponseEntity<>("ok", HttpStatus.OK));

        assertTrue(httpUtils.healthCheck());
    }

    @Test
    void healthCheck_shouldReturnFalse_whenFlaskUnreachable() {
        when(restTemplate.getForEntity(anyString(), eq(String.class)))
                .thenThrow(new RuntimeException("Connection refused"));

        assertFalse(httpUtils.healthCheck());
    }

    @Test
    void callRecommend_shouldReturnEmptyMap_whenFlaskReturnsError() {
        ResponseEntity<String> errorResp = new ResponseEntity<>(
                "{\"code\":500,\"data\":null,\"message\":\"error\"}",
                HttpStatus.INTERNAL_SERVER_ERROR);

        when(restTemplate.postForEntity(anyString(), any(), eq(String.class)))
                .thenReturn(errorResp);

        Map<String, Object> result = httpUtils.callRecommend("test query", Collections.emptyList());
        assertTrue(result.isEmpty());
    }

    @Test
    void callRecommend_shouldRetry_onNetworkError() {
        when(restTemplate.postForEntity(anyString(), any(), eq(String.class)))
                .thenThrow(new org.springframework.web.client.ResourceAccessException("timeout"))
                .thenReturn(new ResponseEntity<>(
                        "{\"code\":200,\"data\":{\"recommendations\":[]}}",
                        HttpStatus.OK));

        Map<String, Object> result = httpUtils.callRecommend("test", Collections.emptyList());
        // 重试后成功
        verify(restTemplate, times(2)).postForEntity(anyString(), any(), eq(String.class));
    }

    @Test
    void callApi_shouldUnwrapFlaskEnvelope() {
        String flaskResponse = "{\"code\":200,\"data\":{\"answer\":\"hello\"},\"message\":\"success\"}";
        when(restTemplate.postForEntity(anyString(), any(), eq(String.class)))
                .thenReturn(new ResponseEntity<>(flaskResponse, HttpStatus.OK));

        Map<String, Object> result = httpUtils.callQa("question?", "", "s1");
        assertEquals("hello", result.get("answer"));
    }
}
