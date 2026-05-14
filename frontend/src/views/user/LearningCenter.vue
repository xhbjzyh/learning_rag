<template>
  <div class="learning-center">
    <!-- 🔥 新增：顶部行为分析面板 -->
    <el-row :gutter="20" class="analysis-panel">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #e3f2fd;">
              <el-icon :size="32" color="#2196f3"><Clock /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">本周学习时长</div>
              <div class="stat-value">{{ formatDuration(behaviorStats?.total_duration || 0) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #e8f5e9;">
              <el-icon :size="32" color="#4caf50"><Check /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">掌握知识点</div>
              <div class="stat-value">{{ behaviorStats?.mastered_points || 0 }} 个</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #fff3e0;">
              <el-icon :size="32" color="#ff9800"><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">连续学习</div>
              <div class="stat-value">{{ behaviorStats?.consecutive_days || 0 }} 天</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #fce4ec;">
              <el-icon :size="32" color="#e91e63"><Medal /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">当前等级</div>
              <div class="stat-value">{{ prediction?.current_level || '入门' }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 🔥 新增：详细分析区域 -->
    <el-row :gutter="20" class="detailed-analysis">
      <!-- 左侧：薄弱标签分析 -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>🎯 薄弱知识点标签</span>
              <el-tag size="small" type="warning">需要加强</el-tag>
            </div>
          </template>
          <div v-loading="loadingWeakTags">
            <div v-if="weakTags.length === 0" class="empty-tip">
              <el-empty description="暂无薄弱标签，继续保持！" :image-size="80" />
            </div>
            <div v-else class="tag-list">
              <div
                v-for="(tag, index) in weakTags"
                :key="tag.tag_id"
                class="weak-tag-item"
              >
                <div class="tag-rank">{{ index + 1 }}</div>
                <div class="tag-info">
                  <div class="tag-name">{{ tag.tag_name }}</div>
                  <div class="tag-category">{{ tag.category }}</div>
                </div>
                <div class="tag-score">
                  <el-progress
                    :percentage="tag.avg_mastery"
                    :color="getMasteryColor(tag.avg_mastery)"
                    :stroke-width="8"
                  />
                  <div class="score-text">{{ tag.avg_mastery }}分</div>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：学习预测 -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>📈 学习效果预测</span>
              <el-tag size="small" type="success">AI预测</el-tag>
            </div>
          </template>
          <div v-loading="loadingPrediction">
            <div v-if="!prediction" class="empty-tip">
              <el-empty description="暂无预测数据" :image-size="80" />
            </div>
            <div v-else class="prediction-content">
              <div class="prediction-levels">
                <div class="level-item current">
                  <div class="level-label">当前等级</div>
                  <div class="level-name">{{ prediction.current_level }}</div>
                  <div class="level-score">平均 {{ prediction.current_avg_mastery }}分</div>
                </div>
                <div class="level-arrow">
                  <el-icon :size="32" color="#409eff"><Right /></el-icon>
                </div>
                <div class="level-item predicted">
                  <div class="level-label">预计达到</div>
                  <div class="level-name">{{ prediction.predicted_level }}</div>
                  <div class="level-time">还需 {{ prediction.estimated_days }} 天</div>
                </div>
              </div>

              <div class="confidence-bar">
                <div class="confidence-label">
                  <span>置信度</span>
                  <span>{{ (prediction.confidence * 100).toFixed(0) }}%</span>
                </div>
                <el-progress
                  :percentage="prediction.confidence * 100"
                  :color="'#67c23a'"
                />
              </div>

              <el-alert
                title="学习建议"
                type="info"
                :closable="false"
                show-icon
              >
                <p>建议重点攻克薄弱知识点，每天保持学习{{ Math.max(1, Math.round(prediction.estimated_days / 30)) }}小时，可更快达到目标等级。</p>
              </el-alert>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 原有课程列表区域 -->
    <div class="page-header">
      <h2 class="page-title">课程推荐</h2>
      <el-button type="primary" :icon="Notebook" @click="goToWrongBook">
        我的错题本
      </el-button>
    </div>

    <!-- 顶部搜索栏 -->
    <div class="search-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索课程..."
        style="width: 400px"
        clearable
        @keyup.enter="handleSearch"
      >
        <template #append>
          <el-button :icon="Search" @click="handleSearch" />
        </template>
      </el-input>
    </div>

    <!-- 三级分类筛选栏 -->
    <div class="category-filter">
      <div class="filter-row">
        <span class="filter-label">课程分类：</span>
        <div class="filter-options">
          <el-tag
            v-for="cat in level1Categories"
            :key="cat.id"
            :type="selectedLevel1 === cat.id ? 'primary' : 'info'"
            class="filter-tag"
            @click="selectLevel1Category(cat)"
          >
            {{ cat.name }}
          </el-tag>
        </div>
      </div>

      <div v-if="level2Categories.length > 0" class="filter-row">
        <span class="filter-label">二级分类：</span>
        <div class="filter-options">
          <el-tag
            v-for="cat in level2Categories"
            :key="cat.id"
            :type="selectedLevel2 === cat.id ? 'primary' : 'info'"
            class="filter-tag"
            @click="selectLevel2Category(cat)"
          >
            {{ cat.name }}
          </el-tag>
        </div>
      </div>

      <div v-if="level3Categories.length > 0" class="filter-row">
        <span class="filter-label">三级分类：</span>
        <div class="filter-options">
          <el-tag
            v-for="cat in level3Categories"
            :key="cat.id"
            :type="selectedLevel3 === cat.id ? 'primary' : 'info'"
            class="filter-tag"
            @click="selectLevel3Category(cat)"
          >
            {{ cat.name }}
          </el-tag>
        </div>
      </div>
    </div>

    <!-- 课程卡片列表 -->
    <div class="course-list">
      <div v-if="courseList.length === 0 && !loading" class="empty-data">
        <el-empty description="暂无课程" />
      </div>

      <el-skeleton v-if="loading" :rows="3" animated />

      <el-card
        v-else
        v-for="course in courseList"
        :key="course.id"
        class="course-card"
        shadow="hover"
        @click="goToCourseDetail(course.id)"
      >
        <div class="card-content">
          <div class="card-cover">
            <img :src="getFullImageUrl(course.cover_url)" :alt="course.title" />
          </div>
          <div class="card-info">
            <h3 class="card-title">{{ course.title }}</h3>
            <p class="card-desc">{{ course.description || '暂无简介' }}</p>
            <div class="card-meta">
              <span class="meta-item">
                <el-icon><User /></el-icon>
                {{ course.lecturer || '未知讲师' }}
              </span>
              <span class="meta-item">
                <el-icon><View /></el-icon>
                {{ course.view_count }} 次学习
              </span>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :total="total"
      :page-sizes="[10, 20, 40]"
      layout="total, sizes, prev, pager, next, jumper"
      @current-change="loadCourseList"
      @size-change="handleSizeChange"
      class="pagination"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, User, View, Notebook, Clock, Check, TrendCharts, Medal, Right } from '@element-plus/icons-vue'
import courseApi from '@/api/user/course.js'
import { getUserBehaviorAnalysis, getLearningPrediction } from '@/api/user/userProfile'  // 🔥 修复：改为 userProfile

const router = useRouter()

// 🔥 新增：行为分析相关
const behaviorStats = ref(null)
const weakTags = ref([])
const prediction = ref(null)
const loadingWeakTags = ref(false)
const loadingPrediction = ref(false)

// 默认封面
const defaultCover = 'https://via.placeholder.com/300x200?text=课程封面'

const getFullImageUrl = (url) => {
  if (!url) return defaultCover
  if (url.startsWith('http')) return url
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  return `${baseUrl}${url}`
}

// 搜索
const searchKeyword = ref('')

// 分类
const allCategories = ref([])
const selectedLevel1 = ref(null)
const selectedLevel2 = ref(null)
const selectedLevel3 = ref(null)

// 课程列表
const courseList = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(12)
const total = ref(0)

const level1Categories = computed(() => {
  return allCategories.value.filter(cat => cat.level === 1)
})

const level2Categories = computed(() => {
  if (!selectedLevel1.value) return []
  const level1 = allCategories.value.find(cat => cat.id === selectedLevel1.value)
  return level1?.children || []
})

const level3Categories = computed(() => {
  if (!selectedLevel2.value) return []
  const level2 = allCategories.value.find(cat => cat.id === selectedLevel2.value)
  return level2?.children || []
})

// 🔥 新增：加载行为分析
const loadBehaviorAnalysis = async () => {
  try {
    const res = await getUserBehaviorAnalysis()
    if (res.code === 0) {
      behaviorStats.value = res.data

      // 提取薄弱标签
      if (res.data.weak_tags) {
        weakTags.value = res.data.weak_tags.slice(0, 5)  // 只显示前5个
      }
    }
  } catch (error) {
    console.error('加载行为分析失败:', error)
  }
}

// 🔥 新增：加载学习预测
const loadLearningPrediction = async () => {
  loadingPrediction.value = true
  try {
    const res = await getLearningPrediction()
    if (res.code === 0) {
      prediction.value = res.data
    }
  } catch (error) {
    console.error('加载学习预测失败:', error)
  } finally {
    loadingPrediction.value = false
  }
}

// 🔥 新增：格式化时长
const formatDuration = (seconds) => {
  if (!seconds) return '0分钟'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0) return `${hours}小时${minutes}分钟`
  return `${minutes}分钟`
}

// 🔥 新增：获取掌握度颜色
const getMasteryColor = (score) => {
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#e6a23c'
  return '#f56c6c'
}

const loadCategories = async () => {
  try {
    const res = await courseApi.getCategories()
    if (res && res.code === 0) {
      allCategories.value = res.data
    }
  } catch (error) {
    console.error('加载分类失败:', error)
  }
}

const loadCourseList = async () => {
  loading.value = true
  try {
    const categoryId = selectedLevel3.value || selectedLevel2.value || selectedLevel1.value
    const res = await courseApi.getCourseList({
      category_id: categoryId,
      keyword: searchKeyword.value,
      page: currentPage.value,
      page_size: pageSize.value
    })
    if (res && res.code === 0) {
      courseList.value = res.data.items || res.data.list || []
      total.value = res.data.total || 0
    }
  } catch (error) {
    console.error('加载课程列表失败:', error)
    ElMessage.error('加载课程列表失败')
  } finally {
    loading.value = false
  }
}

const selectLevel1Category = (cat) => {
  selectedLevel1.value = selectedLevel1.value === cat.id ? null : cat.id
  selectedLevel2.value = null
  selectedLevel3.value = null
  currentPage.value = 1
  loadCourseList()
}

const selectLevel2Category = (cat) => {
  selectedLevel2.value = selectedLevel2.value === cat.id ? null : cat.id
  selectedLevel3.value = null
  currentPage.value = 1
  loadCourseList()
}

const selectLevel3Category = (cat) => {
  selectedLevel3.value = selectedLevel3.value === cat.id ? null : cat.id
  currentPage.value = 1
  loadCourseList()
}

const handleSearch = () => {
  currentPage.value = 1
  loadCourseList()
}

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
  loadCourseList()
}

