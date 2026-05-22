<template>
  <div class="rag-chat">
    <!-- 🔥 左侧：聊天区域 -->
    <div class="chat-section">
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

        <!-- 顶部工具栏 -->
        <div class="kb-switch">
          <div class="btn-group">
            <el-button type="primary" size="small" @click="privateDrawerVisible = true">
              <el-icon><Folder /></el-icon> 私有知识库
            </el-button>
            <el-button type="success" size="small" disabled>
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
    </div>

    <!-- 🔥 右侧：个性化推荐侧边栏（始终显示） -->
    <div class="recommendation-sidebar">
      <el-card shadow="hover" class="auto-recommend-card">
        <template #header>
          <div class="card-header">
            <span>💡 为你推荐</span>
            <el-tag size="small" type="success" v-if="recommendations.length > 0">
              实时更新
            </el-tag>
          </div>
        </template>

        <div v-loading="loadingRecommendations" class="recommendation-list">
          <div
            v-for="(rec, index) in recommendations"
            :key="rec.course_id"
            class="recommendation-item"
            @click="goToCourse(rec.course_id)"
          >
            <div class="item-rank">{{ index + 1 }}</div>
            <img :src="getFullImageUrl(rec.cover_url)" class="course-cover" />
            <div class="course-info">
              <h4>{{ rec.course_title }}</h4>
              <p class="reason" v-if="rec.reason">
                <el-icon><ChatDotRound /></el-icon>
                {{ rec.reason }}
              </p>
              <div class="meta">
                <el-tag size="small" :type="getScoreType(rec.score)">
                  匹配度 {{ rec.score }}%
                </el-tag>
                <el-tag size="small" type="info" v-if="rec.recommend_type">
                  {{ getRecommendTypeText(rec.recommend_type) }}
                </el-tag>
              </div>
            </div>
          </div>

          <el-empty
            v-if="!loadingRecommendations && recommendations.length === 0"
            description="完成一些学习后，我会为你推荐课程"
            :image-size="80"
          />
        </div>
      </el-card>

      <!-- 🔥 学习进度概览 -->
      <el-card shadow="hover" class="progress-card" v-if="learningStats">
        <template #header>
          <span>📊 本周学习</span>
        </template>
        <div class="stats-content">
          <div class="stat-item">
            <span class="label">学习时长</span>
            <span class="value">{{ formatDuration(learningStats.total_duration) }}</span>
          </div>
          <div class="stat-item">
            <span class="label">掌握知识点</span>
            <span class="value">{{ learningStats.mastered_points }} 个</span>
          </div>
          <div class="stat-item">
            <span class="label">连续学习</span>
            <span class="value">{{ learningStats.consecutive_days }} 天</span>
          </div>
        </div>
      </el-card>
    </div>

    <!-- ====================== 原有抽屉和弹窗（保持不变） ====================== -->
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
              <el-tag size="small" :type="getProcessStatusType(doc.process_status)">
                {{ getProcessStatusText(doc.process_status) }}
              </el-tag>
            </div>
            <div class="actions">
              <!-- 解析按钮 -->
              <el-button
                size="small"
                type="success"
                @click="parseDocument(doc)"
                :loading="doc.parsing"
                :disabled="doc.process_status === 1"
              >
                {{ doc.process_status === 1 ? '解析中...' : '解析' }}
              </el-button>

              <!-- 知识点查看按钮(仅解析完成后显示) -->
              <el-button
                size="small"
                type="primary"
                v-if="doc.process_status === 2"
                @click="viewPrivatePoints(doc)"
              >
                知识点
              </el-button>

              <!-- 公开申请按钮 -->
              <el-button
                size="small"
                type="warning"
                @click="applyPublic(doc)"
                :disabled="doc.is_public === 1 || doc.process_status !== 2"
              >
                {{ doc.is_public === 1 ? '已公开' : '申请公开' }}
              </el-button>

              <!-- 删除按钮 -->
              <el-button size="small" type="danger" @click="deletePrivateDoc(doc)">删除</el-button>
            </div>
          </div>
        </div>
      </div>
    </el-drawer>

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

    <el-drawer v-model="pointsDrawerVisible" title="文档知识点" direction="rtl" size="40%">
      <div v-if="currentDoc" class="points-detail">
        <h3>{{ currentDoc.title }}</h3>
        <div v-for="(p, i) in pointsList" :key="i" class="point-item">
          <div class="point-title">知识点 {{ i + 1 }}</div>
          <div class="point-content" v-html="formatContent(p.content)"></div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import ragApi from '@/api/user/rag'
