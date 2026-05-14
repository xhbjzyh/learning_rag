<template>
  <div class="personal-recommend">
    <h2 class="page-title">个性化推荐</h2>

    <!-- 标签页切换：课程推荐 / 知识点推荐 / 学习路径 -->
    <el-tabs v-model="activeTab" type="border-card" class="recommend-tabs">
      <!-- 🔥 新增：1. 个性化课程推荐（第二阶段） -->
      <el-tab-pane label="课程推荐" name="courses">
        <div class="control-bar">
          <div class="param-item">
            <span class="label">搜索关键词：</span>
            <el-input
              v-model="searchQuery"
              placeholder="输入感兴趣的关键词"
              clearable
              style="width: 300px"
            />
          </div>
          <div class="param-item">
            <span class="label">推荐数量：</span>
            <el-input-number
              v-model="courseLimit"
              :min="5"
              :max="20"
              controls-position="right"
              size="small"
            />
          </div>
          <el-button
            type="primary"
            @click="loadCourseRecommendations"
            :loading="loading.courses"
            size="small"
          >
            重新推荐
          </el-button>
        </div>

        <!-- 加载中 / 空状态 / 推荐列表 -->
        <div v-loading="loading.courses" class="content-container">
          <div v-if="courseRecommendList.length === 0" class="empty-data">
            <el-icon><VideoPlay /></el-icon>
            <p>暂无推荐课程，开始学习吧！</p>
          </div>
          <div v-else class="course-recommend-list">
            <el-card
              v-for="item in courseRecommendList"
              :key="item.course_id"
              class="course-recommend-card"
              shadow="hover"
            >
              <div class="card-content">
                <div class="course-info">
                  <h3 class="course-title">{{ item.course_title }}</h3>
                  <div class="recommend-meta">
                    <el-tag :type="getRecommendTypeTag(item.recommend_type)" size="small">
                      {{ getRecommendTypeText(item.recommend_type) }}
                    </el-tag>
                    <span class="score-label">推荐分：{{ (item.final_score * 100).toFixed(1) }}</span>
                  </div>
                  <div class="reason-box" v-if="item.reason">
                    <el-icon><ChatDotRound /></el-icon>
                    <span>{{ item.reason }}</span>
                  </div>
                </div>
                <div class="action-buttons">
                  <el-button type="primary" size="small" @click="goToCourse(item.course_id)">
                    去学习
                  </el-button>
                  <el-button size="small" @click="showFeedbackDialog(item)">
                    反馈
                  </el-button>
                </div>
              </div>
            </el-card>
          </div>
        </div>
      </el-tab-pane>

      <!-- 2. 个性化推荐知识点 -->
      <el-tab-pane label="知识点推荐" name="knowledge">
        <div class="control-bar">
          <div class="param-item">
            <span class="label">推荐数量：</span>
            <el-input-number
              v-model="topK"
              :min="1"
              :max="20"
              controls-position="right"
              size="small"
            />
          </div>
          <el-button
            type="primary"
            @click="loadPersonalRecommend"
            :loading="loading.personal"
            size="small"
          >
            重新推荐
          </el-button>
        </div>

        <!-- 加载中 / 空状态 / 错误状态 -->
        <div v-loading="loading.personal" class="content-container">
          <div v-if="personalRecommendList.length === 0" class="empty-data">
            <el-icon><Document /></el-icon>
            <p>暂无推荐知识点</p>
          </div>
          <div v-else class="recommend-list">
            <el-card
              v-for="item in personalRecommendList"
              :key="item.id"
              class="recommend-card"
              shadow="hover"
            >
              <div class="card-header">
                <h3 class="title">{{ item.title }}</h3>
                <el-tag :type="getDifficultyTag(item.difficulty)" size="small">
                  {{ item.difficulty }}
                </el-tag>
              </div>
              <div class="card-content">
                <p class="content-text">{{ item.content }}</p>
                <div class="key-points" v-if="item.key_points">
                  <span class="label">关键要点：</span>
                  <span class="text">{{ item.key_points }}</span>
                </div>
              </div>
            </el-card>
          </div>
        </div>
      </el-tab-pane>

      <!-- 3. 个性化学习路径 -->
      <el-tab-pane label="学习路径" name="path">
        <div class="control-bar">
          <div class="param-item">
            <span class="label">路径长度：</span>
            <el-input-number
              v-model="maxLength"
              :min="1"
              :max="20"
              controls-position="right"
              size="small"
            />
          </div>
          <el-button
            type="primary"
            @click="loadLearningPath"
            :loading="loading.path"
            size="small"
          >
            生成路径
          </el-button>
        </div>

        <!-- 加载中 / 空状态 / 错误状态 -->
        <div v-loading="loading.path" class="content-container">
          <div v-if="learningPathList.length === 0" class="empty-data">
            <el-icon><Guide /></el-icon>
            <p>暂无学习路径</p>
          </div>
          <div v-else class="path-list">
            <el-card
              v-for="(item, index) in learningPathList"
              :key="item.id"
              class="path-card"
              shadow="hover"
            >
              <div class="card-header">
                <div class="order-badge">{{ index + 1 }}</div>
                <div class="header-content">
                  <h3 class="title">{{ item.title }}</h3>
                  <el-tag :type="getDifficultyTag(item.difficulty)" size="small">
                    {{ item.difficulty }}
                  </el-tag>
                </div>
              </div>
              <div class="card-content">
                <p class="content-text">{{ item.content }}</p>
                <div class="reason" v-if="item.reason">
                  <span class="label">推荐理由：</span>
                  <span class="text">{{ item.reason }}</span>
                </div>
                <div class="suggestion" v-if="item.suggestion">
                  <span class="label">学习建议：</span>
                  <span class="text">{{ item.suggestion }}</span>
                </div>
              </div>
            </el-card>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 🔥 新增：反馈对话框 -->
    <el-dialog v-model="feedbackDialogVisible" title="推荐反馈" width="400px">
      <el-form :model="feedbackForm" label-width="80px">
        <el-form-item label="是否点击">
          <el-radio-group v-model="feedbackForm.is_clicked">
            <el-radio :label="true">是</el-radio>
            <el-radio :label="false">否</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="是否有用">
          <el-radio-group v-model="feedbackForm.is_helpful">
            <el-radio :label="true">有用</el-radio>
            <el-radio :label="false">无用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="评分">
          <el-rate v-model="feedbackForm.feedback_score" :max="5" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="feedbackDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitFeedback">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, Guide, VideoPlay, ChatDotRound } from '@element-plus/icons-vue'
