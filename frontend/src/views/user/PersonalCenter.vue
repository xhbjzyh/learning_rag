<template>
  <div class="personal-center">
    <h2 class="page-title">个人中心</h2>

    <div class="profile-container">
      <!-- 1. 用户基本信息卡片 -->
      <el-card class="info-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="header-title">
              <el-icon><User /></el-icon>
              基本信息
            </span>
          </div>
        </template>
        <div class="info-content" v-loading="loading.info">
          <div class="info-item">
            <span class="label">用户名：</span>
            <span class="value">{{ userInfo.username || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="label">角色ID：</span>
            <span class="value">{{ userInfo.role_id || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="label">创建时间：</span>
            <span class="value">{{ formatTime(userInfo.create_time) }}</span>
          </div>
        </div>
      </el-card>

      <!-- 2. 用户画像-学习统计卡片 -->
      <el-card class="profile-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="header-title">
              <el-icon><DataAnalysis /></el-icon>
              学习统计
            </span>
          </div>
        </template>
        <div class="profile-content" v-loading="loading.profile">
          <div class="stat-grid">
            <div class="stat-item">
              <div class="stat-value">{{ formatDuration(userProfile.total_study_duration) }}</div>
              <div class="stat-label">学习总时长</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ userProfile.finished_points_count || 0 }}</div>
              <div class="stat-label">已完成知识点</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ userProfile.total_questions || 0 }}</div>
              <div class="stat-label">答题总数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ formatScore(userProfile.average_score) }}%</div>
              <div class="stat-label">平均正确率</div>
            </div>
          </div>

          <!-- 正确率进度条 -->
          <div class="progress-section">
            <div class="progress-label">
              <span>答题正确率</span>
              <span>{{ formatScore(userProfile.average_score) }}%</span>
            </div>
            <el-progress
              :percentage="formatScore(userProfile.average_score)"
              :stroke-width="12"
              :status="getProgressStatus(userProfile.average_score)"
              :show-text="false"
            />
          </div>
        </div>
      </el-card>

      <!-- 3. 行为统计卡片（新增） -->
      <el-card class="behavior-stats-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="header-title">
              <el-icon><TrendCharts /></el-icon>
              行为统计
            </span>
            <el-button size="small" @click="loadBehaviorStats" :loading="loading.behaviorStats">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </template>
        <div class="behavior-content" v-loading="loading.behaviorStats">
          <div class="behavior-grid">
            <div class="behavior-item">
              <div class="behavior-value">{{ behaviorStats.total_learning_sessions || 0 }}</div>
              <div class="behavior-label">学习会话数</div>
            </div>
            <div class="behavior-item">
              <div class="behavior-value">{{ formatDuration(behaviorStats.total_study_duration) }}</div>
              <div class="behavior-label">总学习时长</div>
            </div>
            <div class="behavior-item">
              <div class="behavior-value">{{ Math.round(behaviorStats.average_session_duration / 60) || 0 }}分钟</div>
              <div class="behavior-label">平均会话时长</div>
            </div>
            <div class="behavior-item">
              <div class="behavior-value">{{ behaviorStats.mastered_points_count || 0 }}</div>
              <div class="behavior-label">已掌握知识点</div>
            </div>
            <div class="behavior-item">
              <div class="behavior-value">{{ behaviorStats.learning_streak_days || 0 }}天</div>
              <div class="behavior-label">连续学习</div>
            </div>
            <div class="behavior-item">
              <div class="behavior-value">{{ getPreferredStudyTimeText(behaviorStats.preferred_study_time) }}</div>
              <div class="behavior-label">偏好学习时间</div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 4. 用户画像-强弱标签卡片 -->
      <el-card class="tags-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="header-title">
              <el-icon><Document /></el-icon>
              知识点分析
            </span>
          </div>
        </template>
        <div class="tags-content" v-loading="loading.profile">
          <!-- 薄弱知识点 -->
          <div class="tag-group">
            <div class="group-title">
              <el-tag type="danger" size="small" effect="dark">
                <el-icon><WarningFilled /></el-icon>
                薄弱知识点
              </el-tag>
            </div>
            <div class="tag-list">
              <el-tag
                v-for="tag in userProfile.weak_tags"
                :key="tag"
                type="danger"
                effect="plain"
                class="tag-item"
              >
                {{ tag }}
              </el-tag>
              <span v-if="!userProfile.weak_tags?.length" class="empty-tip">
                <el-icon><CircleCheck /></el-icon>
                暂无薄弱知识点，继续加油！
              </span>
            </div>
          </div>

          <!-- 优势知识点 -->
          <div class="tag-group">
            <div class="group-title">
              <el-tag type="success" size="small" effect="dark">
                <el-icon><Star /></el-icon>
                优势知识点
              </el-tag>
            </div>
            <div class="tag-list">
              <el-tag
                v-for="tag in userProfile.strong_tags"
                :key="tag"
                type="success"
                effect="plain"
                class="tag-item"
              >
                {{ tag }}
              </el-tag>
              <span v-if="!userProfile.strong_tags?.length" class="empty-tip">
                <el-icon><InfoFilled /></el-icon>
                暂无优势知识点，多做题提升吧！
              </span>
            </div>
          </div>

          <!-- 偏好难度 -->
          <div class="tag-group">
            <div class="group-title">
              <el-tag type="warning" size="small" effect="dark">
                <el-icon><TrendCharts /></el-icon>
                偏好难度
              </el-tag>
            </div>
            <div class="tag-list">
              <el-tag type="warning" effect="plain" size="large">
                {{ userProfile.preferred_difficulty || '暂无偏好' }}
              </el-tag>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 5. 学习历史卡片（新增） -->
      <el-card class="history-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="header-title">
              <el-icon><Clock /></el-icon>
              学习历史
            </span>
            <el-button size="small" @click="loadLearningHistory" :loading="loading.history">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </template>
        <div class="history-content" v-loading="loading.history">
          <el-table :data="learningHistory" style="width: 100%" max-height="400">
            <el-table-column prop="title" label="知识点" min-width="150" show-overflow-tooltip />
            <el-table-column prop="study_duration" label="学习时长" width="120">
              <template #default="{ row }">
                {{ formatDuration(row.study_duration) }}
              </template>
            </el-table-column>
            <el-table-column prop="is_mastered" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.is_mastered ? 'success' : 'info'" size="small">
                  {{ row.is_mastered ? '已掌握' : '学习中' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="create_time" label="学习时间" width="180">
              <template #default="{ row }">
                {{ formatDateTime(row.create_time) }}
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="historyPage"
              :page-size="historyPageSize"
              :total="historyTotal"
              layout="total, prev, pager, next"
              @current-change="handleHistoryPageChange"
            />
          </div>
        </div>
      </el-card>

      <!-- 6. 修改密码卡片 -->
      <el-card class="password-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="header-title">
              <el-icon><Lock /></el-icon>
              修改密码
            </span>
          </div>
        </template>
        <div class="password-content">
          <el-form
            :model="passwordForm"
            :rules="passwordRules"
            ref="passwordFormRef"
            label-width="100px"
            size="default"
          >
            <el-form-item label="旧密码" prop="old_password">
              <el-input
                v-model="passwordForm.old_password"
                type="password"
                placeholder="请输入旧密码"
                show-password
                clearable
              />
            </el-form-item>
            <el-form-item label="新密码" prop="new_password">
              <el-input
                v-model="passwordForm.new_password"
                type="password"
                placeholder="请输入新密码（长度6-20位）"
                show-password
                clearable
              />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirm_new_password">
              <el-input
                v-model="passwordForm.confirm_new_password"
                type="password"
                placeholder="请再次输入新密码"
                show-password
                clearable
              />
            </el-form-item>
            <el-form-item class="form-buttons">
              <el-button
                type="primary"
                @click="handleUpdatePassword"
                :loading="loading.password"
                size="large"
              >
                确认修改
              </el-button>
              <el-button @click="resetPasswordForm" size="large">重置</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  User, DataAnalysis, Document, Lock, WarningFilled, CircleCheck,
  Star, InfoFilled, TrendCharts, Refresh, Clock
} from '@element-plus/icons-vue'
import userProfileApi from '@/api/user/userProfile.js'

// 加载状态
const loading = ref({
  info: false,
  profile: false,
  password: false,
  behaviorStats: false,
  history: false
})

// 用户基本信息
const userInfo = ref({})
// 用户画像数据
const userProfile = ref({})

// 行为统计数据（新增）
const behaviorStats = ref({})

// 学习历史（新增）
const learningHistory = ref([])
const historyPage = ref(1)
const historyPageSize = ref(10)
const historyTotal = ref(0)

// 修改密码表单
const passwordFormRef = ref(null)
const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_new_password: ''
})

