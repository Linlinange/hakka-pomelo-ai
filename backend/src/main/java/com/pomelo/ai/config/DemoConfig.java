package com.pomelo.ai.config;

import org.springframework.boot.autoconfigure.data.redis.RedisAutoConfiguration;
import org.springframework.boot.autoconfigure.data.redis.RedisRepositoriesAutoConfiguration;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;

/**
 * 演示模式配置 — 完全禁用 Redis，无需外部依赖。
 * Redis 相关的自动配置已在 application-demo.properties 中排除，
 * 本类仅用于激活 demo profile 的组件扫描。
 */
@Configuration
@Profile("demo")
public class DemoConfig {
    // Redis 被完全禁用。服务层中的 Redis 操作由 @Autowired(required=false) 或
    // Optional<RedisTemplate> 的方式做空安全处理——详见各 ServiceImpl。
}
