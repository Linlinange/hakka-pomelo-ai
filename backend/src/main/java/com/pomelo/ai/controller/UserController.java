package com.pomelo.ai.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.pomelo.ai.common.Result;
import com.pomelo.ai.dto.LoginRequest;
import com.pomelo.ai.dto.LoginResponse;
import com.pomelo.ai.dto.UserProfileRequest;
import com.pomelo.ai.entity.SysUser;
import com.pomelo.ai.entity.LlmInvokeLog;
import com.pomelo.ai.mapper.LlmInvokeLogMapper;
import com.pomelo.ai.mapper.SysUserMapper;
import com.pomelo.ai.utils.TokenUtils;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * 用户管理接口
 *
 * POST /api/login  微信登录
 * GET  /api/user   获取当前用户信息
 * PUT  /api/user   修改用户信息
 */
@Slf4j
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class UserController {

    private final SysUserMapper userMapper;
    private final LlmInvokeLogMapper logMapper;
    private final TokenUtils tokenUtils;
    private final RestTemplate restTemplate;

    @Value("${pomelo.wechat.app-id:}")
    private String appId;

    @Value("${pomelo.wechat.app-secret:}")
    private String appSecret;

    /** 微信登录 */
    @PostMapping("/login")
    public Result<LoginResponse> login(@Valid @RequestBody LoginRequest request) {
        String openid = resolveOpenid(request.getCode());
        if (openid == null) {
            return Result.fail(400, "微信登录失败，请重试");
        }

        // 查找或创建用户
        SysUser user = userMapper.selectOne(
                new LambdaQueryWrapper<SysUser>().eq(SysUser::getOpenid, openid));
        boolean isNew = (user == null);

        if (isNew) {
            user = new SysUser();
            user.setOpenid(openid);
            user.setNickname(request.getNickname() != null ? request.getNickname() : "金柚爱好者");
            user.setAvatarUrl(request.getAvatarUrl());
            user.setStatus(1);
            user.setLastLoginTime(LocalDateTime.now());
            user.setCreateTime(LocalDateTime.now());
            user.setUpdateTime(LocalDateTime.now());
            userMapper.insert(user);
        } else {
            if (request.getNickname() != null) user.setNickname(request.getNickname());
            if (request.getAvatarUrl() != null) user.setAvatarUrl(request.getAvatarUrl());
            user.setLastLoginTime(LocalDateTime.now());
            user.setUpdateTime(LocalDateTime.now());
            userMapper.updateById(user);
        }

        String token = tokenUtils.generateToken(user.getId());

        return Result.ok(LoginResponse.builder()
                .token(token)
                .userId(user.getId())
                .nickname(user.getNickname())
                .avatarUrl(user.getAvatarUrl())
                .isNewUser(isNew)
                .build());
    }

    /** 获取当前用户信息 */
    @GetMapping("/user")
    public Result<SysUser> getProfile(@RequestHeader(value = "Authorization", required = false) String auth) {
        Long userId = tokenUtils.getUserId(extractToken(auth));
        if (userId == null) return Result.fail(401, "未登录或Token已过期");
        SysUser user = userMapper.selectById(userId);
        if (user == null) return Result.fail(404, "用户不存在");
        user.setOpenid(null); // 不返回敏感字段
        return Result.ok(user);
    }

    /** 修改用户信息 */
    @PutMapping("/user")
    public Result<SysUser> updateProfile(@RequestHeader(value = "Authorization", required = false) String auth,
                                          @RequestBody UserProfileRequest request) {
        Long userId = tokenUtils.getUserId(extractToken(auth));
        if (userId == null) return Result.fail(401, "未登录或Token已过期");

        SysUser user = userMapper.selectById(userId);
        if (user == null) return Result.fail(404, "用户不存在");

        if (request.getNickname() != null) user.setNickname(request.getNickname());
        if (request.getAvatarUrl() != null) user.setAvatarUrl(request.getAvatarUrl());
        if (request.getPhone() != null) user.setPhone(request.getPhone());
        if (request.getGender() != null) user.setGender(request.getGender());
        if (request.getProvince() != null) user.setProvince(request.getProvince());
        if (request.getCity() != null) user.setCity(request.getCity());
        user.setUpdateTime(LocalDateTime.now());
        userMapper.updateById(user);

        user.setOpenid(null);
        return Result.ok(user);
    }

    /** 获取当前用户的浏览/提问历史（最近 20 条） */
    @GetMapping("/user/history")
    public Result<List<LlmInvokeLog>> history(@RequestHeader(value = "Authorization", required = false) String auth) {
        Long userId = tokenUtils.getUserId(extractToken(auth));
        if (userId == null) return Result.fail(401, "未登录");
        LambdaQueryWrapper<LlmInvokeLog> qw = new LambdaQueryWrapper<>();
        qw.eq(LlmInvokeLog::getUserId, userId)
          .orderByDesc(LlmInvokeLog::getCreateTime)
          .last("LIMIT 20");
        return Result.ok(logMapper.selectList(qw));
    }

    // ---- 内部 ----

    /** 调用微信 API 用 code 换取 openid */
    @SuppressWarnings("unchecked")
    private String resolveOpenid(String code) {
        // 开发环境未配置 appId 时，用 code 的 hash 作为模拟 openid
        if (appId == null || appId.isEmpty()) {
            log.warn("微信AppId未配置，使用模拟openid");
            return "mock_openid_" + Math.abs(code.hashCode());
        }
        try {
            String url = String.format(
                    "https://api.weixin.qq.com/sns/jscode2session?appid=%s&secret=%s&js_code=%s&grant_type=authorization_code",
                    appId, appSecret, code);
            ResponseEntity<Map> resp = restTemplate.getForEntity(url, Map.class);
            Map<String, Object> body = resp.getBody();
            if (body != null && body.get("openid") != null) {
                return String.valueOf(body.get("openid"));
            }
            log.error("微信登录返回异常: {}", body);
        } catch (Exception e) {
            log.error("调用微信API失败: {}", e.getMessage());
        }
        return null;
    }

    private String extractToken(String auth) {
        if (auth != null && auth.startsWith("Bearer ")) {
            return auth.substring(7);
        }
        return auth;
    }
}