import contentPrivateApi from '@/api/user/contentPrivate'
import contentPublicApi from '@/api/user/contentPublic'
import { ref, nextTick, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, Platform, Folder, Document, Plus, Loading, ChatDotRound } from '@element-plus/icons-vue'
import { formatDate } from '@/utils/format'
import axios from 'axios'
import { getToken } from '@/utils/storage'
import learningSessionTracker from '@/utils/learningSession'
import { useRoute, useRouter } from 'vue-router'
import { getSmartRecommendations, getUserBehaviorAnalysis } from '@/api/user/userProfile'

const route = useRoute()
const router = useRouter()

// -------------------------- 聊天基础 --------------------------
const messagesRef = ref(null)
const query = ref('')
const isStreaming = ref(false)
const streamingContent = ref('')
const kbType = ref('private')

const messages = ref([
  { role: 'assistant', content: '你好！我是RAG智能学习助手~', time: formatDate(new Date(), 'HH:mm:ss') }
])

// 🔥 新增：推荐相关
const recommendations = ref([])
const learningStats = ref(null)
const loadingRecommendations = ref(false)
const defaultCover = 'https://via.placeholder.com/80x60?text=课程'

// 🔥 新增：获取完整的图片URL
const getFullImageUrl = (url) => {
  if (!url) return defaultCover
  // 如果已经是完整URL，直接返回
  if (url.startsWith('http')) return url
  // 否则拼接基础URL
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  return `${baseUrl}${url}`
}

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

  // 🔥 如果有知识点ID，开始跟踪学习会话
  const pointId = route.query.point_id ? parseInt(route.query.point_id) : null
  if (pointId) {
    learningSessionTracker.startSession(pointId)
  }

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

    // 🔥 问答完成后结束学习会话
    if (pointId) {
      await learningSessionTracker.endSession({
        isMastered: false,
        sessionType: 'review',
        notes: q
      })
    }

    // 🔥 自动刷新推荐（异步，不阻塞）
    loadRecommendations()

  } catch (e) {
    ElMessage.error('请求失败')

    // 🔥 即使失败也要结束会话
    if (pointId) {
      learningSessionTracker.endSession()
    }
  } finally {
    isStreaming.value = false
    streamingContent.value = ''
  }
}

// 🔥 新增：加载推荐
const loadRecommendations = async () => {
  loadingRecommendations.value = true
  try {
    const res = await getSmartRecommendations(3)
    if (res.code === 0) {
      recommendations.value = res.data
    }

    // 同时加载学习统计
    const statsRes = await getUserBehaviorAnalysis()
    if (statsRes.code === 0) {
      learningStats.value = statsRes.data
    }
  } catch (error) {
    console.error('加载推荐失败:', error)
  } finally {
    loadingRecommendations.value = false
  }
}

// 🔥 新增：跳转到课程
const goToCourse = (courseId) => {
  router.push(`/user/course/${courseId}`)
}

// 🔥 新增：获取分数类型
const getScoreType = (score) => {
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'danger'
}

// 🔥 新增：获取推荐类型文本
const getRecommendTypeText = (type) => {
  const map = {
    weak_point: '薄弱加强',
    interest_based: '兴趣匹配',
    learning_path: '学习路径',
    hot: '热门课程'
  }
  return map[type] || '推荐'
}

// 🔥 新增：格式化时长
const formatDuration = (seconds) => {
  if (!seconds) return '0分钟'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0) return `${hours}小时${minutes}分钟`
  return `${minutes}分钟`
}

// -------------------------- 私有知识库（原有代码保持不变） --------------------------
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
  privateDocList.value = (res.data || []).map(doc => ({
    ...doc,
    parsing: false
  }))
  privateLoading.value = false
}

const loadCategoryList = async () => {
  categoryLoading.value = true
  const res = await contentPublicApi.getCategoryList()
  publicCategoryList.value = res.data || []
  categoryLoading.value = false
}

const parseDocument = async (doc) => {
  try {
    await ElMessageBox.confirm('确定要解析该文档吗？解析过程可能需要几分钟。', '提示', {
      confirmButtonText: '开始解析',
      cancelButtonText: '取消',
      type: 'info'
    })

    doc.parsing = true
    const res = await contentPrivateApi.parseDocument(doc.id)
    const result = res.data

    if (result.failed_chunks && result.failed_chunks.length > 0) {
      ElMessage.warning({
        message: `解析完成！成功 ${result.points_count} 个知识点，${result.failed_chunks.length} 个块失败。可点击「重试」重新解析失败部分。`,
        duration: 5000
      })
    } else {
      ElMessage.success(`文档解析成功！共提取 ${result.points_count} 个知识点`)
    }

    await loadPrivateDocs()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '解析失败，请重试')
    }
  } finally {
    doc.parsing = false
  }
}

