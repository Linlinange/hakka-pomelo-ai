package com.pomelo.ai.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.pomelo.ai.entity.PomeloPromptLibrary;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

/** Prompt库 Mapper */
@Mapper
public interface PromptLibraryMapper extends BaseMapper<PomeloPromptLibrary> {

    /** 获取指定场景当前启用的Prompt模板 */
    @Select("""
        SELECT * FROM pomelo_prompt_library
        WHERE scene_category = #{sceneCategory}
          AND is_current = 1 AND status = 1
        ORDER BY priority DESC LIMIT 1
        """)
    PomeloPromptLibrary getCurrentByScene(@Param("sceneCategory") String sceneCategory);
}
