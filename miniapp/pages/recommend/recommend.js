/**
 * AI智荐对话页面
 *
 * 功能：
 * 1. 聊天气泡式交互（用户提问 / AI 回答）
 * 2. 调用 /api/recommend 获取推荐结果
 * 3. AI 回答中嵌入金柚卡片组件
 * 4. 加载态：打字动画「AI正在思考中...」
 * 5. 上拉加载历史对话、下拉回到底部
 */

const { recommend, qa } = require('../../utils/request');

// 系统提示语
const SYSTEM_HINT = '我是客家金柚AI导购，你可以：\n• 输入选购需求，如"200元中秋送礼推荐"\n• 输入知识问题，如"金柚怎么保存"\n• 点击下方[选购推荐]/[知识问答]切换模式';

const QA_HINT = '我是客家金柚知识专家，你可以问我：\n• "金柚皮怎么制作客家菜？"\n• "沙田柚和蜜柚有什么区别？"\n• "金柚有什么营养价值？"';

Page({
  data: {
    messages: [],
    inputText: '',
    loading: false,
    sessionId: '',
    scrollToId: '',
    autoScroll: true,
    inputHeight: 44,
    mode: 'recommend',  // 'recommend' | 'qa'
  },

  onLoad() {
    this.setData({ sessionId: this._genSessionId() });
    this._addMessage('ai', 'text', SYSTEM_HINT);

    // 处理首页传来的快捷提问
    const quickQuery = wx.getStorageSync('quick_query');
    if (quickQuery) {
      wx.removeStorageSync('quick_query');
      // 延迟发送，等页面渲染完
      setTimeout(() => {
        this.setData({ inputText: quickQuery });
        this.onSend();
      }, 500);
    }
  },

  /** 切换模式 */
  onSwitchMode(e) {
    const mode = e.currentTarget.dataset.mode;
    if (mode === this.data.mode) return;
    this.setData({ mode });
    const hint = mode === 'qa' ? QA_HINT : SYSTEM_HINT;
    this._addMessage('ai', 'text', hint);
  },

  // ==================== 输入框事件 ====================

  onInput(e) {
    this.setData({ inputText: e.detail.value });
  },

  /** 发送消息 */
  onSend() {
    const text = this.data.inputText.trim();
    if (!text || this.data.loading) return;

    // 1. 添加用户消息
    this._addMessage('user', 'text', text);
    this.setData({ inputText: '' });

    // 2. 显示加载态
    this._showLoading();

    // 3. 根据模式调用不同接口
    const apiCall = this.data.mode === 'qa'
      ? qa(text, this.data.sessionId)
      : recommend(text, this.data.sessionId);

    apiCall
      .then(res => {
        this._hideLoading();
        if (this.data.mode === 'qa') {
          this._handleQaResponse(res);
        } else {
          this._handleRecommendResponse(res);
        }
      })
      .catch(err => {
        this._hideLoading();
        console.error('请求失败:', err);
        this._addMessage('ai', 'text', '抱歉，网络出了一点问题，请稍后再试～');
      });
  },

  /** 快捷提问 */
  onQuickAsk(e) {
    const text = e.currentTarget.dataset.text;
    this.setData({ inputText: text });
    this.onSend();
  },

  // ==================== 页面滚动事件 ====================

  onScroll(e) {
    // 如果用户手动上滑，停止自动滚动
    const scrollTop = e.detail.scrollTop;
    // 简单判断：如果离底部超过 200rpx，停止自动滚动
  },

  onScrollToLower() {
    this.setData({ autoScroll: true });
  },

  // ==================== 内部方法 ====================

  /** 添加一条消息 */
  _addMessage(role, type, content, extra = {}) {
    const msg = {
      id: this._genMsgId(),
      role,          // 'user' | 'ai'
      type,          // 'text' | 'recommend'
      content,       // 文本内容
      time: this._formatTime(new Date()),
      ...extra,
    };

    this.setData({
      messages: [...this.data.messages, msg],
      scrollToId: 'msg-' + msg.id,
    });
  },

  /** 显示 AI 思考中... 动画 */
  _showLoading() {
    this.setData({ loading: true });
    const loadingId = this._genMsgId();
    this.setData({
      loadingMsgId: loadingId,
      messages: [...this.data.messages, {
        id: loadingId,
        role: 'ai',
        type: 'loading',
        content: '',
        time: '',
      }],
      scrollToId: 'msg-' + loadingId,
    });
  },

  /** 隐藏 AI 思考中... 动画 */
  _hideLoading() {
    // 移除 loading 消息
    const messages = this.data.messages.filter(m => m.id !== this.data.loadingMsgId);
    this.setData({ loading: false, messages });
  },

  /**
   * 处理 Spring Boot 推荐响应。
   * RecommendResponse 结构:
   *   { recommendations: [...], intent: {intent, confidence, needs_confirm, ...}, count, fromCache, sessionId, costMs }
   */
  _handleRecommendResponse(res) {
    const recommendations = res.recommendations || [];
    const intentObj = res.intent || {};
    const intentType = intentObj.intent || 'BUY';
    const needsConfirm = intentObj.needs_confirm || false;

    // 如果没有推荐结果
    if (recommendations.length === 0) {
      this._addMessage('ai', 'text', '暂时没有找到符合您需求的金柚，试试换个方式描述吧～');
      return;
    }

    // 如果置信度不足，追加一句确认引导
    if (needsConfirm) {
      this._addMessage('ai', 'text', '您的意思是...我按照理解帮您筛选了几款，如果不太对可以再说详细一点哦～');
    }

    // 添加推荐结果消息（嵌入金柚卡片）
    const top3 = recommendations.slice(0, 3);
    const summary = this._buildSummary(intentType, top3.length);
    this._addMessage('ai', 'recommend', summary, {
      recommendations: top3,
      intent: intentType,
    });
  },

  /** 处理问答响应 */
  _handleQaResponse(res) {
    const answer = res.answer || '抱歉，暂时无法回答这个问题。';
    const source = res.source || '';
    const prefix = source === 'KNOWLEDGE_BASE' ? '📚 ' : '🤖 ';
    this._addMessage('ai', 'text', prefix + answer);
  },

  /** 构建摘要文案 */
  _buildSummary(intentType, count) {
    if (intentType === 'BUY') {
      return `为您精选了 ${count} 款客家金柚，请看看合不合心意：`;
    }
    return `根据您的问题，为您找到 ${count} 款相关金柚：`;
  },

  // ==================== 工具方法 ====================

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
