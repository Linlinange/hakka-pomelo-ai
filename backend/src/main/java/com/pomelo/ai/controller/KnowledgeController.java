package com.pomelo.ai.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.pomelo.ai.common.Result;
import com.pomelo.ai.entity.GoldenPomeloKnowledge;
import com.pomelo.ai.mapper.PomeloKnowledgeMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 金柚知识库管理 CRUD 接口
 *
 * GET    /api/knowledge      获取所有知识条目
 * GET    /api/knowledge/{id} 获取单条
 * POST   /api/knowledge      新增（管理员）
 * PUT    /api/knowledge/{id} 修改（管理员）
 * DELETE /api/knowledge/{id} 删除（管理员）
 */
@Slf4j
@RestController
@RequestMapping("/api/knowledge")
@RequiredArgsConstructor
public class KnowledgeController {

    private final PomeloKnowledgeMapper knowledgeMapper;

    /** 获取所有上架知识条目 */
    @GetMapping
    public Result<List<GoldenPomeloKnowledge>> list(
            @RequestParam(required = false) String category,
            @RequestParam(required = false) String keyword) {
        LambdaQueryWrapper<GoldenPomeloKnowledge> qw = new LambdaQueryWrapper<>();
        qw.eq(GoldenPomeloKnowledge::getStatus, 1);
        if (category != null && !category.isEmpty()) {
            qw.eq(GoldenPomeloKnowledge::getCategory, category);
        }
        if (keyword != null && !keyword.isEmpty()) {
            qw.like(GoldenPomeloKnowledge::getPomeloName, keyword);
        }
        qw.orderByDesc(GoldenPomeloKnowledge::getCreateTime);
        return Result.ok(knowledgeMapper.selectList(qw));
    }

    /** 获取单条 */
    @GetMapping("/{id}")
    public Result<GoldenPomeloKnowledge> getById(@PathVariable Long id) {
        GoldenPomeloKnowledge entity = knowledgeMapper.selectById(id);
        if (entity == null) return Result.fail(404, "知识条目不存在");
        return Result.ok(entity);
    }

    /** 新增（管理员） */
    @PostMapping
    @PreAuthorize("hasRole('ADMIN')")
    public Result<GoldenPomeloKnowledge> create(@RequestBody GoldenPomeloKnowledge entity) {
        entity.setCreateTime(LocalDateTime.now());
        entity.setUpdateTime(LocalDateTime.now());
        entity.setStatus(1);
        knowledgeMapper.insert(entity);
        log.info("新增知识条目: id={}, name={}", entity.getId(), entity.getPomeloName());
        return Result.ok(entity);
    }

    /** 修改（管理员） */
    @PutMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public Result<GoldenPomeloKnowledge> update(@PathVariable Long id,
                                                 @RequestBody GoldenPomeloKnowledge entity) {
        GoldenPomeloKnowledge exist = knowledgeMapper.selectById(id);
        if (exist == null) return Result.fail(404, "知识条目不存在");
        entity.setId(id);
        entity.setUpdateTime(LocalDateTime.now());
        knowledgeMapper.updateById(entity);
        log.info("修改知识条目: id={}", id);
        return Result.ok(knowledgeMapper.selectById(id));
    }

    /** 删除（管理员，逻辑删除） */
    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public Result<Void> delete(@PathVariable Long id) {
        GoldenPomeloKnowledge exist = knowledgeMapper.selectById(id);
        if (exist == null) return Result.fail(404, "知识条目不存在");
        knowledgeMapper.deleteById(id);  // MyBatis-Plus 逻辑删除
        log.info("删除知识条目: id={}", id);
        return Result.ok();
    }
}