// 表单验证规则
const passwordRules = {
  old_password: [
    { required: true, message: '请输入旧密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度需在6-20位之间', trigger: 'blur' }
  ],
  confirm_new_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: (rule, value, callback) => {
      if (value !== passwordForm.value.new_password) {
        callback(new Error('两次输入的密码不一致'))
      } else {
        callback()
      }
    }, trigger: 'blur' }
  ]
}

// ==============================================
// 🔥 彻底修复数据异常问题
// ==============================================
/**
 * 格式化时间戳
 * @param {number} timestamp - 时间戳（毫秒）
 */
const formatTime = (timestamp) => {
  if (!timestamp) return '-'
  const date = new Date(timestamp)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

/**
 * 格式化日期时间
 * @param {string} dateTime - ISO格式日期时间
 */
const formatDateTime = (dateTime) => {
  if (!dateTime) return '-'
  const date = new Date(dateTime)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

/**
 * 格式化学习时长（智能显示）
 * @param {number} duration - 时长（秒）
 */
const formatDuration = (duration) => {
  if (!duration || duration <= 0) return '0秒'

  // 转换为数字类型（防止字符串）
  const seconds = Number(duration)

  if (seconds < 60) {
    // 小于1分钟，显示秒
    return `${seconds}秒`
  } else if (seconds < 3600) {
    // 小于1小时，显示分钟
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return remainingSeconds > 0
      ? `${minutes}分${remainingSeconds}秒`
      : `${minutes}分钟`
  } else {
    // 大于1小时，显示小时
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return minutes > 0 ? `${hours}小时${minutes}分钟` : `${hours}小时`
  }
}

/**
 * 获取偏好学习时间文本
 * @param {string} time - morning/afternoon/evening/night
 */
const getPreferredStudyTimeText = (time) => {
  const timeMap = {
    morning: '上午',
    afternoon: '下午',
    evening: '晚上',
    night: '深夜'
  }
  return timeMap[time] || '未设置'
}

/**
 * 格式化正确率（适配满分10分的得分）
 * @param {number} score - 得分（0-10分，满分10分）
 */
const formatScore = (score) => {
  if (!score || score <= 0) return 0
  // 转换逻辑：(得分 / 满分) * 100 = 百分比
  const percentage = (score / 10) * 100
  // 限制在0-100%之间
  return Math.min(percentage, 100).toFixed(1)
}

/**
 * 获取进度条状态（适配满分10分）
 * @param {number} score - 得分（0-10分）
 */
const getProgressStatus = (score) => {
  const validScore = score || 0
  // 满分10分，8分及以上为优秀，6分及以上为合格
  if (validScore >= 8) return 'success'
  if (validScore >= 6) return ''
  return 'exception'
}

// ==============================================
// 接口请求
// ==============================================
const loadUserInfo = async () => {
  loading.value.info = true
  try {
    const res = await userProfileApi.getUserInfo()
    if (res.code === 0 && res.data) {
      userInfo.value = res.data
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
    ElMessage.error('获取用户信息失败')
  } finally {
    loading.value.info = false
  }
}

const loadUserProfile = async () => {
  loading.value.profile = true
  try {
    const res = await userProfileApi.getUserProfile()
    console.log('=== 用户画像API响应 ===')
    console.log('完整响应:', res)
    console.log('响应code:', res.code)
    console.log('响应data:', res.data)
    console.log('total_study_duration:', res.data?.total_study_duration)
    console.log('total_study_duration类型:', typeof res.data?.total_study_duration)

    if (res.code === 0 && res.data) {
      userProfile.value = res.data
      console.log('赋值后的userProfile:', userProfile.value)
      console.log('赋值后的total_study_duration:', userProfile.value.total_study_duration)
    } else {
      console.error('API返回异常:', res)
    }
  } catch (error) {
    console.error('获取用户画像失败:', error)
    ElMessage.error('获取用户画像失败')
  } finally {
    loading.value.profile = false
  }
}

// 加载行为统计（新增）
const loadBehaviorStats = async () => {
  loading.value.behaviorStats = true
  try {
    const res = await userProfileApi.getBehaviorStats()
    if (res.code === 0 && res.data) {
      behaviorStats.value = res.data
      console.log('行为统计数据:', behaviorStats.value)
    }
  } catch (error) {
    console.error('获取行为统计失败:', error)
    ElMessage.error('获取行为统计失败')
  } finally {
    loading.value.behaviorStats = false
  }
}

// 加载学习历史（新增）
const loadLearningHistory = async () => {
  loading.value.history = true
  try {
    const res = await userProfileApi.getLearningHistory({
      page: historyPage.value,
      limit: historyPageSize.value
    })
    if (res.code === 0 && res.data) {
      learningHistory.value = res.data.list
      historyTotal.value = res.data.total
    }
  } catch (error) {
    console.error('获取学习历史失败:', error)
    ElMessage.error('获取学习历史失败')
  } finally {
    loading.value.history = false
  }
}

// 学习历史分页切换
const handleHistoryPageChange = (page) => {
  historyPage.value = page
  loadLearningHistory()
}

const handleUpdatePassword = async () => {
  await passwordFormRef.value.validate()

  loading.value.password = true
  try {
    await userProfileApi.updatePassword(passwordForm.value)
    ElMessage.success('密码修改成功，请重新登录')
    resetPasswordForm()
  } catch (error) {
    console.error('修改密码失败:', error)
    ElMessage.error('修改密码失败，请检查旧密码是否正确')
  } finally {
    loading.value.password = false
  }
}

const resetPasswordForm = () => {
  passwordFormRef.value?.resetFields()
}

// 页面初始化
onMounted(() => {
  loadUserInfo()
  loadUserProfile()
  loadBehaviorStats()
  loadLearningHistory()
})
</script>

<style scoped>
.personal-center {
  padding: 0;
}

.page-title {
  margin: 0 0 24px;
  color: #303133;
  font-size: 24px;
  font-weight: 600;
  padding-bottom: 16px;
  border-bottom: 2px solid #409EFF;
}

.profile-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
  gap: 24px;
}

/* 卡片通用样式 */
.el-card {
  border-radius: 12px;
  transition: all 0.3s ease;
  border: 1px solid #e4e7ed;
}

.el-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(64, 158, 255, 0.15);
  border-color: #409EFF;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.header-title .el-icon {
  color: #409EFF;
  font-size: 20px;
}

/* 基本信息卡片 */
.info-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 8px 0;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
  border-radius: 8px;
  transition: all 0.3s ease;
}

