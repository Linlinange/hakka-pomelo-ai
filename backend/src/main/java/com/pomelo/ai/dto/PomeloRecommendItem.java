package com.pomelo.ai.dto;

import lombok.Data;
import lombok.Builder;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import java.math.BigDecimal;
import java.util.List;

/** 推荐结果中的单条产品（V2.0支持多品类） */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PomeloRecommendItem {

    private Long id;
    private String productType;         // V2.0: 产品类型
    private String pomeloName;
    private String category;
    private String origin;
    private String specification;
    private String priceRange;
    private String tasteDescription;
    private String hakkaCultureRelation;
    private String productDescription;  // V2.0: 通用产品描述
    private String imageUrl;
    private String giftSceneTags;
    private String tags;

    // 打分明细
    private BigDecimal scorePriceMatch;
    private BigDecimal scoreSceneFit;
    private BigDecimal scoreHakkaFeature;
    private BigDecimal scoreProductFeature;  // V2.0: 产品特色评分
    private BigDecimal ruleTotal;
    private BigDecimal llmScore;
    private BigDecimal finalScore;

    /** 个性化推荐理由 */
    private String reason;
}
