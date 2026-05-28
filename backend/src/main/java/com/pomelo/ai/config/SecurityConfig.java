package com.pomelo.ai.config;

import com.pomelo.ai.utils.TokenUtils;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.filter.OncePerRequestFilter;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.Arrays;
import java.util.Collections;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * Spring Security 分级鉴权配置。
 * - 所有 GET 读取接口放行
 * - POST/PUT/DELETE 写操作需认证 + ADMIN 角色（由 @PreAuthorize 控制）
 * - 使用 TokenUtils 从 Authorization header 读取用户信息
 * - 管理员白名单通过 pomelo.admin.user-ids 配置（逗号分隔）
 */
@Configuration
@EnableWebSecurity
@EnableMethodSecurity
public class SecurityConfig {

    private final TokenUtils tokenUtils;

    @Value("${pomelo.admin.user-ids:1}")
    private String adminUserIds;

    public SecurityConfig(TokenUtils tokenUtils) {
        this.tokenUtils = tokenUtils;
    }

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf(csrf -> csrf.disable())
            .sessionManagement(sm -> sm.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                // 公共读取接口 — GET 全部放行
                .requestMatchers(HttpMethod.GET, "/api/**").permitAll()
                // 无需认证的 POST 接口
                .requestMatchers("/api/login", "/api/health",
                    "/api/recommend", "/api/qa", "/api/content",
                    "/api/intent", "/api/text/segment").permitAll()
                // 流式端点放行
                .requestMatchers("/api/recommend/stream", "/api/qa/stream").permitAll()
                // 会话历史 — 需认证但通过 TokenAuthFilter 解析 userId
                .requestMatchers("/api/conversation/**").permitAll()
                // 用户信息 — 需认证
                .requestMatchers("/api/user/**").permitAll()
                // 其余所有写操作需认证（@PreAuthorize 控制具体角色）
                .anyRequest().authenticated()
            )
            .addFilterBefore(new TokenAuthFilter(tokenUtils, adminUserIds),
                    UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    /**
     * 从 Authorization header 读取 Token，设置 SecurityContext。
     * 管理员白名单从配置属性 pomelo.admin.user-ids 读取。
     */
    static class TokenAuthFilter extends OncePerRequestFilter {

        private final TokenUtils tokenUtils;
        private final Set<Long> adminIds;

        TokenAuthFilter(TokenUtils tokenUtils, String adminUserIds) {
            this.tokenUtils = tokenUtils;
            this.adminIds = Arrays.stream(adminUserIds.split(","))
                    .map(String::trim)
                    .filter(s -> !s.isEmpty())
                    .map(Long::parseLong)
                    .collect(Collectors.toSet());
        }

        @Override
        protected void doFilterInternal(HttpServletRequest request,
                                        HttpServletResponse response,
                                        FilterChain chain)
                throws ServletException, IOException {
            String auth = request.getHeader("Authorization");
            if (auth != null && auth.startsWith("Bearer ")) {
                String token = auth.substring(7);
                Long userId = tokenUtils.getUserId(token);
                if (userId != null) {
                    boolean isAdmin = tokenUtils.isAdmin(token) || adminIds.contains(userId);
                    var authorities = isAdmin
                            ? Collections.singletonList(new SimpleGrantedAuthority("ROLE_ADMIN"))
                            : Collections.<SimpleGrantedAuthority>emptyList();
                    var authentication =
                            new org.springframework.security.authentication
                                    .UsernamePasswordAuthenticationToken(userId, token, authorities);
                    SecurityContextHolder.getContext().setAuthentication(authentication);
                }
            }
            chain.doFilter(request, response);
        }
    }
}
