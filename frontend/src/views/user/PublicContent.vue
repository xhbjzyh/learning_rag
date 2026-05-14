<template>
  <div class="public-content">
    <h2 class="page-title">公共知识库</h2>

    <el-row :gutter="20">
      <!-- 左侧分类导航 -->
      <el-col :span="4">
        <el-card class="category-card" shadow="hover">
          <h3 class="category-title">知识分类</h3>
          <el-menu
            v-model="activeCategory"
            class="category-menu"
            @select="handleCategoryChange"
          >
            <el-menu-item
              v-for="category in categoryList"
              :key="category.id"
              :index="String(category.id)"
            >
              {{ category.category_name }}
            </el-menu-item>
          </el-menu>
        </el-card>
      </el-col>

      <!-- 右侧文档列表 -->
      <el-col :span="20">
        <el-card class="documents-card" shadow="hover">
          <div class="documents-header">
            <h3 class="documents-title">
              {{ currentCategory?.category_name || '全部文档' }}
            </h3>
            <span class="document-count">共 {{ documentList.length }} 个文档</span>
          </div>

          <!-- 加载状态 -->
          <div v-if="loading" class="loading-container">
            <el-icon class="loading-icon" size="40"><Loading /></el-icon>
            <p>正在加载文档...</p>
          </div>

          <!-- 空状态 -->
          <el-empty
            v-else-if="documentList.length === 0"
            description="该分类下暂无文档"
          />

          <!-- 文档列表 -->
          <el-row :gutter="20" v-else>
            <el-col :span="8" v-for="doc in documentList" :key="doc.id">
              <el-card class="document-card" shadow="hover">
                <div class="document-icon">
                  <el-icon :size="48" color="#409EFF"><Document /></el-icon>
                </div>
                <div class="document-info">
                  <h4 class="document-title" :title="doc.title">{{ doc.title }}</h4>
                  <p class="document-filename" :title="doc.file_name">
                    {{ doc.file_name }}
                  </p>
                  <p class="document-time">
                    上传时间：{{ formatDate(doc.create_time) }}
                  </p>
                </div>
                <div class="document-actions">
                  <el-button
                    type="primary"
                    size="small"
                    @click="handleViewDetail(doc)"
                  >
                    查看详情
                  </el-button>
                  <el-button
                    type="success"
                    size="small"
                    @click="handleDownload(doc)"
                  >
                    下载
                  </el-button>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <!-- 文档详情抽屉 -->
    <el-drawer
      v-model="detailDrawerVisible"
      title="文档详情"
      direction="rtl"
      size="50%"
      :before-close="handleCloseDrawer"
    >
      <div v-if="currentDocument" class="document-detail">
        <h3 class="detail-title">{{ currentDocument.title }}</h3>
        <div class="detail-meta">
          <span>文件名：{{ currentDocument.file_name }}</span>
          <span>上传时间：{{ formatDate(currentDocument.create_time) }}</span>
        </div>

        <div class="detail-section">
          <h4>文档描述</h4>
          <p>{{ currentDocument.description || '暂无描述' }}</p>
        </div>

        <div class="detail-section">
          <h4>包含知识点</h4>
          <div v-if="pointsLoading" class="points-loading">
            <el-icon class="loading-icon"><Loading /></el-icon>
            <span>正在加载知识点...</span>
          </div>
          <el-empty v-else-if="pointsList.length === 0" description="暂无知识点" />
          <div v-else class="points-list">
            <div
              v-for="(point, index) in pointsList"
              :key="index"
              class="point-item"
            >
              <div class="point-title">知识点 {{ index + 1 }}</div>
              <div class="point-content" v-html="formatContent(point.content)"></div>
            </div>
          </div>
        </div>

        <div class="detail-actions">
          <el-button type="success" @click="handleDownload(currentDocument)">
            下载文档
          </el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Loading } from '@element-plus/icons-vue'
import { formatDate } from '@/utils/format'
import contentPublicApi from '@/api/user/contentPublic'
import { getToken } from '@/utils/storage' // 你的项目之前用的是这个路径，直接复制
// 状态
const loading = ref(false)
const pointsLoading = ref(false)
const categoryList = ref([])
const documentList = ref([])
const activeCategory = ref('')
const currentCategory = ref(null)
const currentDocument = ref(null)
const detailDrawerVisible = ref(false)
const pointsList = ref([])

