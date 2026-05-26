package com.pomelo.ai.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.context.annotation.Profile;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.core.RedisTemplate;

/**
 * 演示模式配置 — 提供 Redis Mock（无需外部 Redis）。
 */
@Configuration
@Profile("demo")
public class DemoConfig {

    @Bean
    @Primary
    public RedisConnectionFactory redisConnectionFactory() {
        return new org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory() {
            @Override public void afterPropertiesSet() {}
            @Override public void destroy() {}
        };
    }

    @Bean
    @Primary
    public RedisTemplate<String, Object> redisTemplate(RedisConnectionFactory factory) {
        RedisTemplate<String, Object> t = new RedisTemplate<>();
        t.setConnectionFactory(factory);
        t.afterPropertiesSet();
        return t;
    }
}