import personalRecommendApi from '@/api/user/personalRecommend.js'
import recommendationApi from '@/api/user/recommendation.js'  // 🔥 新增导入

const router = useRouter()

// 标签页控制
const activeTab = ref('courses')  // 🔥 修改默认标签页为课程推荐

// 🔥 新增：课程推荐参数
const searchQuery = ref('')
const courseLimit = ref(10)
const courseRecommendList = ref([])
const feedbackDialogVisible = ref(false)
const currentRecommendItem = ref(null)
const feedbackForm = ref({
  is_clicked: true,
  is_helpful: true,
  feedback_score: 4
})

// 原有参数
const topK = ref(10)
const maxLength = ref(10)

// 数据存储
const personalRecommendList = ref([])
const learningPathList = ref([])

// 加载状态
const loading = ref({
  courses: false,  // 🔥 新增
  personal: false,
  path: false
})

// ==============================================
// 工具函数：难度标签样式
// ==============================================
const getDifficultyTag = (difficulty) => {
  const map = {
    '简单': 'success',
    '中等': 'warning',
    '困难': 'danger'
  }
  return map[difficulty] || 'info'
}

// 🔥 新增：推荐类型标签
const getRecommendTypeTag = (type) => {
  const map = {
    'collaborative_filtering': 'success',
    'content_based': 'primary',
    'profile_based': 'warning',
    'hybrid': 'success',
    'popular': 'info'
  }
  return map[type] || 'info'
}

// 🔥 新增：推荐类型文本
const getRecommendTypeText = (type) => {
  const map = {
    'collaborative_filtering': '协同过滤',
    'content_based': '内容相似',
    'profile_based': '兴趣匹配',
    'hybrid': '混合推荐',
    'popular': '热门推荐'
  }
  return map[type] || type
}

// 🔥 新增：跳转到课程详情
const goToCourse = (courseId) => {
  console.log('跳转到课程:', courseId)  // 🔥 调试日志
  router.push({
    path: `/user/course/${courseId}`
  })
}

// 🔥 新增：显示反馈对话框
const showFeedbackDialog = (item) => {
  currentRecommendItem.value = item
  feedbackDialogVisible.value = true
}

