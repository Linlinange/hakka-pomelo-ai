const { generateContent } = require('../../utils/request');

Page({
  data: {
    scene: 'social',       // 'ecommerce' | 'social'
    prompt: '',
    pomeloName: '客家金柚',
    result: null,          // { content, scene, pomelo_name, created_at }
    loading: false,
  },

  onSceneChange(e) {
    this.setData({ scene: e.currentTarget.dataset.scene });
  },

  onInput(e) {
    const field = e.currentTarget.dataset.field;
    this.setData({ [field]: e.detail.value });
  },

  /** 生成内容 */
  onGenerate() {
    if (this.data.loading) return;
    this.setData({ loading: true, result: null });

    generateContent({
      scene: this.data.scene,
      prompt: this.data.prompt,
      pomeloName: this.data.pomeloName,
    })
      .then(res => {
        this.setData({ result: res, loading: false });
      })
      .catch(err => {
        console.error('生成失败:', err);
        wx.showToast({ title: '生成失败，请重试', icon: 'none' });
        this.setData({ loading: false });
      });
  },

  /** 复制文案 */
  onCopy() {
    if (!this.data.result) return;
    wx.setClipboardData({
      data: this.data.result.content,
      success: () => wx.showToast({ title: '已复制到剪贴板', icon: 'success' }),
    });
  },
});