const applyPublic = async (doc) => {
  try {
    const { value: remark } = await ElMessageBox.prompt(
      '请输入申请理由（可选）',
      '申请公开文档',
      {
        confirmButtonText: '提交申请',
        cancelButtonText: '取消',
        inputPlaceholder: '例如：该文档对其他人有帮助...',
        inputPattern: /.{0,200}/,
        inputErrorMessage: '最多200个字符'
      }
    )

    await contentPrivateApi.applyPublic(doc.id, remark || '')

    ElMessage.success('申请提交成功，请等待审核！')

    doc.is_public = 1
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '申请失败，请重试')
    }
  }
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

onMounted(() => {
  loadCategoryList()
  loadRecommendations()  // 🔥 新增：加载推荐
})

const getProcessStatusText = (status) => {
  const statusMap = {
    0: '待处理',
    1: '解析中',
    2: '已解析',
    3: '解析失败'
  }
  return statusMap[status] || '未知'
}

const getProcessStatusType = (status) => {
  const typeMap = {
    0: 'info',
    1: 'warning',
    2: 'success',
    3: 'danger'
  }
  return typeMap[status] || ''
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

  try {
    await axios.post('/api/user/content/private/document/upload', fd, {
      headers: { 'Content-Type': 'multipart/form-data', Authorization: `Bearer ${getToken()}` }
    })
    ElMessage.success('上传成功')
    showUploadDialog.value = false

    if (privateDrawerVisible.value) {
      await loadPrivateDocs()
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.msg || '上传失败')
  } finally {
    uploadLoading.value = false
  }
}

watch(privateDrawerVisible, (newVal) => {
  if (newVal) {
    loadPrivateDocs()
  }
})

</script>

<style scoped>
/* 🔥 修改：整体布局改为左右分栏 */
.rag-chat {
  width: 100%;
  height: 100%;
  display: flex;
  gap: 20px;
  padding: 20px;
  background: #f0f2f5;
}

.chat-section {
  flex: 1;
  min-width: 0;
}

.chat-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

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

/* 🔥 新增：推荐侧边栏样式 */
.recommendation-sidebar {
  width: 350px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.auto-recommend-card {
  flex-shrink: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.recommendation-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recommendation-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid #ebeef5;
}

.recommendation-item:hover {
  background: #f5f7fa;
  border-color: #409eff;
  transform: translateX(4px);
}

.item-rank {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #409eff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
  flex-shrink: 0;
}

.course-cover {
  width: 80px;
  height: 60px;
  object-fit: cover;
  border-radius: 4px;
  flex-shrink: 0;
}

.course-info h4 {
  margin: 0 0 8px;
  font-size: 14px;
  line-height: 1.4;
}

.reason {
  font-size: 12px;
  color: #666;
  margin: 0 0 8px;
  display: flex;
  align-items: flex-start;
  gap: 4px;
}

.reason .el-icon {
  margin-top: 2px;
  flex-shrink: 0;
}

.meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.stats-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-item .label {
  font-size: 13px;
  color: #666;
}

.stat-item .value {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

/* 原有抽屉样式保持不变 */
.knowledge-drawer-content { height:100%; display:flex; flex-direction:column; }
.drawer-header { display:flex; justify-content:space-between; margin-bottom:15px; padding-bottom:10px; border-bottom:1px solid #eee; }
.doc-list { flex:1; overflow-y:auto; }
.doc-item { display:flex; align-items:center; padding:12px; background:#f9f9f9; border-radius:8px; margin-bottom:8px; }
.doc-item .info { flex:1; margin-left:10px; }
.doc-item .title { font-weight:500; }
.doc-item .actions { display:flex; gap:6px; }
.loading-center { text-align:center; padding:40px; color:#999; }
.point-item { padding:12px; background:#f7f8fa; border-radius:8px; margin-bottom:10px; }
.point-title { font-weight:500; color:#409EFF; margin-bottom:6px; }
.detail-box { padding:20px; }
.detail-info { display:flex; justify-content:space-between; color:#666; margin-bottom:15px; }
</style>