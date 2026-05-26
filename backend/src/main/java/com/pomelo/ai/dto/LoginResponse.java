package com.pomelo.ai.dto;

import lombok.Data;
import lombok.Builder;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

/** 登录响应 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class LoginResponse {

    /** 认证 Token */
    private String token;

    /** 用户 ID */
    private Long userId;

    /** 用户昵称 */
    private String nickname;

    /** 头像 URL */
    private String avatarUrl;

    /** 是否新用户 */
    private Boolean isNewUser;
}
