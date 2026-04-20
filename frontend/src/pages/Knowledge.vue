<template>
  <div class="knowledge-page">
    <el-card>
      <template #header>
        <span>知识库管理</span>
      </template>

      <!-- 上传区域 -->
      <div class="upload-box">
        <el-upload
          ref="uploadRef"
          :action="uploadUrl"
          :headers="uploadHeaders"
          :show-file-list="false"
          :on-success="handleUploadSuccess"
          :on-error="handleUploadError"
          accept=".pdf,.txt,.docx"
        >
          <el-button type="primary">上传文档</el-button>
        </el-upload>
        <div style="margin-top: 10px; color: #909399">
          支持格式：PDF / TXT / DOCX
        </div>
      </div>

      <el-divider />

      <!-- 文档列表 -->
      <div class="list-box">
        <div class="list-item" v-for="item in docList" :key="item.id">
          <div class="doc-info">
            <div class="doc-title">{{ item.title }}</div>
            <div class="doc-desc">
              类型：{{ item.file_type }} | 状态：{{ getStatusText(item.audit_status) }}
            </div>
          </div>
        </div>
        <div v-if="docList.length === 0" class="empty-text">
          暂无文档，请上传
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'

const uploadRef = ref(null)
const docList = ref([])
const uploadUrl = 'http://127.0.0.1:8000/api/knowledge/upload'

// 请求头携带 token
const uploadHeaders = ref({})
const userStore = JSON.parse(localStorage.getItem('user'))
if (userStore?.token) {
  uploadHeaders.value.Authorization = `Bearer ${userStore.token}`
}

// 获取文档列表
const getDocList = async () => {
  try {
    const res = await request.get('/knowledge/list')
    docList.value = res.data
  } catch (err) {
    console.error(err)
  }
}

// 上传成功
const handleUploadSuccess = (res) => {
  ElMessage.success('上传成功，等待审核')
  getDocList()
}

// 上传失败
const handleUploadError = () => {
  ElMessage.error('上传失败')
}

// 状态转换
const getStatusText = (status) => {
  const map = { 0: '待审核', 1: '已通过', 2: '已驳回' }
  return map[status] || '未知'
}

onMounted(() => {
  getDocList()
})
</script>

<style scoped>
.knowledge-page {
  max-width: 1000px;
  margin: 0 auto;
}
.upload-box {
  padding: 10px;
}
.list-box {
  padding: 10px;
}
.list-item {
  padding: 15px;
  border-bottom: 1px solid #eee;
}
.doc-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 5px;
}
.doc-desc {
  font-size: 12px;
  color: #909399;
}
.empty-text {
  text-align: center;
  padding: 40px;
  color: #909399;
}
</style>