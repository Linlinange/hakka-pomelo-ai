/**
 * AI智荐对话页面
 *
 * 功能：
 * 1. 聊天气泡式交互（用户提问 / AI 回答）
 * 2. 调用 /api/recommend 获取推荐结果
 * 3. AI 回答中嵌入金柚卡片组件
 * 4. 加载态：打字动画、"AI正在思考中..."
 * 5. 会话历史持久化 + 恢复
 */

const { recommend, qa, saveMessage, getHistory, getSessions, deleteSession } = require('../../utils/request');

const MAX_INPUT_LENGTH = 500;

const SYSTEM_HINT = '我是客家金柚AI导购，你可以：\n• 输入选购需求，如"200元中秋送礼推荐"\n• 输入知识问题，如"金柚怎么保存"\n• 点击下方[选购推荐]/[知识问答]切换模式';

const QA_HINT = '我是客家金柚知识专家，你可以问我：\n• "金柚皮怎么制作客家菜？"\n• "沙田柚和蜜柚有什么区别？"\n• "金柚有什么营养价值？"';

const MODE_HINTS = { recommend: SYSTEM_HINT, qa: QA_HINT };

Page({
  data: {
    messages: [],
    inputText: '',
    loading: false,
    sessionId: '',
    scrollToId: '',
    autoScroll: true,
    mode: 'recommend',
    showHistory: false,
    sessionList: [],
  },

  onLoad() {
    this._restoreSession();
  },

  /** 恢复或创建会话 */
  async _restoreSession() {
    const sid = wx.getStorageSync('pomelo_session_id');
    if (sid) {
      this.setData({ sessionId: sid });
      try {
        const history = await getHistory(sid, 50);
        if (history && history.length > 0) {
          this.setData({
            messages: history.map(m => ({
              id: this._genMsgId(),
              role: m.role,
              type: m.msgType || 'text',
              content: m.content,
              recommendations: m.metadataJson ? JSON.parse(m.metadataJson).items : undefined,
              time: this._formatTime(new Date(m.createTime)),
            })),
          });
          return;
        }
      } catch (e) {
        console.warn('加载历史失败:', e);
      }
    }
    // 无历史，创建新会话
    this._newSession(false);
    this._addMessage('ai', 'text', SYSTEM_HINT);
  },

  _newSession(persist = true) {
    const sid = 'wx_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
    this.setData({ sessionId: sid, messages: [] });
    if (persist) wx.setStorageSync('pomelo_session_id', sid);
  },

  /** 切换模式 */
  onSwitchMode(e) {
    const mode = e.currentTarget.dataset.mode;
    if (mode === this.data.mode) return;
    this.setData({ mode });
    this._addMessage('ai', 'text', MODE_HINTS[mode]);
  },

  onInput(e) {
    const val = e.detail.value;
    if (val.length <= MAX_INPUT_LENGTH) {
      this.setData({ inputText: val });
    }
  },

  /** 发送消息 */
  async onSend() {
    const text = this.data.inputText.trim();
    if (!text || this.data.loading || text.length > MAX_INPUT_LENGTH) return;

    // 保存用户消息
    this._addMessage('user', 'text', text);
    this.setData({ inputText: '' });
    this._showLoading();

    // 持久化用户消息
    saveMessage({
      sessionId: this.data.sessionId,
      role: 'user',
      msgType: 'text',
      content: text,
    }).catch(() => {});

    const isQa = this.data.mode === 'qa';
    const apiCall = isQa ? qa(text, this.data.sessionId) : recommend(text, this.data.sessionId);

    try {
      const res = await apiCall;
      this._hideLoading();

      if (isQa) {
        this._handleQaResponse(res);
      } else {
        this._handleRecommendResponse(res);
      }
    } catch (err) {
      this._hideLoading();
      console.error('请求失败:', err);
      this._addMessage('ai', 'text', '抱歉，网络出了一点问题，请稍后再试～');
    }
  },

  /** 快捷提问 */
  onQuickAsk(e) {
    const text = e.currentTarget.dataset.text;
    this.setData({ inputText: text });
    this.onSend();
  },

  /** 新建会话 */
  onNewChat() {
    this._newSession(true);
    this._addMessage('ai', 'text', SYSTEM_HINT);
  },

  /** 切换历史面板 */
  async onToggleHistory() {
    const show = !this.data.showHistory;
    this.setData({ showHistory: show });
    if (show) {
      try {
        const sessions = await getSessions(1, 20);
        this.setData({ sessionList: sessions || [] });
      } catch { this.setData({ sessionList: [] }); }
    }
  },

  /** 切换到指定会话 */
  async onSwitchSession(e) {
    const sid = e.currentTarget.dataset.sid;
    this.setData({ showHistory: false, sessionId: sid, messages: [] });
    wx.setStorageSync('pomelo_session_id', sid);
    try {
      const history = await getHistory(sid, 50);
      if (history && history.length > 0) {
        this.setData({
          messages: history.map(m => ({
            id: this._genMsgId(),
            role: m.role,
            type: m.msgType || 'text',
            content: m.content,
            recommendations: m.metadataJson ? JSON.parse(m.metadataJson).items : undefined,
            time: this._formatTime(new Date(m.createTime)),
          })),
        });
      }
    } catch {}
  },

  /** 删除当前会话 */
  async onDeleteSession() {
    const res = await new Promise(r => wx.showModal({ title: '确认删除', content: '删除当前会话？', success: r }));
    if (!res.confirm) return;
    try { await deleteSession(this.data.sessionId); } catch {}
    this._newSession(true);
    this._addMessage('ai', 'text', SYSTEM_HINT);
  },

  onScroll(e) {},
  onScrollToLower() { this.setData({ autoScroll: true }); },

  // ==================== 内部方法 ====================

  _addMessage(role, type, content, extra = {}) {
    const msg = {
      id: this._genMsgId(),
      role, type, content,
      time: this._formatTime(new Date()),
      ...extra,
    };
    this.setData({
      messages: [...this.data.messages, msg],
      scrollToId: 'msg-' + msg.id,
    });
  },

  _showLoading() {
    this.setData({ loading: true });
    const lid = this._genMsgId();
    this.setData({
      loadingMsgId: lid,
      messages: [...this.data.messages, { id: lid, role: 'ai', type: 'loading', content: '', time: '' }],
      scrollToId: 'msg-' + lid,
    });
  },

  _hideLoading() {
    const messages = this.data.messages.filter(m => m.id !== this.data.loadingMsgId);
    this.setData({ loading: false, messages });
  },

  _handleRecommendResponse(res) {
    const recs = res.recommendations || [];
    if (recs.length === 0) {
      this._addMessage('ai', 'text', '暂时没有找到符合您需求的金柚，试试换个方式描述吧～');
      return;
    }
    const intentObj = res.intent || {};
    const intentType = intentObj.intent || 'BUY';
    const top3 = recs.slice(0, 3);
    const summary = this._buildSummary(intentType, top3.length);
    this._addMessage('ai', 'recommend', summary, { recommendations: top3, intent: intentType });

    // 持久化
    saveMessage({
      sessionId: this.data.sessionId,
      role: 'ai',
      msgType: 'recommend',
      content: summary,
      metadataJson: JSON.stringify({ items: top3, intent: intentObj }),
    }).catch(() => {});
  },

  _handleQaResponse(res) {
    const answer = res.answer || '抱歉，暂时无法回答这个问题。';
    const source = res.source || '';
    const prefix = source === 'KNOWLEDGE_BASE' ? '📎 ' : '🤖 ';
    this._addMessage('ai', 'text', prefix + answer);
    saveMessage({
      sessionId: this.data.sessionId,
      role: 'ai',
      msgType: 'text',
      content: prefix + answer,
    }).catch(() => {});
  },

  _buildSummary(intentType, count) {
    return intentType === 'BUY'
      ? `为您精选了 ${count} 款客家金柚，请看看合不合心意：`
      : `根据您的问题，为您找到 ${count} 款相关金柚：`;
  },

  _genSessionId() {
    return 'wx_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
  },
  _genMsgId() {
    return 'm_' + Date.now() + '_' + Math.random().toString(36).slice(2, 6);
  },
  _formatTime(date) {
    const h = date.getHours().toString().padStart(2, '0');
    const m = date.getMinutes().toString().padStart(2, '0');
    return h + ':' + m;
  },
});
