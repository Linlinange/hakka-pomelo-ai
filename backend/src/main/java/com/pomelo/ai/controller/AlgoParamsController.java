package com.pomelo.ai.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.pomelo.ai.common.Result;
import com.pomelo.ai.entity.AlgoRuleParams;
import com.pomelo.ai.mapper.AlgoRuleParamsMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 算法参数管理接口 — 在线调参
 */
@Slf4j
@RestController
@RequestMapping("/api/algo-params")
@RequiredArgsConstructor
public class AlgoParamsController {

    private final AlgoRuleParamsMapper algoMapper;

    /** 获取所有启用的算法参数 */
    @GetMapping
    public Result<List<AlgoRuleParams>> list(@RequestParam(required = false) String group) {
        LambdaQueryWrapper<AlgoRuleParams> qw = new LambdaQueryWrapper<>();
        qw.eq(AlgoRuleParams::getStatus, 1);
        if (group != null && !group.isEmpty()) {
            qw.eq(AlgoRuleParams::getParamGroup, group);
        }
        qw.orderByAsc(AlgoRuleParams::getParamGroup, AlgoRuleParams::getSortOrder);
        return Result.ok(algoMapper.selectList(qw));
    }

    /** 修改参数值（管理员） */
    @PutMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public Result<AlgoRuleParams> update(@PathVariable Long id, @RequestBody AlgoRuleParams entity) {
        AlgoRuleParams exist = algoMapper.selectById(id);
        if (exist == null) return Result.fail(404, "参数不存在");
        entity.setId(id);
        entity.setUpdateTime(LocalDateTime.now());
        algoMapper.updateById(entity);
        log.info("修改算法参数: id={}, key={}, value={}", id, entity.getParamKey(), entity.getParamValue());
        return Result.ok(algoMapper.selectById(id));
    }
}
