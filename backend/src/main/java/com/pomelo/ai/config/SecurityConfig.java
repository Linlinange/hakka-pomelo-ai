package com.pomelo.ai.config;

import com.pomelo.ai.utils.TokenUtils;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
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
import java.util.Collections;

/**
 * Spring Security 最小化配置。
 * - 所有 GET 请求放行
 * - 管理接口 POST/PUT/DELETE 需 ADMIN 角色
 * - 使用 TokenUtils 从 Authorization header 读取用户信息
 */
@Configuration
@EnableWebSecurity
@EnableMethodSecurity
public class SecurityConfig {

    private final TokenUtils tokenUtils;

    public SecurityConfig(TokenUtils tokenUtils) {
        this.tokenUtils = tokenUtils;
    }

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf(csrf -> csrf.disable())
            .sessionManagement(sm -> sm.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/login", "/api/health").permitAll()
                .requestMatchers("/api/recommend", "/api/qa", "/api/content").permitAll()
                .requestMatchers("/api/intent").permitAll()
                .requestMatchers("/api/user/**").permitAll()
                .requestMatchers("/api/knowledge/**").permitAll()
                .requestMatchers("/api/prompt/**").permitAll()
                .anyRequest().permitAll()
            )
            .addFilterBefore(new TokenAuthFilter(tokenUtils),
                    UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    /**
     * 从 Authorization header 读取 Token，设置 SecurityContext。
     * 仅 admin 用户获得 ROLE_ADMIN 权限。
     */
    static class TokenAuthFilter extends OncePerRequestFilter {

        private final TokenUtils tokenUtils;

        TokenAuthFilter(TokenUtils tokenUtils) {
            this.tokenUtils = tokenUtils;
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
                    // 检查是否为管理员（userId=1 或 token 中存储了 admin 角色）
                    boolean isAdmin = tokenUtils.isAdmin(token) || userId == 1L;
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
