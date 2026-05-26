package com.pomelo.ai.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/** 内容生成请求 */
@Data
public class ContentRequest {

    /** 场景类型：ecommerce-电商文案 / social-朋友圈推广 */
    @NotBlank(message = "场景类型不能为空")
    private String scene;

    /** 可选，自定义额外要求 */
    private String prompt;

    /** 可选，指定金柚品名 */
    private String pomeloName;

    /** 可选，文案风格 */
    private String style;
}
