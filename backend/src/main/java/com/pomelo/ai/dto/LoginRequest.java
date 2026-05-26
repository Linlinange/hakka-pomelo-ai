package com.pomelo.ai.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/** 微信登录请求 */
@Data
public class LoginRequest {

    /** 微信 wx.login() 返回的临时 code */
    @NotBlank(message = "code不能为空")
    private String code;

    /** 可选：微信用户昵称 */
    private String nickname;

    /** 可选：微信头像 URL */
    private String avatarUrl;
}
