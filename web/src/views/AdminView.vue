<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api/request'

const tab = ref('knowledge')
const knowledgeList = ref([])
const promptList = ref([])
const algoParams = ref([])
const editItem = ref(null)
const showModal = ref(false)
const toast = ref('')

function showToast(msg) { toast.value = msg; setTimeout(() => { toast.value = '' }, 2000) }

async function load() {
  try { knowledgeList.value = await api.getKnowledge() } catch {}
  try { promptList.value = await api.getPrompts() } catch {}
  try {
    const data = await api.getAlgoParams()
    if (Array.isArray(data)) algoParams.value = data
  } catch {}
}

onMounted(load)

function openAdd() {
  if (tab.value === 'knowledge') {
    editItem.value = {
      productType: 'pomelo', pomeloName: '', category: '', origin: '', specification: '',
      weightRange: '', priceRange: '', seasonInfo: '',
      tasteDescription: '', cultivationProcess: '',
      hakkaCultureRelation: '', productDescription: '', identificationTips: '',
      preservationMethod: '', ediblePairing: '', nutritionalValue: '',
      giftSceneTags: '', tags: '', imageUrl: '',
      scoreRequirementMatch: 5, scoreSceneFit: 5, scoreHakkaFeature: 5, scoreProductFeature: 5,
    }
  } else {
    editItem.value = {
      promptName: '', sceneCategory: 'BUY', promptTemplate: '',
      systemRoleDesc: '', temperature: 0.7, maxTokens: 1024,
    }
  }
  showModal.value = true
}

function openEdit(item) { editItem.value = { ...item }; showModal.value = true }

async function save() {
  try {
    if (tab.value === 'knowledge') {
      if (editItem.value.id) await api.updateKnowledge(editItem.value.id, editItem.value)
      else await api.createKnowledge(editItem.value)
    } else {
      if (editItem.value.id) await api.updatePrompt(editItem.value.id, editItem.value)
      else await api.createPrompt(editItem.value)
    }
    showModal.value = false; await load(); showToast('保存成功')
  } catch { showToast('保存失败') }
}

async function del(id) {
  if (!confirm('确认删除？')) return
  tab.value === 'knowledge' ? await api.deleteKnowledge(id) : await api.deletePrompt(id)
  await load(); showToast('已删除')
}

async function updateParam(id, value) {
  try { await api.updateAlgoParam(id, { paramValue: parseFloat(value) }); showToast('参数已更新') }
  catch { showToast('更新失败') }
}
</script>

