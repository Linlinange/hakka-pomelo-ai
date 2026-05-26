package com.pomelo.ai.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.pomelo.ai.entity.SysUser;
import org.apache.ibatis.annotations.Mapper;

/** 用户表 Mapper */
@Mapper
public interface SysUserMapper extends BaseMapper<SysUser> {
}