// 🔥 新增：提交反馈
const submitFeedback = async () => {
  try {
    await recommendationApi.submitRecommendationFeedback({
      recommendation_id: currentRecommendItem.value.course_id,  // 这里需要后端返回 recommendation_id
      is_clicked: feedbackForm.value.is_clicked,
      is_helpful: feedbackForm.value.is_helpful,
      feedback_score: feedbackForm.value.feedback_score
    })

    ElMessage.success('反馈提交成功')
    feedbackDialogVisible.value = false

    // 重置表单
    feedbackForm.value = {
      is_clicked: true,
      is_helpful: true,
      feedback_score: 4
    }
  } catch (error) {
    console.error('提交反馈失败:', error)
    ElMessage.error('提交反馈失败')
  }
}

// 🔥 新增：加载课程推荐
const loadCourseRecommendations = async () => {
  loading.value.courses = true
  try {
    const res = await recommendationApi.getPersonalizedRecommendations({
      query: searchQuery.value,
      limit: courseLimit.value
    })

    if (res.code === 0 && res.data) {
      courseRecommendList.value = res.data.recommendations || []

      if (courseRecommendList.value.length === 0) {
        ElMessage.info('暂无推荐课程')
      }
    } else {
      courseRecommendList.value = []
      ElMessage.warning(res.msg || '获取推荐失败')
    }
  } catch (error) {
    console.error('获取课程推荐失败:', error)
    ElMessage.error('获取推荐失败，请稍后重试')
    courseRecommendList.value = []
  } finally {
    loading.value.courses = false
  }
}

// ==============================================
// 1. 加载个性化推荐知识点
// ==============================================
const loadPersonalRecommend = async () => {
  loading.value.personal = true
  try {
    const res = await personalRecommendApi.getPersonalRecommend({ top_k: topK.value })
    if (res.code === 0 && res.data) {
      personalRecommendList.value = res.data
    } else {
      personalRecommendList.value = []
      ElMessage.warning(res.msg || '获取推荐失败')
    }
  } catch (error) {
    console.error('获取知识点推荐失败:', error)
    ElMessage.error('获取推荐失败，请稍后重试')
    personalRecommendList.value = []
  } finally {
    loading.value.personal = false
  }
}

// ==============================================
// 2. 加载个性化学习路径
// ==============================================
const loadLearningPath = async () => {
  loading.value.path = true
  try {
    const res = await personalRecommendApi.getLearningPath({ max_length: maxLength.value })
    if (res.code === 0 && res.data) {
      learningPathList.value = res.data
    } else {
      learningPathList.value = []
      ElMessage.warning(res.msg || '生成学习路径失败')
    }
  } catch (error) {
    console.error('生成学习路径失败:', error)
    ElMessage.error('生成学习路径失败，请稍后重试')
    learningPathList.value = []
  } finally {
    loading.value.path = false
  }
}

// 页面初始化加载默认数据
onMounted(() => {
  loadCourseRecommendations()  // 🔥 新增：默认加载课程推荐
  loadPersonalRecommend()
  loadLearningPath()
})
</script>

<style scoped>
.page-title {
  margin: 0 0 20px;
  color: #333;
  font-size: 20px;
}

.control-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
  flex-wrap: wrap;
}

.param-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.param-item .label {
  font-size: 14px;
  color: #606266;
}

.content-container {
  min-height: 200px;
}

.empty-data {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  color: #909399;
}

.empty-data .el-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

/* 🔥 新增：课程推荐卡片样式 */
.course-recommend-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.course-recommend-card {
  transition: all 0.3s;
}

.course-recommend-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}

.course-info {
  flex: 1;
}

.course-title {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.recommend-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.score-label {
  font-size: 13px;
  color: #909399;
}

.reason-box {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #606266;
  padding: 8px 12px;
  background: #f0f9ff;
  border-radius: 4px;
  border-left: 3px solid #409eff;
}

.reason-box .el-icon {
  color: #409eff;
}

.action-buttons {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

/* 知识点推荐卡片样式 */
.recommend-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 16px;
}

.recommend-card, .path-card {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.card-header .title {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.card-content .content-text {
  margin: 0 0 8px;
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
}

.card-content .key-points,
.card-content .reason,
.card-content .suggestion {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  font-size: 13px;
  color: #909399;
}

.card-content .key-points .label,
.card-content .reason .label,
.card-content .suggestion .label {
  font-weight: 500;
  color: #606266;
}

/* 学习路径卡片样式 */
.path-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.path-card .card-header {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.order-badge {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #409eff;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 500;
  flex-shrink: 0;
}

.path-card .header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex: 1;
}
</style>