<template>
  <div class="admin">
    <!-- Toast -->
    <transition name="fade">
      <div class="toast toast-success" v-if="toast">{{ toast }}</div>
    </transition>

    <h1 class="page-title">⚙️ 管理后台</h1>

    <!-- Tabs -->
    <div class="admin-tabs">
      <button v-for="t in [{k:'knowledge',l:'📚 知识库'},{k:'prompt',l:'📋 Prompt库'},{k:'algo',l:'📊 算法参数'}]"
        :key="t.k" :class="['admin-tab', { active: tab === t.k }]" @click="tab = t.k">{{ t.l }}</button>
    </div>

    <!-- 知识库 / Prompt -->
    <div v-if="tab !== 'algo'">
      <button class="btn btn-gold" style="margin-bottom:16px;width:100%;" @click="openAdd">+ 新增</button>
      <div class="card list-item" v-for="item in (tab === 'knowledge' ? knowledgeList : promptList)" :key="item.id">
        <div style="flex:1;overflow:hidden;">
          <div style="font-weight:600;">{{ item.pomeloName || item.promptName }}</div>
          <div style="font-size:12px;color:var(--text-placeholder);margin-top:4px;">
            {{ item.origin || '' }}{{ item.category ? ' · ' + item.category : '' }}
            {{ item.sceneCategory || '' }}{{ item.version ? ' v' + item.version : '' }}
          </div>
        </div>
        <div style="display:flex;gap:8px;">
          <button class="btn btn-outline btn-sm" @click="openEdit(item)">编辑</button>
          <button class="btn btn-red btn-sm" @click="del(item.id)">删除</button>
        </div>
      </div>
    </div>

    <!-- 算法参数 -->
    <div v-else>
      <div class="card list-item" v-for="p in algoParams" :key="p.id">
        <div style="flex:1;">
          <div style="font-weight:600;">{{ p.paramName }}
            <span class="tag tag-gold" style="margin-left:8px;">{{ p.paramGroup }}</span>
          </div>
          <div style="font-size:12px;color:var(--text-placeholder);margin-top:4px;">{{ p.description }}</div>
        </div>
        <input class="input" style="width:110px;text-align:center;" type="number" step="0.01"
               :value="p.paramValue" @change="updateParam(p.id, .target.value)" />
      </div>
    </div>

    <!-- Modal -->
    <transition name="fade">
      <div class="modal-mask" v-if="showModal" @click.self="showModal = false">
        <div class="modal">
          <h3 style="margin-bottom:20px;">{{ editItem?.id ? '编辑' : '新增' }}</h3>

          <!-- 知识库表单 -->
          <div v-if="tab === 'knowledge'" class="modal-form">
            <div class="form-row">
              <div class="form-col"><label>产品类型*</label>
                <select class="input" v-model="editItem.productType">
                  <option value="pomelo">金柚</option>
                  <option value="apple">苹果</option>
                  <option value="banana">香蕉</option>
                  <option value="watermelon">西瓜</option>
                  <option value="orange">橙子</option>
                  <option value="grape">葡萄</option>
                </select>
              </div>
              <div class="form-col"><label>品名*</label><input class="input" v-model="editItem.pomeloName" /></div>
            </div>
            <div class="form-row">
              <div class="form-col"><label>品类</label>
                <select class="input" v-model="editItem.category">
                  <option value="">选择品类</option>
                  <template v-if="editItem.productType === 'pomelo'">
                    <option value="沙田柚">沙田柚</option>
                    <option value="蜜柚">蜜柚</option>
                    <option value="文旦柚">文旦柚</option>
                    <option value="金柚深加工品">金柚深加工品</option>
                  </template>
                  <template v-else>
                    <option value="优选">优选</option>
                    <option value="精品">精品</option>
                    <option value="有机">有机</option>
                    <option value="其他">其他</option>
                  </template>
                </select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-col"><label>产地</label><input class="input" v-model="editItem.origin" /></div>
              <div class="form-col"><label>规格</label><input class="input" v-model="editItem.specification" /></div>
            </div>
            <div class="form-row">
              <div class="form-col"><label>单果重量</label><input class="input" v-model="editItem.weightRange" placeholder="如：1.2-1.8kg" /></div>
              <div class="form-col"><label>价格区间</label><input class="input" v-model="editItem.priceRange" placeholder="如：88-128元/箱" /></div>
            </div>
            <div class="form-row">
              <div class="form-col"><label>上市季节</label><input class="input" v-model="editItem.seasonInfo" placeholder="如：11月至次年3月" /></div>
              <div class="form-col"><label>图片URL</label><input class="input" v-model="editItem.imageUrl" placeholder="https://..." /></div>
            </div>
            <label>口感描述</label>
            <textarea class="textarea" v-model="editItem.tasteDescription" placeholder="如：清甜化渣、蜜香浓郁" rows="2" />
            <label>种植工艺</label>
            <textarea class="textarea" v-model="editItem.cultivationProcess" placeholder="有机种植、客家传统农法" rows="2" />
            <label>客家文化关联（仅金柚）</label>
            <textarea class="textarea" v-model="editItem.hakkaCultureRelation" placeholder="如：金柚与客家民俗、节庆、待客礼仪的关联" rows="2" />
            <label>产品特色描述（非金柚使用）</label>
            <textarea class="textarea" v-model="editItem.productDescription" placeholder="产品通用描述/特色说明" rows="2" />
            <label>辨别技巧</label>
            <textarea class="textarea" v-model="editItem.identificationTips" rows="2" />
            <label>保存方法</label>
            <textarea class="textarea" v-model="editItem.preservationMethod" rows="2" />
            <label>食用搭配</label>
            <textarea class="textarea" v-model="editItem.ediblePairing" rows="2" />
            <label>营养价值</label>
            <textarea class="textarea" v-model="editItem.nutritionalValue" rows="2" />
            <label>送礼场景标签（逗号分隔）</label>
            <input class="input" v-model="editItem.giftSceneTags" placeholder="中秋送礼,春节年货" />
            <label>通用标签</label>
            <input class="input" v-model="editItem.tags" placeholder="金奖,送礼首选" />
            <div class="form-row" style="margin-top:12px;">
              <div class="form-col"><label>需求匹配分</label><input class="input" type="number" step="0.1" min="0" max="10" v-model="editItem.scoreRequirementMatch" /></div>
              <div class="form-col"><label>场景适配分</label><input class="input" type="number" step="0.1" min="0" max="10" v-model="editItem.scoreSceneFit" /></div>
              <div class="form-col"><label>客家特色分</label><input class="input" type="number" step="0.1" min="0" max="10" v-model="editItem.scoreHakkaFeature" /></div>
              <div class="form-col"><label>产品特色分</label><input class="input" type="number" step="0.1" min="0" max="10" v-model="editItem.scoreProductFeature" /></div>
            </div>
          </div>

          <!-- Prompt 表单 -->
          <div v-else class="modal-form">
            <label>模板名称</label><input class="input" v-model="editItem.promptName" />
            <label>场景分类</label>
            <select class="input" v-model="editItem.sceneCategory">
              <option value="BUY">BUY - 选购推荐</option>
              <option value="QA">QA - 知识问答</option>
              <option value="GEN">GEN - 内容生成</option>
            </select>
            <label>System 角色设定</label>
            <textarea class="textarea" v-model="editItem.systemRoleDesc" rows="3" />
            <label>Prompt 模板</label>
            <textarea class="textarea" v-model="editItem.promptTemplate" rows="5" />
            <div class="form-row">
              <div class="form-col"><label>温度</label><input class="input" type="number" step="0.05" min="0" max="2" v-model="editItem.temperature" /></div>
              <div class="form-col"><label>最大Token</label><input class="input" type="number" v-model="editItem.maxTokens" /></div>
            </div>
          </div>

          <div class="modal-actions">
            <button class="btn btn-outline" style="flex:1;" @click="showModal = false">取消</button>
            <button class="btn btn-gold" style="flex:1;" @click="save">保存</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.admin { padding-bottom: 40px; }

