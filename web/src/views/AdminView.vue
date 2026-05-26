<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api/request'

const tab = ref('knowledge')
const knowledgeList = ref([])
const promptList = ref([])
const algoParams = ref([])
const editItem = ref(null)
const showModal = ref(false)

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
  editItem.value = tab.value === 'knowledge'
    ? { pomeloName: '', category: '', origin: '', tasteDescription: '', specification: '', priceRange: '' }
    : { promptName: '', sceneCategory: 'BUY', promptTemplate: '', systemRoleDesc: '' }
  showModal.value = true
}
function openEdit(item) { editItem.value = { ...item }; showModal.value = true }

async function save() {
  if (tab.value === 'knowledge') {
    if (editItem.value.id) await api.updateKnowledge(editItem.value.id, editItem.value)
    else await api.createKnowledge(editItem.value)
  } else {
    if (editItem.value.id) await api.updatePrompt(editItem.value.id, editItem.value)
    else await api.createPrompt(editItem.value)
  }
  showModal.value = false; await load()
}

async function del(id) {
  if (!confirm('确认删除？')) return
  tab.value === 'knowledge' ? await api.deleteKnowledge(id) : await api.deletePrompt(id)
  await load()
}

async function updateParam(id, value) {
  await api.updateAlgoParam(id, { paramValue: parseFloat(value) })
}
</script>

<template>
  <div class="admin">
    <h1 class="page-title">⚙️ 管理后台</h1>

    <!-- Tabs -->
    <div class="tabs">
      <button v-for="t in [{k:'knowledge',l:'📚 知识库'},{k:'prompt',l:'💬 Prompt库'},{k:'algo',l:'📊 算法参数'}]"
        :key="t.k" :class="['tab', { active: tab === t.k }]" @click="tab = t.k">{{ t.l }}</button>
    </div>

    <!-- 知识库 / Prompt -->
    <div v-if="tab !== 'algo'">
      <button class="btn btn-gold" style="margin-bottom:16px;" @click="openAdd">+ 新增</button>
      <div class="card list-item" v-for="item in (tab === 'knowledge' ? knowledgeList : promptList)" :key="item.id">
        <div style="flex:1;overflow:hidden;">
          <div style="font-weight:600;">{{ item.pomeloName || item.promptName }}</div>
          <div style="font-size:12px;color:#999;margin-top:4px;">
            {{ item.origin || '' }}{{ item.category ? ' · ' + item.category : '' }}
            {{ item.sceneCategory || '' }}{{ item.version ? ' v' + item.version : '' }}
          </div>
        </div>
        <div style="display:flex;gap:12px;">
          <button class="btn btn-outline" style="padding:6px 14px;font-size:12px;" @click="openEdit(item)">编辑</button>
          <button class="btn btn-red" style="padding:6px 14px;font-size:12px;" @click="del(item.id)">删除</button>
        </div>
      </div>
    </div>

    <!-- 算法参数 -->
    <div v-else>
      <div class="card list-item" v-for="p in algoParams" :key="p.id">
        <div style="flex:1;">
          <div style="font-weight:600;">{{ p.paramName }} <span class="tag">{{ p.paramGroup }}</span></div>
          <div style="font-size:12px;color:#999;">{{ p.description }}</div>
        </div>
        <input class="input" style="width:100px;text-align:center;" type="number" step="0.01"
               :value="p.paramValue" @change="updateParam(p.id, $event.target.value)" />
      </div>
    </div>

    <!-- Modal -->
    <div class="modal-mask" v-if="showModal" @click.self="showModal = false">
      <div class="modal">
        <h3 style="margin-bottom:16px;">{{ editItem.id ? '编辑' : '新增' }}</h3>
        <div v-if="tab === 'knowledge'">
          <input class="input" style="margin-bottom:10px;" v-model="editItem.pomeloName" placeholder="金柚品名" />
          <input class="input" style="margin-bottom:10px;" v-model="editItem.category" placeholder="品类" />
          <input class="input" style="margin-bottom:10px;" v-model="editItem.origin" placeholder="产地" />
          <input class="input" style="margin-bottom:10px;" v-model="editItem.priceRange" placeholder="价格区间" />
          <textarea class="textarea" v-model="editItem.tasteDescription" placeholder="口感描述" />
        </div>
        <div v-else>
          <input class="input" style="margin-bottom:10px;" v-model="editItem.promptName" placeholder="模板名称" />
          <input class="input" style="margin-bottom:10px;" v-model="editItem.sceneCategory" placeholder="场景: BUY/QA/GEN" />
          <textarea class="textarea" style="margin-bottom:10px;" v-model="editItem.promptTemplate" placeholder="Prompt模板" />
          <textarea class="textarea" v-model="editItem.systemRoleDesc" placeholder="System角色设定" />
        </div>
        <div style="display:flex;gap:12px;margin-top:16px;">
          <button class="btn btn-outline" style="flex:1;" @click="showModal = false">取消</button>
          <button class="btn btn-gold" style="flex:1;" @click="save">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tabs { display: flex; gap: 12px; margin-bottom: 20px; }
.tab { padding: 8px 20px; border-radius: 16px; border: 1px solid #ece4d0; background: #fff; cursor: pointer; font-size: 13px; }
.tab.active { background: #d4a843; color: #fff; border-color: #d4a843; }
.list-item { display: flex; align-items: center; gap: 16px; }
.modal-mask { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.4); z-index: 200; display: flex; align-items: center; justify-content: center; }
.modal { background: #fff; border-radius: 16px; padding: 28px; width: 90%; max-width: 500px; max-height: 80vh; overflow-y: auto; }
</style>
