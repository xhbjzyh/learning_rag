<template>
  <div class="private-knowledge">
    <div class="page-header">
      <h2 class="page-title">私有知识库</h2>
      <el-button type="primary" @click="showUploadDialog = true">
        <el-icon><Plus /></el-icon> 上传文档
      </el-button>
    </div>

    <!-- 上传弹窗 -->
    <el-dialog
    v-model="showUploadDialog"
    title="上传私有文档"
    width="500px"
    @open="loadCategoryList"
    @close="resetForm"
  >
    <el-form :model="uploadForm" label-width="80px">
      <el-form-item label="文档标题" required>
        <el-input v-model="uploadForm.title" placeholder="请输入文档标题" />
      </el-form-item>

      <!-- 新增：动态分类选择 -->
      <el-form-item label="文档分类">
        <el-select
          v-model="uploadForm.category_id"
          placeholder="请选择分类（可选，AI自动识别）"
          clearable
          :loading="categoryLoading"
          style="width: 100%;"
        >
          <el-option
            v-for="category in categoryList"
            :key="category.id"
            :label="category.category_name"
            :value="category.id"
            :title="category.description"
          />
        </el-select>
        <div style="font-size: 12px; color: #909399; margin-top: 5px;">
          不选择分类将由AI自动识别文档内容并分配
        </div>
      </el-form-item>

      <el-form-item label="选择文件" required>
        <el-upload
          v-model:file-list="fileList"
          :limit="1"
          accept=".pdf,.docx,.doc,.txt"
          :auto-upload="false"
          :on-exceed="handleExceed"
        >
          <el-button type="primary">选择文件</el-button>
          <template #tip>
            <div class="el-upload__tip">
              支持 PDF、Word、TXT 格式，单个文件不超过 50MB
            </div>
          </template>
        </el-upload>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="showUploadDialog = false">取消</el-button>
      <el-button
        type="primary"
        @click="submitUpload"
        :loading="uploadLoading"
        :disabled="!fileList.length || !uploadForm.title"
      >
        开始上传
      </el-button>
    </template>
  </el-dialog>

    <!-- 文档列表 -->
    <el-card class="documents-card" shadow="hover">
      <div class="documents-header">
        <h3 class="documents-title">我的私有文档</h3>
        <span class="document-count">共 {{ documentList.length }} 个文档</span>
      </div>

      <div v-if="loading" class="loading-container">
        <el-icon class="loading-icon" size="40"><Loading /></el-icon>
        <p>正在加载文档...</p>
      </div>

      <el-empty v-else-if="documentList.length === 0" description="暂无私有文档" />

      <el-row :gutter="20" v-else>
        <el-col :span="8" v-for="doc in documentList" :key="doc.id">
          <el-card class="document-card">
            <div class="document-status">
              <el-tag :type="getStatusTagType(doc)" size="small">{{ getStatusText(doc) }}</el-tag>
            </div>
            <div class="document-icon">
              <el-icon :size="48" color="#409EFF"><Document /></el-icon>
            </div>
            <div class="document-info">
              <h4 class="document-title" :title="doc.title">{{ doc.title }}</h4>
              <p class="document-filename" :title="doc.file_name">{{ doc.file_name }}</p>
              <p class="document-time">上传时间：{{ formatDate(doc.create_time) }}</p>
            </div>
            <div class="document-actions">
              <el-button v-if="!doc.is_parsed" type="warning" size="small" @click="handleParse(doc)">解析文档</el-button>
              <el-button v-if="doc.is_parsed" type="primary" size="small" @click="handleViewPoints(doc)">查看知识点</el-button>
              <el-button v-if="doc.audit_status === 0" type="success" size="small" @click="handleApplyPublic(doc)">申请公开</el-button>
              <el-button type="danger" size="small" @click="handleDelete(doc)">删除</el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <!-- 知识点抽屉 -->
    <el-drawer v-model="pointsDrawerVisible" title="文档知识点" direction="rtl" size="50%">
      <div v-if="currentDoc" class="points-detail">
        <h3 class="detail-title">{{ currentDoc.title }}</h3>
        <div class="points-list">
          <div v-for="(point, index) in pointsList" :key="index" class="point-item">
            <div class="point-title">知识点 {{ index + 1 }}</div>
            <div class="point-content" v-html="formatContent(point.content)"></div>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, UploadFilled, Loading, Document } from '@element-plus/icons-vue'
import { formatDate } from '@/utils/format'
import contentPrivateApi from '@/api/user/contentPrivate'
import axios from 'axios'
import { getToken } from '@/utils/storage'

// 状态
const loading = ref(false)
const showUploadDialog = ref(false)
const uploadLoading = ref(false)
const documentList = ref([])
const pointsDrawerVisible = ref(false)
const currentDoc = ref(null)
const pointsList = ref([])