const goToCourseDetail = (courseId) => {
  router.push(`/user/course/${courseId}`)
}

const goToWrongBook = () => {
  router.push('/user/wrong-question-book')
}

onMounted(() => {
  loadCategories()
  loadCourseList()
  loadBehaviorAnalysis()  // 🔥 新增：加载行为分析
  loadLearningPrediction()  // 🔥 新增：加载学习预测
})
</script>

<style scoped>
.learning-center {
  padding: 20px;
}

/* 🔥 新增：行为分析面板样式 */
.analysis-panel {
  margin-bottom: 24px;
}

.stat-card {
  height: 100%;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-info {
  flex: 1;
}

.stat-label {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

/* 🔥 新增：详细分析区域样式 */
.detailed-analysis {
  margin-bottom: 32px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.empty-tip {
  padding: 20px 0;
}

.tag-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.weak-tag-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 8px;
  transition: all 0.3s;
}

.weak-tag-item:hover {
  background: #f0f0f0;
}

.tag-rank {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #f56c6c;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: bold;
  flex-shrink: 0;
}

.tag-info {
  flex: 1;
}

.tag-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.tag-category {
  font-size: 12px;
  color: #999;
}

.tag-score {
  width: 150px;
}

.score-text {
  font-size: 12px;
  color: #666;
  text-align: right;
  margin-top: 4px;
}

.prediction-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.prediction-levels {
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: 20px;
  background: #f9f9f9;
  border-radius: 8px;
}

.level-item {
  text-align: center;
}

.level-label {
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
}

.level-name {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.level-score, .level-time {
  font-size: 13px;
  color: #666;
}

.level-arrow {
  display: flex;
  align-items: center;
}

.confidence-bar {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.confidence-label {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #666;
}

/* 原有样式保持不变 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.search-bar {
  margin-bottom: 24px;
}

.category-filter {
  background: #f5f7fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 24px;
}

.filter-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: 16px;
}

.filter-row:last-child {
  margin-bottom: 0;
}

.filter-label {
  font-size: 14px;
  color: #666;
  width: 80px;
  flex-shrink: 0;
  padding-top: 4px;
}

.filter-options {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.filter-tag {
  cursor: pointer;
  transition: all 0.3s;
}

.filter-tag:hover {
  transform: translateY(-1px);
}

.course-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.course-card {
  cursor: pointer;
  transition: all 0.3s;
  height: 100%;
}

.course-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.card-content {
  display: flex;
  flex-direction: column;
}

.card-content > * {
  pointer-events: auto;
}

.card-cover {
  width: 100%;
  height: 180px;
  overflow: hidden;
  border-radius: 4px;
  margin-bottom: 16px;
}

.card-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.card-info {
  flex: 1;
}

.card-title {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-desc {
  margin: 0 0 12px;
  font-size: 14px;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.card-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #999;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.empty-data {
  grid-column: 1 / -1;
  padding: 60px 0;
}

.pagination {
  display: flex;
  justify-content: center;
}
</style>