package com.pomelo.ai.dto;

import lombok.Data;

/** 用户信息修改请求 */
@Data
public class UserProfileRequest {

    private String nickname;
    private String avatarUrl;
    private String phone;
    private Integer gender;
    private String province;
    private String city;
}
