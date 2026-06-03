package com.pomelo.ai.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/** 产品知识库实体（原金柚知识库，V2.0扩展为多品类） */
@Data
@TableName("golden_pomelo_knowledge")
public class GoldenPomeloKnowledge {

    @TableId(type = IdType.AUTO)
    private Long id;
    private String productType;           // V2.0: 产品类型 pomelo/apple/banana/watermelon...
    private String pomeloName;            // 产品品名（兼容历史字段名）
    private String category;
    private String origin;
    private String specification;
    private String weightRange;
    private String priceRange;
    private String seasonInfo;
    private String cultivationProcess;
    private String hakkaCultureRelation;  // 客家文化关联（仅pomelo）
    private String productDescription;    // V2.0: 通用产品描述（非pomelo使用）
    private String identificationTips;
    private String preservationMethod;
    private String ediblePairing;
    private String nutritionalValue;
    private String tasteDescription;
    private String storyContent;
    private String imageUrl;
    private String tags;
    private String giftSceneTags;
    private BigDecimal scoreRequirementMatch;
    private BigDecimal scoreSceneFit;
    private BigDecimal scoreHakkaFeature;
    private BigDecimal scoreProductFeature;  // V2.0: 通用产品特色评分
    private Integer viewCount;
    private Integer recCount;
    private Integer status;

    @TableLogic
    private Integer isDeleted;

    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
