package com.pomelo.ai.dto;

import lombok.Data;
import lombok.Builder;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

/** 内容生成响应 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ContentResponse {

    /** 生成的内容 */
    private String content;

    /** 场景类型 */
    private String scene;

    /** 金柚品名 */
    private String pomeloName;

    /** 创建时间 */
    private String createdAt;
}
