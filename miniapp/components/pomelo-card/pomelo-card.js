/**
 * 产品卡片组件
 *
 * 接收属性：
 *   item: {
 *     id, pomeloName, origin, priceRange, tasteDescription,
 *     hakkaCultureRelation, productDescription, imageUrl, giftSceneTags, tags,
 *     finalScore, ruleTotal, llmScore, reason,
 *     scorePriceMatch, scoreSceneFit, scoreHakkaFeature, scoreProductFeature,
 *     productType
 *   }
 */

Component({
  properties: {
    item: {
      type: Object,
      value: null,
      observer(newVal) {
        if (newVal) {
          this._formatItem(newVal);
        }
      }
    },
    /** 是否在对话气泡底部显示「查看详情」按钮 */
    showDetailBtn: {
      type: Boolean,
      value: false,
    }
  },

  data: {
    displayName: '',
    displayOrigin: '',
    displayPrice: '',
    displayScore: 0,
    displayReason: '',
    displayImage: '',
    displayTags: [],
    displayProductType: '',
    scoreStars: [0, 0, 0, 0, 0], // 5 星制
  },

  methods: {
    _formatItem(item) {
      const score = Number(item.finalScore || item.final_score) || 0;
      // 0-100 分 → 5 星制
      const starCount = Math.round(score / 20);
      const stars = [];
      for (let i = 0; i < 5; i++) {
        stars.push(i < starCount ? 1 : 0);
      }

      // 标签拆分（兼容 camelCase + snake_case）
      const tagStr = [item.giftSceneTags || item.gift_scene_tags, item.tags].filter(Boolean).join(',');
      const tags = tagStr ? tagStr.split(/[,，]/).map(t => t.trim()).filter(Boolean).slice(0, 4) : [];

      const productType = item.productType || item.product_type || 'pomelo';

      this.setData({
        displayName: item.pomeloName || item.pomelo_name || item.name || '精选水果',
        displayOrigin: item.origin || '',
        displayPrice: item.priceRange || item.price_range || '',
        displayScore: score,
        displayReason: item.reason || '',
        displayImage: item.imageUrl || item.image_url || '/images/default_pomelo.png',
        displayTags: tags,
        displayProductType: productType,
        scoreStars: stars,
      });
    },

    onTapCard() {
      const item = this.properties.item;
      if (item && item.id) {
        this.triggerEvent('tapcard', { id: item.id, name: item.pomeloName || item.name });
      }
    },

    onTapDetail() {
      const item = this.properties.item;
      if (item && item.id) {
        wx.navigateTo({
          url: '/pages/detail/detail?id=' + item.id,
        });
      }
    }
  }
});
