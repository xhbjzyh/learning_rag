<template>
  <div class="rag-chat">
    <div class="chat-container">
      <!-- 聊天消息区 -->
      <div class="chat-messages" ref="messagesRef">
        <el-empty v-if="messages.length === 0" description="开始你的RAG问答之旅吧！" />

        <div
          v-for="(msg, index) in messages"
          :key="index"
          class="message-item"
          :class="msg.role"
        >
          <div class="message-avatar">
            <el-icon v-if="msg.role === 'user'" :size="24"><User /></el-icon>
            <el-icon v-else :size="24" color="#409EFF"><Platform /></el-icon>
          </div>
          <div class="message-content">
            <div class="message-bubble" v-html="msg.content"></div>
            <div class="message-time">{{ msg.time }}</div>
          </div>
        </div>

        <div v-if="isStreaming" class="message-item assistant">
          <div class="message-avatar">
            <el-icon :size="24" color="#409EFF"><Platform /></el-icon>
          </div>
          <div class="message-content">
            <div class="message-bubble">
              {{ streamingContent }}
              <span class="cursor">|</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 顶部工具栏：私有 + 公共知识库按钮 -->
      <div class="kb-switch">
        <div class="btn-group">
          <el-button type="primary" size="small" @click="privateDrawerVisible = true">
            <el-icon><Folder /></el-icon> 私有知识库
          </el-button>
          <el-button type="success" size="small" @click="publicDrawerVisible = true">
            <el-icon><Document /></el-icon> 公共知识库
          </el-button>
        </div>

        <el-radio-group v-model="kbType" size="small">
          <el-radio label="private">私有知识库</el-radio>
          <el-radio label="public">公共知识库</el-radio>
        </el-radio-group>

        <el-button type="text" @click="handleClearHistory" :disabled="isStreaming">
          清除历史
        </el-button>
      </div>

      <!-- 输入区 -->
      <div class="chat-input">
        <el-input
          v-model="query"
          type="textarea"
          :rows="3"
          placeholder="请输入你的问题..."
          :disabled="isStreaming"
          @keyup.ctrl.enter="handleSend"
        />
        <div class="input-actions">
          <span class="input-tip">按 Ctrl+Enter 发送</span>
          <el-button
            type="primary"
            :loading="isStreaming"
            @click="handleSend"
          >
            {{ isStreaming ? '回答中...' : '发送' }}
          </el-button>
        </div>
      </div>
    </div>

    <!-- ====================== 1. 私有知识库抽屉 ====================== -->
    <el-drawer v-model="privateDrawerVisible" title="私有知识库" direction="rtl" size="45%" :destroy-on-close="true">
      <div class="knowledge-drawer-content">
        <div class="drawer-header">
          <el-button type="primary" size="small" @click="showUploadDialog = true">
            <el-icon><Plus /></el-icon> 上传文档
          </el-button>
          <span>共 {{ privateDocList.length }} 个文档</span>
        </div>

        <div v-if="privateLoading" class="loading-center">
          <el-icon><Loading /></el-icon> 加载中...
        </div>
        <el-empty v-else-if="privateDocList.length === 0" description="暂无文档" />

        <div v-else class="doc-list">
          <div v-for="doc in privateDocList" :key="doc.id" class="doc-item">
            <el-icon><Document /></el-icon>
            <div class="info">
              <div class="title">{{ doc.title }}</div>
              <el-tag size="small" :type="doc.is_parsed ? 'success' : 'warning'">
                {{ doc.is_parsed ? '已解析' : '未解析' }}
              </el-tag>
            </div>
            <div class="actions">
              <el-button size="small" type="primary" v-if="doc.is_parsed" @click="viewPrivatePoints(doc)">知识点</el-button>
              <el-button size="small" type="danger" @click="deletePrivateDoc(doc)">删除</el-button>
            </div>
          </div>
        </div>
      </div>
    </el-drawer>

    <!-- ====================== 2. 公共知识库抽屉 ====================== -->
    <el-drawer v-model="publicDrawerVisible" title="公共知识库" direction="rtl" size="50%" :destroy-on-close="true">
      <div class="public-drawer-content">
        <el-row :gutter="10">
          <el-col :span="6">
            <div class="category-box">
              <h4>知识分类</h4>
              <el-menu v-model="activeCategory" @select="changePublicCategory" :router="false">
                <el-menu-item v-for="c in publicCategoryList" :key="c.id" :index="String(c.id)">
                  {{ c.category_name }}
                </el-menu-item>
              </el-menu>
            </div>
          </el-col>

          <el-col :span="18">
            <div v-if="publicLoading" class="loading-center">
              <el-icon><Loading /></el-icon> 加载中...
            </div>
            <el-empty v-else-if="publicDocList.length === 0" description="该分类暂无文档" />

            <div v-else class="public-doc-grid">
              <el-card v-for="doc in publicDocList" :key="doc.id" shadow="hover" class="public-card">
                <div class="card-icon">
                  <el-icon size="30" color="#409EFF"><Document /></el-icon>
                </div>
                <div class="card-info">
                  <div class="card-title">{{ doc.title }}</div>
                  <div class="card-time">{{ formatDate(doc.create_time) }}</div>
                </div>
                <div class="card-actions">
                  <el-button size="small" type="primary" @click="viewPublicDetail(doc)">查看</el-button>
                  <el-button size="small" type="success" @click="downloadPublicDoc(doc)">下载</el-button>
                </div>
              </el-card>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-drawer>

    <!-- 上传弹窗（私有） -->
    <el-dialog v-model="showUploadDialog" title="上传私有文档" width="500px" @open="loadCategoryList" @close="resetUploadForm">
      <el-form :model="uploadForm" label-width="80px">
        <el-form-item label="文档标题" required>
          <el-input v-model="uploadForm.title" placeholder="请输入标题" />
        </el-form-item>
        <el-form-item label="文档分类">
          <el-select v-model="uploadForm.category_id" placeholder="可选" clearable :loading="categoryLoading">
            <el-option v-for="c in publicCategoryList" :key="c.id" :label="c.category_name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="选择文件" required>
          <el-upload v-model:file-list="fileList" :limit="1" accept=".pdf,.docx,.doc,.txt" :auto-upload="false">
            <el-button type="primary">选择文件</el-button>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="submitUpload" :loading="uploadLoading">开始上传</el-button>
      </template>
    </el-dialog>

    <!-- 知识点查看抽屉 -->
    <el-drawer v-model="pointsDrawerVisible" title="文档知识点" direction="rtl" size="40%">
      <div v-if="currentDoc" class="points-detail">
        <h3>{{ currentDoc.title }}</h3>
        <div v-for="(p, i) in pointsList" :key="i" class="point-item">
          <div class="point-title">知识点 {{ i + 1 }}</div>
          <div class="point-content" v-html="formatContent(p.content)"></div>
        </div>
      </div>
    </el-drawer>

    <!-- 公共文档详情 -->
    <el-drawer v-model="publicDetailVisible" title="文档详情" direction="rtl" size="45%">
      <div v-if="currentPublicDoc" class="detail-box">
        <h3>{{ currentPublicDoc.title }}</h3>
        <div class="detail-info">
          <span>文件名：{{ currentPublicDoc.file_name }}</span>
          <span>上传：{{ formatDate(currentPublicDoc.create_time) }}</span>
        </div>
        <div class="detail-points">
          <h4>知识点</h4>
          <div v-for="(p, i) in publicPoints" :key="i" class="point-item">
            <div class="point-content" v-html="formatContent(p.content)"></div>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import ragApi from '@/api/user/rag'
