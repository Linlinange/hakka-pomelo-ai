package com.pomelo.ai.service;

import com.pomelo.ai.entity.ConversationMessage;

import java.util.List;
import java.util.Map;

/**
 * 会话历史服务接口
 */
public interface ConversationService {

    /** 保存一条消息 */
    ConversationMessage save(ConversationMessage msg);

    /** 批量保存消息 */
    List<ConversationMessage> saveBatch(List<ConversationMessage> messages);

    /** 查询会话历史（最近N条，按时间正序） */
    List<ConversationMessage> getHistory(String sessionId, int limit);

    /** 获取用户的会话列表 */
    List<Map<String, Object>> getUserSessions(Long userId, int limit);

    /** 删除指定会话 */
    int deleteSession(String sessionId);

    /** 清理过期会话（>30天） */
    int cleanExpired(int days);
}
