package com.pomelo.ai.utils;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Component;

import java.util.UUID;
import java.util.concurrent.TimeUnit;

/**
 * 简易 Token 管理工具。
 * Token 存储在 Redis 中，默认 7 天过期。
 */
@Component
public class TokenUtils {

    @Autowired(required = false)
    private RedisTemplate<String, Object> redisTemplate;

    private static final String TOKEN_PREFIX = "pomelo:token:";
    private static final long TOKEN_TTL_DAYS = 7;

    /** 生成 Token 并关联用户 ID */
    public String generateToken(Long userId) {
        String token = UUID.randomUUID().toString().replace("-", "");
        if (redisTemplate != null) {
            redisTemplate.opsForValue().set(TOKEN_PREFIX + token, userId, TOKEN_TTL_DAYS, TimeUnit.DAYS);
        }
        return token;
    }

    /** 从 Token 获取用户 ID，Token 无效或过期返回 null */
    public Long getUserId(String token) {
        if (token == null || token.isEmpty() || redisTemplate == null) return null;
        Object val = redisTemplate.opsForValue().get(TOKEN_PREFIX + token);
        if (val instanceof Number n) return n.longValue();
        return null;
    }

    /** 刷新 Token 过期时间 */
    public void refreshToken(String token) {
        if (redisTemplate != null && token != null && !token.isEmpty()) {
            redisTemplate.expire(TOKEN_PREFIX + token, TOKEN_TTL_DAYS, TimeUnit.DAYS);
        }
    }

    /** 检查 Token 是否属于管理员 */
    public boolean isAdmin(String token) {
        if (token == null || token.isEmpty() || redisTemplate == null) return false;
        Object val = redisTemplate.opsForValue().get(TOKEN_PREFIX + "admin:" + token);
        return val != null;
    }

    /** 为指定 Token 赋予管理员角色 */
    public void grantAdmin(String token) {
        if (redisTemplate != null && token != null && !token.isEmpty()) {
            redisTemplate.opsForValue().set(TOKEN_PREFIX + "admin:" + token,
                    true, TOKEN_TTL_DAYS, TimeUnit.DAYS);
        }
    }
}
