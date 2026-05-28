package com.pomelo.ai.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.pomelo.ai.entity.ConversationMessage;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Delete;

import java.util.List;

/**
 * 会话消息 Mapper
 */
@Mapper
public interface ConversationMessageMapper extends BaseMapper<ConversationMessage> {

    /**
     * 按会话ID查询最近消息（按时间正序）
     */
    @Select("""
        SELECT * FROM conversation_message
        WHERE session_id = #{sessionId}
        ORDER BY create_time ASC
        LIMIT #{limit}
        """)
    List<ConversationMessage> findBySessionId(@Param("sessionId") String sessionId,
                                               @Param("limit") int limit);

    /**
     * 获取用户的所有会话ID列表（按最近活跃时间排序）
     */
    @Select("""
        SELECT session_id, MAX(create_time) as last_time, COUNT(*) as msg_count
        FROM conversation_message
        WHERE user_id = #{userId}
        GROUP BY session_id
        ORDER BY last_time DESC
        LIMIT #{limit}
        """)
    List<java.util.Map<String, Object>> findSessionsByUserId(@Param("userId") Long userId,
                                                              @Param("limit") int limit);

    /**
     * 删除指定会话的所有消息
     */
    @Delete("DELETE FROM conversation_message WHERE session_id = #{sessionId}")
    int deleteBySessionId(@Param("sessionId") String sessionId);

    /**
     * 清理超过指定天数的旧会话
     */
    @Delete("""
        DELETE FROM conversation_message
        WHERE create_time < DATE_SUB(NOW(), INTERVAL #{days} DAY)
        """)
    int deleteExpired(@Param("days") int days);
}