/* === Tabs === */
.admin-tabs { display: flex; gap: 8px; margin-bottom: 20px; }
.admin-tab {
  flex: 1; padding: 10px 16px; border-radius: var(--radius-full);
  border: 1.5px solid var(--border); background: var(--bg-card);
  cursor: pointer; font-size: 14px; font-weight: 600; text-align: center;
  color: var(--text-secondary); transition: all .2s;
}
.admin-tab.active { background: var(--primary); color: #fff; border-color: var(--primary); }

/* === 列表 === */
.list-item { display: flex; align-items: center; gap: 16px; margin-bottom: 10px; }

/* === Modal === */
.modal-mask {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(44,36,22,0.4); backdrop-filter: blur(4px);
  z-index: 200; display: flex; align-items: center; justify-content: center;
  padding: 20px;
}
.modal {
  background: var(--bg-card); border-radius: var(--radius-lg);
  padding: 28px; width: 100%; max-width: 620px;
  max-height: 85vh; overflow-y: auto;
  box-shadow: var(--shadow-xl);
}
.modal-form { display: flex; flex-direction: column; gap: 4px; }
.modal-form label { font-size: 12px; font-weight: 600; color: var(--text-secondary); margin-top: 10px; margin-bottom: 4px; }
.form-row { display: flex; gap: 10px; }
.form-col { flex: 1; }
.form-col label { font-size: 12px; font-weight: 600; color: var(--text-secondary); margin-bottom: 4px; display: block; }
.modal-actions { display: flex; gap: 12px; margin-top: 20px; }

/* === Toast === */
.toast {
  position: fixed; top: 20px; left: 50%; transform: translateX(-50%);
  padding: 10px 24px; border-radius: var(--radius-full);
  font-size: 14px; font-weight: 600; z-index: 500;
  box-shadow: var(--shadow-md);
  background: #4caf50; color: #fff;
}

.fade-enter-active, .fade-leave-active { transition: opacity .3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
