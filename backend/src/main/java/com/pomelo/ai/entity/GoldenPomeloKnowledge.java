package com.pomelo.ai.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/** 金柚知识库实体 */
@Data
@TableName("golden_pomelo_knowledge")
public class GoldenPomeloKnowledge {

    @TableId(type = IdType.AUTO)
    private Long id;
    private String pomeloName;
    private String category;
    private String origin;
    private String specification;
    private String weightRange;
    private String priceRange;
    private String seasonInfo;
    private String cultivationProcess;
    private String hakkaCultureRelation;
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
    private Integer viewCount;
    private Integer recCount;
    private Integer status;

    @TableLogic
    private Integer isDeleted;

    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
