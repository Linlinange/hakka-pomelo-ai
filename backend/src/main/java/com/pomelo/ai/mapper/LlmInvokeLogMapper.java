package com.pomelo.ai.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.pomelo.ai.entity.LlmInvokeLog;
import org.apache.ibatis.annotations.Mapper;

/** 大模型调用日志 Mapper */
@Mapper
public interface LlmInvokeLogMapper extends BaseMapper<LlmInvokeLog> {
}