// 新增：分类相关状态
const categoryList = ref([])
const categoryLoading = ref(false)

// 修改：uploadForm 添加 category_id
const uploadForm = ref({
  title: '',
  category_id: null
})
const fileList = ref([])

// 格式化
const formatContent = (content) => content?.replace(/\n/g, '<br>') || ''
const getStatusTagType = (doc) => doc.audit_status === 1 ? 'success' : doc.audit_status === 2 ? 'warning' : doc.audit_status === 3 ? 'danger' : 'info'
const getStatusText = (doc) => doc.audit_status === 1 ? '已公开' : doc.audit_status === 2 ? '审核中' : doc.audit_status === 3 ? '已拒绝' : '未解析'

// 获取列表
const getDocumentList = async () => {
  loading.value = true
  try {
    const res = await contentPrivateApi.getDocumentList()
    documentList.value = res.data || []
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

// 新增：加载分类列表
const loadCategoryList = async () => {
  categoryLoading.value = true
  try {
    const response = await axios.get('/api/user/content/public/content/public/category/list', {
      headers: {
        'Authorization': `Bearer ${getToken()}`
      }
    })

    if (response.data.code === 0) {
      categoryList.value = response.data.data || []
    } else {
      ElMessage.error(response.data.msg || '获取分类列表失败')
    }
  } catch (error) {
    console.error('获取分类列表失败:', error)
    ElMessage.error('获取分类列表失败，请稍后重试')
  } finally {
    categoryLoading.value = false
  }
}

// 新增：文件超出限制处理
const handleExceed = (files, fileList) => {
  ElMessage.warning('只能上传一个文件')
}

// 上传文件（修改版）
const submitUpload = async () => {
  if (!uploadForm.value.title) return ElMessage.warning('请输入标题')
  if (!fileList.value.length) return ElMessage.warning('请选择文件')

  uploadLoading.value = true
  const formData = new FormData()
  formData.append('title', uploadForm.value.title)
  formData.append('file', fileList.value[0].raw)

  // 新增：传递分类ID（如果用户选择了）
  if (uploadForm.value.category_id) {
    formData.append('category_id', uploadForm.value.category_id)
  }

  try {
    await axios.post('/api/user/content/private/content/private/document/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data', 'Authorization': `Bearer ${getToken()}` }
    })
    ElMessage.success('上传成功，正在后台解析文档...')
    showUploadDialog.value = false
    getDocumentList()
  } catch (err) {
    ElMessage.error('上传失败：' + (err.response?.data?.msg || '未知错误'))
  } finally {
    uploadLoading.value = false
  }
}

// 修改：重置表单（完整重置）
const resetForm = () => {
  uploadForm.value = {
    title: '',
    category_id: null
  }
  fileList.value = []
  uploadLoading.value = false
}

// 解析
const handleParse = async (doc) => {
  try {
    await contentPrivateApi.parseDocument(doc.id)
    ElMessage.success('解析中')
    setTimeout(getDocumentList, 2000)
  } catch (e) { ElMessage.error('解析失败') }
}

// 查看知识点
const handleViewPoints = async (doc) => {
  currentDoc.value = doc
  pointsDrawerVisible.value = true
  try {
    const res = await contentPrivateApi.getDocumentPoints(doc.id)
    pointsList.value = res.data || []
  } catch (e) { ElMessage.error('获取失败') }
}

// 申请公开
const handleApplyPublic = async (doc) => {
  await ElMessageBox.confirm('确定申请公开？')
  try {
    await contentPrivateApi.applyPublic(doc.id)
    ElMessage.success('申请成功')
    getDocumentList()
  } catch (e) { ElMessage.error('申请失败') }
}

// 删除
const handleDelete = async (doc) => {
  await ElMessageBox.confirm('确定删除？')
  try {
    await contentPrivateApi.deleteDocument(doc.id)
    ElMessage.success('删除成功')
    getDocumentList()
  } catch (e) { ElMessage.error('删除失败') }
}

onMounted(() => getDocumentList())
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-title { margin: 0; font-size: 24px; font-weight: 600; }
.upload-document { text-align: center; margin: 15px 0; }
.upload-icon { color: #c0c4cc; }
.documents-card { min-height: 60vh; }
.documents-header { display: flex; justify-content: space-between; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #eee; }
.document-card { height: 300px; position: relative; text-align: center; }
.document-status { position: absolute; top: 10px; right: 10px; }
.document-info { padding: 15px; }
.document-actions { border-top: 1px solid #eee; padding: 10px; }
.point-item { background: #f5f7fa; padding: 15px; margin-bottom: 10px; border-radius: 8px; }
</style>