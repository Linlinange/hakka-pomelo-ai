package com.pomelo.ai.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.pomelo.ai.entity.GoldenPomeloKnowledge;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import java.util.List;

/** 产品知识库 Mapper */
@Mapper
public interface PomeloKnowledgeMapper extends BaseMapper<GoldenPomeloKnowledge> {

    /**
     * 全文关键词检索知识库
     */
    @Select("""
        SELECT * FROM golden_pomelo_knowledge
        WHERE is_deleted = 0 AND status = 1
          AND (MATCH(pomelo_name, taste_description, hakka_culture_relation, product_description, cultivation_process, edible_pairing) AGAINST(#{keyword} IN BOOLEAN MODE)
               OR pomelo_name LIKE CONCAT('%', #{keyword}, '%')
               OR tags LIKE CONCAT('%', #{keyword}, '%')
               OR origin LIKE CONCAT('%', #{keyword}, '%'))
        ORDER BY view_count DESC
        LIMIT #{limit}
        """)
    List<GoldenPomeloKnowledge> searchByKeyword(@Param("keyword") String keyword, @Param("limit") int limit);

    /**
     * 标签模糊匹配检索
     */
    @Select("""
        SELECT * FROM golden_pomelo_knowledge
        WHERE is_deleted = 0 AND status = 1
          AND (tags LIKE CONCAT('%', #{tag}, '%')
               OR gift_scene_tags LIKE CONCAT('%', #{tag}, '%')
               OR pomelo_name LIKE CONCAT('%', #{tag}, '%'))
        ORDER BY score_requirement_match DESC
        LIMIT #{limit}
        """)
    List<GoldenPomeloKnowledge> searchByTag(@Param("tag") String tag, @Param("limit") int limit);

    /**
     * 召回全部上架产品（供推荐算法使用）
     */
    @Select("SELECT * FROM golden_pomelo_knowledge WHERE is_deleted = 0 AND status = 1")
    List<GoldenPomeloKnowledge> selectAllActive();

    /**
     * V2.0: 按产品类型筛选
     */
    @Select("SELECT * FROM golden_pomelo_knowledge WHERE is_deleted = 0 AND status = 1 AND product_type = #{productType}")
    List<GoldenPomeloKnowledge> selectByProductType(@Param("productType") String productType);
}
