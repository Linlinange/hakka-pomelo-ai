package com.pomelo.ai.controller;

import com.pomelo.ai.common.Result;
import com.pomelo.ai.entity.ConversationMessage;
import com.pomelo.ai.service.ConversationService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 会话历史管理接口
 *
 * POST   /api/conversation/save            保存消息
 * POST   /api/conversation/save-batch      批量保存
 * GET    /api/conversation/history?sessionId=xxx&limit=50  加载历史
 * GET    /api/conversation/sessions?userId=xxx&limit=20    会话列表
 * DELETE /api/conversation/sessions/{sessionId}            删除会话
 */
@Slf4j
@RestController
@RequestMapping("/api/conversation")
@RequiredArgsConstructor
public class ConversationController {

    private final ConversationService conversationService;

    /** 保存单条消息 */
    @PostMapping("/save")
    public Result<ConversationMessage> save(@RequestBody ConversationMessage msg) {
        if (msg.getSessionId() == null || msg.getSessionId().isBlank()) {
            return Result.fail(400, "sessionId 不能为空");
        }
        if (msg.getRole() == null || msg.getRole().isBlank()) {
            return Result.fail(400, "role 不能为空");
        }
        ConversationMessage saved = conversationService.save(msg);
        return Result.ok(saved);
    }

    /** 批量保存消息 */
    @PostMapping("/save-batch")
    public Result<List<ConversationMessage>> saveBatch(@RequestBody List<ConversationMessage> messages) {
        if (messages == null || messages.isEmpty()) {
            return Result.fail(400, "消息列表不能为空");
        }
        List<ConversationMessage> saved = conversationService.saveBatch(messages);
        return Result.ok(saved);
    }

    /** 加载会话历史 */
    @GetMapping("/history")
    public Result<List<ConversationMessage>> getHistory(
            @RequestParam String sessionId,
            @RequestParam(defaultValue = "50") int limit) {
        List<ConversationMessage> history = conversationService.getHistory(sessionId, limit);
        return Result.ok(history);
    }

    /** 获取用户会话列表 */
    @GetMapping("/sessions")
    public Result<List<Map<String, Object>>> getUserSessions(
            @RequestParam(required = false) Long userId,
            @RequestParam(defaultValue = "20") int limit) {
        if (userId == null) {
            return Result.fail(400, "userId 不能为空");
        }
        List<Map<String, Object>> sessions = conversationService.getUserSessions(userId, limit);
        return Result.ok(sessions);
    }

    /** 删除会话 */
    @DeleteMapping("/sessions/{sessionId}")
    public Result<Integer> deleteSession(@PathVariable String sessionId) {
        int deleted = conversationService.deleteSession(sessionId);
        return Result.ok(deleted);
    }
}
