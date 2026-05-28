package com.pomelo.ai.service.impl;

import com.pomelo.ai.entity.ConversationMessage;
import com.pomelo.ai.mapper.ConversationMessageMapper;
import com.pomelo.ai.service.ConversationService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * 会话历史服务实现
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class ConversationServiceImpl implements ConversationService {

    private final ConversationMessageMapper messageMapper;

    private static final int DEFAULT_HISTORY_LIMIT = 50;

    @Override
    public ConversationMessage save(ConversationMessage msg) {
        if (msg.getCreateTime() == null) {
            msg.setCreateTime(LocalDateTime.now());
        }
        messageMapper.insert(msg);
        return msg;
    }

    @Override
    public List<ConversationMessage> saveBatch(List<ConversationMessage> messages) {
        for (ConversationMessage msg : messages) {
            save(msg);
        }
        return messages;
    }

    @Override
    public List<ConversationMessage> getHistory(String sessionId, int limit) {
        int effectiveLimit = limit > 0 ? limit : DEFAULT_HISTORY_LIMIT;
        return messageMapper.findBySessionId(sessionId, effectiveLimit);
    }

    @Override
    public List<Map<String, Object>> getUserSessions(Long userId, int limit) {
        int effectiveLimit = limit > 0 ? limit : 20;
        return messageMapper.findSessionsByUserId(userId, effectiveLimit);
    }

    @Override
    public int deleteSession(String sessionId) {
        int deleted = messageMapper.deleteBySessionId(sessionId);
        log.info("删除会话: sessionId={}, count={}", sessionId, deleted);
        return deleted;
    }

    @Override
    public int cleanExpired(int days) {
        int effectiveDays = days > 0 ? days : 30;
        int cleaned = messageMapper.deleteExpired(effectiveDays);
        log.info("清理过期会话: days={}, count={}", effectiveDays, cleaned);
        return cleaned;
    }
}
