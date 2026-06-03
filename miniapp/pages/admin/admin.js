const { get, post, put, del } = require('../../utils/request');

Page({
  data: {
    tab: 'knowledge',        // 'knowledge' | 'prompt'
    knowledgeList: [],
    promptList: [],
    loading: false,
    editMode: false,
    editItem: null,
    productTypes: ['pomelo', 'apple', 'banana', 'watermelon', 'orange', 'grape'],
  },

  onShow() {
    this.loadData();
  },

  switchTab(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({ tab, editMode: false, editItem: null });
    this.loadData();
  },

  // ---- 加载 ----

  loadData() {
    this.setData({ loading: true });
    const isKnowledge = this.data.tab === 'knowledge';
    const url = isKnowledge ? '/knowledge' : '/prompt';

    get(url)
      .then(data => {
        this.setData({
          [isKnowledge ? 'knowledgeList' : 'promptList']: data || [],
          loading: false,
        });
      })
      .catch(() => this.setData({ loading: false }));
  },

  // ---- 新增 ----

  onProductTypeChange(e) {
    const val = this.data.productTypes[e.detail.value];
    this.setData({ 'editItem.productType': val });
  },

  onAdd() {
    const isKnowledge = this.data.tab === 'knowledge';
    const emptyItem = isKnowledge
      ? { pomeloName: '', productType: 'pomelo', category: '', origin: '', tasteDescription: '', productDescription: '', specification: '', priceRange: '' }
      : { promptName: '', sceneCategory: 'BUY', promptTemplate: '', systemRoleDesc: '' };
    this.setData({ editMode: true, editItem: emptyItem, isNew: true });
  },

  // ---- 编辑 ----

  onEdit(e) {
    const idx = e.currentTarget.dataset.index;
    const list = this.data.tab === 'knowledge' ? this.data.knowledgeList : this.data.promptList;
    this.setData({ editMode: true, editItem: { ...list[idx] }, isNew: false });
  },

  // ---- 删除 ----

  onDelete(e) {
    const idx = e.currentTarget.dataset.index;
    const id = e.currentTarget.dataset.id;
    const isKnowledge = this.data.tab === 'knowledge';
    const url = isKnowledge ? `/knowledge/${id}` : `/prompt/${id}`;

    wx.showModal({
      title: '确认删除',
      content: '删除后不可恢复',
      success: res => {
        if (res.confirm) {
          del(url).then(() => {
            wx.showToast({ title: '已删除', icon: 'success' });
            this.loadData();
          });
        }
      }
    });
  },

  // ---- 保存 ----

  onSave(e) {
    const formData = e.detail.value;
    const isKnowledge = this.data.tab === 'knowledge';
    const isNew = this.data.isNew;
    const id = this.data.editItem ? this.data.editItem.id : null;

    const body = isKnowledge ? {
      pomeloName: formData.pomeloName,
      productType: formData.productType || this.data.editItem.productType || 'pomelo',
      category: formData.category,
      origin: formData.origin,
      tasteDescription: formData.tasteDescription,
      productDescription: formData.productDescription || '',
      specification: formData.specification,
      priceRange: formData.priceRange,
    } : {
      promptName: formData.promptName,
      sceneCategory: formData.sceneCategory,
      promptTemplate: formData.promptTemplate,
      systemRoleDesc: formData.systemRoleDesc,
    };

    const apiCall = isNew
      ? post(isKnowledge ? '/knowledge' : '/prompt', body)
      : put(isKnowledge ? `/knowledge/${id}` : `/prompt/${id}`, body);

    apiCall
      .then(() => {
        wx.showToast({ title: '保存成功', icon: 'success' });
        this.setData({ editMode: false, editItem: null });
        this.loadData();
      })
      .catch(() => wx.showToast({ title: '保存失败', icon: 'none' }));
  },

  onCancelEdit() {
    this.setData({ editMode: false, editItem: null });
  },
});
