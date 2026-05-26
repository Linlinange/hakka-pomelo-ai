package com.pomelo.ai.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/** 算法参数表实体 */
@Data
@TableName("algo_rule_params")
public class AlgoRuleParams {

    @TableId(type = IdType.AUTO)
    private Long id;
    private String paramKey;
    private String paramName;
    private BigDecimal paramValue;
    private String paramType;       // WEIGHT / THRESHOLD / COEFFICIENT
    private String paramGroup;      // REQUIREMENT_MATCH / SCENE_FIT / HAKKA_FEATURE / LLM_ADAPT
    private String paramRange;
    private String description;
    private Integer status;
    private Integer sortOrder;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
