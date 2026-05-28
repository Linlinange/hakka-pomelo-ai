package com.pomelo.ai.entity;

import com.baomidou.mybatisplus.annotation.*;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 会话消息实体 — 存储用户对话历史
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@TableName("conversation_message")
public class ConversationMessage {

    @TableId(type = IdType.AUTO)
    private Long id;

    /** 用户ID（匿名用户为null） */
    private Long userId;

    /** 会话ID，由前端生成并持久化 */
    @JsonProperty("sessionId")
    private String sessionId;

    /** 角色：user / ai */
    private String role;

    /** 消息类型：text / recommend */
    @JsonProperty("msgType")
    private String msgType;

    /** 消息文本内容 */
    private String content;

    /** 扩展元数据（推荐结果JSON等） */
    @JsonProperty("metadataJson")
    private String metadataJson;

    /** 消息创建时间 */
    private LocalDateTime createTime;
}