.info-item:hover {
  background: linear-gradient(135deg, #ecf5ff 0%, #ffffff 100%);
  transform: translateX(4px);
}

.info-item .label {
  font-size: 14px;
  color: #606266;
  width: 90px;
  font-weight: 500;
}

.info-item .value {
  font-size: 15px;
  color: #303133;
  font-weight: 500;
}

/* 学习统计卡片 */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-item {
  text-align: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  transition: all 0.3s ease;
  color: white;
}

.stat-item:nth-child(2) {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-item:nth-child(3) {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-item:nth-child(4) {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-item:hover {
  transform: scale(1.05);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 8px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.stat-label {
  font-size: 13px;
  opacity: 0.95;
}

.progress-section {
  margin-top: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.progress-label {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  color: #606266;
  margin-bottom: 12px;
  font-weight: 500;
}

/* 行为统计卡片（新增） */
.behavior-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.behavior-item {
  text-align: center;
  padding: 16px;
  background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
  border-radius: 10px;
  transition: all 0.3s ease;
}

.behavior-item:nth-child(odd) {
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
}

.behavior-item:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
}

.behavior-value {
  font-size: 22px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 6px;
}

.behavior-label {
  font-size: 12px;
  color: #606266;
}

/* 知识点分析卡片 */
.tags-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.tag-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.group-title {
  font-size: 14px;
  font-weight: 500;
}

.group-title .el-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  font-size: 13px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  min-height: 40px;
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
}

.tag-item {
  margin: 0;
  font-size: 13px;
  padding: 6px 12px;
  transition: all 0.3s ease;
}

.tag-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.empty-tip {
  font-size: 13px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 6px;
}

.empty-tip .el-icon {
  font-size: 16px;
}

/* 学习历史卡片（新增） */
.history-content {
  padding: 8px 0;
}

.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}

/* 修改密码卡片 */
.password-content {
  max-width: 500px;
  margin: 0 auto;
  padding: 20px 0;
}

.form-buttons {
  margin-top: 24px;
  text-align: right;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.form-buttons .el-button {
  margin-left: 0;
  min-width: 100px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .profile-container {
    grid-template-columns: 1fr;
  }

  .stat-grid {
    grid-template-columns: 1fr;
  }

  .behavior-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .page-title {
    font-size: 20px;
  }
}
</style>