package com.pomelo.ai.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/** 金柚Prompt库实体 */
@Data
@TableName("pomelo_prompt_library")
public class PomeloPromptLibrary {

    @TableId(type = IdType.AUTO)
    private Long id;
    private String promptName;
    private String sceneCategory;   // BUY / QA / GEN
    private String applicableScene;
    private String promptTemplate;
    private String variablesSchema;
    private String systemRoleDesc;
    private String version;
    private Integer isCurrent;
    private Integer priority;
    private Integer maxTokens;
    private BigDecimal temperature;
    private Integer status;
    private String remark;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
