package com.pomelo.ai.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.pomelo.ai.common.Result;
import com.pomelo.ai.entity.PomeloPromptLibrary;
import com.pomelo.ai.mapper.PromptLibraryMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;

/**
 * Prompt 库管理 CRUD 接口
 *
 * GET    /api/prompt      获取所有 Prompt 模板
 * GET    /api/prompt/{id} 获取单条
 * POST   /api/prompt      新增（管理员）
 * PUT    /api/prompt/{id} 修改（管理员）
 * DELETE /api/prompt/{id} 删除（管理员）
 */
@Slf4j
@RestController
@RequestMapping("/api/prompt")
@RequiredArgsConstructor
public class PromptController {

    private final PromptLibraryMapper promptMapper;

    /** 获取所有启用的 Prompt */
    @GetMapping
    public Result<List<PomeloPromptLibrary>> list(
            @RequestParam(required = false) String sceneCategory) {
        LambdaQueryWrapper<PomeloPromptLibrary> qw = new LambdaQueryWrapper<>();
        qw.eq(PomeloPromptLibrary::getStatus, 1);
        if (sceneCategory != null && !sceneCategory.isEmpty()) {
            qw.eq(PomeloPromptLibrary::getSceneCategory, sceneCategory);
        }
        qw.orderByDesc(PomeloPromptLibrary::getPriority);
        return Result.ok(promptMapper.selectList(qw));
    }

    /** 获取单条 */
    @GetMapping("/{id}")
    public Result<PomeloPromptLibrary> getById(@PathVariable Long id) {
        PomeloPromptLibrary entity = promptMapper.selectById(id);
        if (entity == null) return Result.fail(404, "Prompt 模板不存在");
        return Result.ok(entity);
    }

    /** 新增（管理员） */
    @PostMapping
    @PreAuthorize("hasRole('ADMIN')")
    public Result<PomeloPromptLibrary> create(@RequestBody PomeloPromptLibrary entity) {
        entity.setCreateTime(LocalDateTime.now());
        entity.setUpdateTime(LocalDateTime.now());
        entity.setStatus(1);
        if (entity.getIsCurrent() == null) entity.setIsCurrent(0);
        promptMapper.insert(entity);
        log.info("新增Prompt模板: id={}, name={}", entity.getId(), entity.getPromptName());
        return Result.ok(entity);
    }

    /** 修改（管理员） */
    @PutMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public Result<PomeloPromptLibrary> update(@PathVariable Long id,
                                               @RequestBody PomeloPromptLibrary entity) {
        PomeloPromptLibrary exist = promptMapper.selectById(id);
        if (exist == null) return Result.fail(404, "Prompt 模板不存在");
        entity.setId(id);
        entity.setUpdateTime(LocalDateTime.now());
        promptMapper.updateById(entity);
        log.info("修改Prompt模板: id={}", id);
        return Result.ok(promptMapper.selectById(id));
    }

    /** 删除（管理员，物理删除 — Prompt 模板无 is_deleted 字段） */
    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public Result<Void> delete(@PathVariable Long id) {
        PomeloPromptLibrary exist = promptMapper.selectById(id);
        if (exist == null) return Result.fail(404, "Prompt 模板不存在");
        promptMapper.deleteById(id);
        log.info("删除Prompt模板: id={}", id);
        return Result.ok();
    }

    /** 设为当前版本 */
    @PutMapping("/{id}/activate")
    @PreAuthorize("hasRole('ADMIN')")
    public Result<Void> activate(@PathVariable Long id) {
        PomeloPromptLibrary entity = promptMapper.selectById(id);
        if (entity == null) return Result.fail(404, "Prompt 模板不存在");

        // 先将同场景其他模板的 is_current 置为 0
        LambdaQueryWrapper<PomeloPromptLibrary> qw = new LambdaQueryWrapper<>();
        qw.eq(PomeloPromptLibrary::getSceneCategory, entity.getSceneCategory());
        List<PomeloPromptLibrary> sameScene = promptMapper.selectList(qw);
        for (PomeloPromptLibrary t : sameScene) {
            t.setIsCurrent(0);
            promptMapper.updateById(t);
        }

        // 激活当前
        entity.setIsCurrent(1);
        promptMapper.updateById(entity);
        log.info("激活Prompt模板: id={}, scene={}", id, entity.getSceneCategory());
        return Result.ok();
    }
}