// 格式化内容
const formatContent = (content) => {
  if (!content) return ''
  return content
    .replace(/\n/g, '<br>')
    .replace(/### (.*?)(<br>|$)/g, '<h5 style="margin:8px 0;font-size:14px;color:#303133;">$1</h5>')
    .replace(/\*\*(.*?)\*\*/g, '<strong style="color:#303133;">$1</strong>')
    .replace(/- (.*?)(<br>|$)/g, '<li style="margin-left:20px;list-style-type:disc;">$1</li>')
}

// 获取分类列表
const getCategoryList = async () => {
  try {
    const res = await contentPublicApi.getCategoryList()
    categoryList.value = res.data

    // 默认选中第一个分类
    if (categoryList.value.length > 0) {
      activeCategory.value = String(categoryList.value[0].id)
      currentCategory.value = categoryList.value[0]
      await getDocumentList(categoryList.value[0].id)
    }
  } catch (error) {
    console.error('获取分类列表失败:', error)
    ElMessage.error('获取分类列表失败')
  }
}

// 获取文档列表
const getDocumentList = async (categoryId) => {
  loading.value = true
  documentList.value = []

  try {
    const res = await contentPublicApi.getDocumentList(categoryId)
    documentList.value = res.data
  } catch (error) {
    console.error('获取文档列表失败:', error)
    ElMessage.error('获取文档列表失败')
  } finally {
    loading.value = false
  }
}

// 分类切换
const handleCategoryChange = async (index) => {
  const categoryId = parseInt(index)
  currentCategory.value = categoryList.value.find(c => c.id === categoryId)
  await getDocumentList(categoryId)
}

// 查看详情
const handleViewDetail = async (doc) => {
  currentDocument.value = doc
  detailDrawerVisible.value = true
  pointsList.value = []

  // 加载知识点列表
  pointsLoading.value = true
  try {
    const res = await contentPublicApi.getDocumentPoints(doc.id)
    pointsList.value = res.data
  } catch (error) {
    console.error('获取知识点列表失败:', error)
    ElMessage.error('获取知识点列表失败')
  } finally {
    pointsLoading.value = false
  }
}

// 终极版：带导入+兼容localStorage，双保险获取Token
const handleDownload = async (row) => {
  try {
    console.log('=== 下载开始 ===')
    console.log('当前下载文档:', row)

    // 双保险获取Token（getToken()优先，localStorage兜底）
    let token = getToken() || localStorage.getItem('token')
    console.log('获取到的Token:', token)

    if (!token) {
      ElMessage.error('❌ 未登录，请重新登录！')
      return
    }

    // 强制清洗Token格式，解决所有JWT问题
    token = token.trim()
    if (!token.startsWith('Bearer ')) {
      token = `Bearer ${token}`
    }
    console.log('清洗后的Authorization头:', token)

    // 下载接口
    const downloadUrl = `/api/user/content/public/document/${row.id}/download`
    console.log('请求地址:', downloadUrl)

    // 发送请求
    const response = await fetch(downloadUrl, {
      method: 'GET',
      headers: {
        'Authorization': token
      }
    })

    console.log('响应状态码:', response.status)

    if (!response.ok) {
      throw new Error(`请求失败，状态码: ${response.status}`)
    }

    // 下载文件
    const blob = await response.blob()
    const objectUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = objectUrl
    link.download = row.file_name
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(objectUrl)

    ElMessage.success('✅ 下载成功！')
  } catch (error) {
    console.error('❌ 下载错误:', error)
    ElMessage.error('下载失败，请查看控制台日志')
  }
}

// 关闭抽屉
const handleCloseDrawer = () => {
  detailDrawerVisible.value = false
  currentDocument.value = null
  pointsList.value = []
}

onMounted(() => {
  getCategoryList()
})
</script>

<style scoped>
.page-title {
  margin-bottom: 20px;
  color: #333;
  font-size: 24px;
  font-weight: 600;
}

.category-card {
  height: calc(100vh - 180px);
  position: sticky;
  top: 20px;
}

.category-title {
  margin: 0 0 15px 0;
  font-size: 16px;
  color: #303133;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 10px;
}

.category-menu {
  border-right: none;
}

.documents-card {
  min-height: calc(100vh - 180px);
}

.documents-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}

.documents-title {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.document-count {
  font-size: 14px;
  color: #909399;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
  color: #909399;
}

.loading-icon {
  animation: rotating 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes rotating {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.document-card {
  margin-bottom: 20px;
  text-align: center;
  height: 280px;
  display: flex;
  flex-direction: column;
}

.document-icon {
  margin: 20px 0;
}

.document-info {
  flex: 1;
  padding: 0 15px;
}

.document-title {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.document-filename {
  margin: 0 0 8px 0;
  font-size: 12px;
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.document-time {
  margin: 0;
  font-size: 12px;
  color: #909399;
}

.document-actions {
  padding: 15px;
  border-top: 1px solid #f5f7fa;
  display: flex;
  justify-content: space-around;
}

.document-detail {
  padding: 20px;
}

.detail-title {
  margin: 0 0 20px 0;
  font-size: 22px;
  color: #303133;
}

.detail-meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
  color: #606266;
  font-size: 14px;
}

.detail-section {
  margin-bottom: 25px;
}

.detail-section h4 {
  margin: 0 0 15px 0;
  font-size: 16px;
  color: #303133;
}

.points-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 30px 0;
  color: #909399;
}

.points-loading .loading-icon {
  margin-right: 10px;
  margin-bottom: 0;
}

.points-list {
  max-height: 400px;
  overflow-y: auto;
}

.point-item {
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.point-title {
  margin-bottom: 10px;
  font-weight: 600;
  color: #303133;
}

.point-content {
  line-height: 1.6;
  color: #606266;
}

.detail-actions {
  text-align: right;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}
</style>