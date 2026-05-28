package com.pomelo.ai.controller;

import com.pomelo.ai.common.Result;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;
import java.util.Map;

/**
 * 健康检查接口
 */
@RestController
public class HealthController {

    @GetMapping("/api/health")
    public Result<Map<String, Object>> health() {
        return Result.ok(Map.of(
            "status", "running",
            "service", "pomelo-ai-backend",
            "time", LocalDateTime.now().toString()
        ));
    }
}