import contentPrivateApi from '@/api/user/contentPrivate'
import contentPublicApi from '@/api/user/contentPublic'
import { ref, nextTick, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, Platform, Folder, Document, Plus, Loading } from '@element-plus/icons-vue'
import { formatDate } from '@/utils/format'
import axios from 'axios'
import { getToken } from '@/utils/storage'

// -------------------------- 聊天基础 --------------------------
const messagesRef = ref(null)
const query = ref('')
const isStreaming = ref(false)
const streamingContent = ref('')
const kbType = ref('private')

const messages = ref([
  { role: 'assistant', content: '你好！我是RAG智能学习助手~', time: formatDate(new Date(), 'HH:mm:ss') }
])

const scrollToBottom = () => nextTick(() => {
  if (messagesRef.value) messagesRef.value.scrollTop = messagesRef.value.scrollHeight
})

const handleClearHistory = async () => {
  await ElMessageBox.confirm('确定清空历史？')
  await ragApi.clearHistory()
  messages.value = [{ role: 'assistant', content: '你好！我是RAG智能学习助手~', time: formatDate(new Date(), 'HH:mm:ss') }]
  ElMessage.success('已清空')
}

const handleSend = async () => {
  if (!query.value) return ElMessage.warning('请输入问题')
  const userMsg = { role: 'user', content: query.value, time: formatDate(new Date(), 'HH:mm:ss') }
  messages.value.push(userMsg)
  const q = query.value
  query.value = ''
  isStreaming.value = true
  streamingContent.value = ''
  scrollToBottom()

  try {
    const token = localStorage.getItem('rag_token')
    const res = await fetch(`/api/user/rag/answer/stream?query=${encodeURIComponent(q)}&kb_type=${kbType.value}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      streamingContent.value += decoder.decode(value)
      scrollToBottom()
    }
    messages.value.push({
      role: 'assistant',
      content: streamingContent.value.replace(/\n/g, '<br>'),
      time: formatDate(new Date(), 'HH:mm:ss')
    })
  } catch (e) {
    ElMessage.error('请求失败')
  } finally {
    isStreaming.value = false
    streamingContent.value = ''
  }
}

// -------------------------- 私有知识库 --------------------------
const privateDrawerVisible = ref(false)
const privateLoading = ref(false)
const privateDocList = ref([])
const showUploadDialog = ref(false)
const uploadLoading = ref(false)
const publicCategoryList = ref([])
const categoryLoading = ref(false)
const uploadForm = ref({ title: '', category_id: null })
const fileList = ref([])
const pointsDrawerVisible = ref(false)
const currentDoc = ref(null)
const pointsList = ref([])

const loadPrivateDocs = async () => {
  privateLoading.value = true
  const res = await contentPrivateApi.getDocumentList()
  privateDocList.value = res.data || []
  privateLoading.value = false
}

const loadCategoryList = async () => {
  categoryLoading.value = true
  const res = await contentPublicApi.getCategoryList()
  publicCategoryList.value = res.data || []
  categoryLoading.value = false
}

const resetUploadForm = () => {
  uploadForm.value = { title: '', category_id: null }
  fileList.value = []
}

const submitUpload = async () => {
  const fd = new FormData()
  fd.append('title', uploadForm.value.title)
  fd.append('file', fileList.value[0].raw)
  if (uploadForm.value.category_id) fd.append('category_id', uploadForm.value.category_id)
  uploadLoading.value = true
  await axios.post('/api/user/content/private/content/private/document/upload', fd, {
    headers: { 'Content-Type': 'multipart/form-data', Authorization: `Bearer ${getToken()}` }
  })
  ElMessage.success('上传成功')
  showUploadDialog.value = false
  loadPrivateDocs()
  uploadLoading.value = false
}

const viewPrivatePoints = async (doc) => {
  currentDoc.value = doc
  pointsDrawerVisible.value = true
  const res = await contentPrivateApi.getDocumentPoints(doc.id)
  pointsList.value = res.data || []
}

const deletePrivateDoc = async (doc) => {
  await ElMessageBox.confirm('确定删除？')
  await contentPrivateApi.deleteDocument(doc.id)
  ElMessage.success('删除成功')
  loadPrivateDocs()
}

const formatContent = (c) => c?.replace(/\n/g, '<br>') || ''

// -------------------------- 公共知识库 --------------------------
const publicDrawerVisible = ref(false)
const publicLoading = ref(false)
const publicDocList = ref([])
const activeCategory = ref('')
const currentPublicCategory = ref(null)
const publicDetailVisible = ref(false)
const currentPublicDoc = ref(null)
const publicPoints = ref([])

const loadPublicCategories = async () => {
  const res = await contentPublicApi.getCategoryList()
  publicCategoryList.value = res.data || []
  if (publicCategoryList.value.length) {
    activeCategory.value = String(publicCategoryList.value[0].id)
    currentPublicCategory.value = publicCategoryList.value[0]
    loadPublicDocs(publicCategoryList.value[0].id)
  }
}

const loadPublicDocs = async (cid) => {
  publicLoading.value = true
  const res = await contentPublicApi.getDocumentList(cid)
  publicDocList.value = res.data || []
  publicLoading.value = false
}

const changePublicCategory = async (idx) => {
  const cid = parseInt(idx)
  currentPublicCategory.value = publicCategoryList.value.find(c => c.id === cid)
  loadPublicDocs(cid)
}

const viewPublicDetail = async (doc) => {
  currentPublicDoc.value = doc
  publicDetailVisible.value = true
  const res = await contentPublicApi.getDocumentPoints(doc.id)
  publicPoints.value = res.data || []
}

const downloadPublicDoc = async (doc) => {
  const token = getToken() || localStorage.getItem('token')
  const res = await fetch(`/api/user/content/public/content/public/document/${doc.id}/download`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  const blob = await res.blob()
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = doc.file_name
  a.click()
  URL.revokeObjectURL(a.href)
  ElMessage.success('开始下载')
}

// 打开对应抽屉时自动加载
privateDrawerVisible.value && loadPrivateDocs()
publicDrawerVisible.value && loadPublicCategories()

onMounted(() => {})
</script>

<style scoped>
.rag-chat { width: 100%; height: 100%; display: flex; justify-content: center; background: #f0f2f5; }
.chat-container { width: 100%; max-width: 900px; height: 100%; display: flex; flex-direction: column; background: #fff; }
.chat-messages { flex: 1; padding: 20px; overflow-y: auto; }
.message-item { display: flex; margin-bottom: 15px; }
.message-item.user { flex-direction: row-reverse; }
.message-avatar { width: 36px; height: 36px; border-radius: 50%; background: #f5f7fa; display: flex; align-items: center; justify-content: center; margin: 0 10px; }
.message-bubble { padding: 10px 14px; border-radius: 8px; max-width: 70%; background: #f5f7fa; line-height: 1.6; }
.message-item.user .message-bubble { background: #409EFF; color: #fff; }
.cursor { animation: blink 1s infinite; }
@keyframes blink { 0%,50%{opacity:1;}51%,100%{opacity:0;} }
.kb-switch { padding: 10px 20px; border-top:1px solid #eee; display:flex; justify-content:space-between; align-items:center; }
.btn-group { display:flex; gap:8px; }
.chat-input { padding:20px; border-top:1px solid #eee; }
.input-actions { display:flex; justify-content:space-between; margin-top:10px; }

/* 抽屉样式 */
.knowledge-drawer-content, .public-drawer-content { height:100%; display:flex; flex-direction:column; }
.drawer-header { display:flex; justify-content:space-between; margin-bottom:15px; padding-bottom:10px; border-bottom:1px solid #eee; }
.doc-list { flex:1; overflow-y:auto; }
.doc-item { display:flex; align-items:center; padding:12px; background:#f9f9f9; border-radius:8px; margin-bottom:8px; }
.doc-item .info { flex:1; margin-left:10px; }
.doc-item .title { font-weight:500; }
.doc-item .actions { display:flex; gap:6px; }
.public-doc-grid { display:grid; grid-template-columns: repeat(2,1fr); gap:10px; }
.public-card { padding:12px; text-align:center; }
.card-icon { margin-bottom:8px; }
.card-title { font-weight:500; margin-bottom:4px; }
.card-time { font-size:12px; color:#999; margin-bottom:8px; }
.loading-center { text-align:center; padding:40px; color:#999; }
.point-item { padding:12px; background:#f7f8fa; border-radius:8px; margin-bottom:10px; }
.point-title { font-weight:500; color:#409EFF; margin-bottom:6px; }
.detail-box { padding:20px; }
.detail-info { display:flex; justify-content:space-between; color:#666; margin-bottom:15px; }
</style>