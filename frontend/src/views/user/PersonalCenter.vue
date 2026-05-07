<template>
  <div class="user-profile">
    <h2 class="page-title">个人中心</h2>

    <div class="profile-container">
      <!-- 1. 用户基本信息卡片 -->
      <el-card class="info-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>基本信息</span>
            <el-icon><User /></el-icon>
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
            <span>学习统计</span>
            <el-icon><DataAnalysis /></el-icon>
          </div>
        </template>
        <div class="profile-content" v-loading="loading.profile">
          <div class="stat-grid">
            <div class="stat-item">
              <div class="stat-value">{{ formatDuration(userProfile.total_study_duration) }}</div>
              <div class="stat-label">学习总时长（小时）</div>
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
              :stroke-width="10"
              :status="getProgressStatus(userProfile.average_score)"
              :show-text="false"
            />
          </div>
        </div>
      </el-card>

      <!-- 3. 用户画像-强弱标签卡片 -->
      <el-card class="tags-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>知识点分析</span>
            <el-icon><Document /></el-icon>
          </div>
        </template>
        <div class="tags-content" v-loading="loading.profile">
          <!-- 薄弱知识点 -->
          <div class="tag-group">
            <div class="group-title">
              <el-tag type="danger" size="small" effect="dark">薄弱知识点</el-tag>
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
                暂无薄弱知识点，继续加油！
              </span>
            </div>
          </div>

          <!-- 优势知识点 -->
          <div class="tag-group">
            <div class="group-title">
              <el-tag type="success" size="small" effect="dark">优势知识点</el-tag>
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
                暂无优势知识点，多做题提升吧！
              </span>
            </div>
          </div>

          <!-- 偏好难度 -->
          <div class="tag-group">
            <div class="group-title">
              <el-tag type="warning" size="small" effect="dark">偏好难度</el-tag>
            </div>
            <div class="tag-list">
              <el-tag type="warning" effect="plain">
                {{ userProfile.preferred_difficulty || '暂无偏好' }}
              </el-tag>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 4. 修改密码卡片 -->
      <el-card class="password-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>修改密码</span>
            <el-icon><Lock /></el-icon>
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
              >
                确认修改
              </el-button>
              <el-button @click="resetPasswordForm">重置</el-button>
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
import { User, DataAnalysis, Document, Lock } from '@element-plus/icons-vue'
import userProfileApi from '@/api/user/userProfile.js'

// 加载状态
const loading = ref({
  info: false,
  profile: false,
  password: false
})

// 用户基本信息
const userInfo = ref({})
// 用户画像数据
const userProfile = ref({})

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
 * 格式化学习时长（自动识别单位，避免异常值）
 * @param {number} duration - 时长（毫秒/秒）
 */
const formatDuration = (duration) => {
  if (!duration || duration <= 0) return 0

  // 自动识别单位：如果数值过大，说明是毫秒，否则是秒
  let hours
  if (duration > 1e9) { // 大于1e9毫秒（约11天），按毫秒计算
    hours = duration / 1000/1000/1000 / 60 / 60
  } else { // 否则按秒计算
    hours = duration / 60 / 60
  }

  // 限制最大显示9999小时，避免异常值
  return Math.min(hours, 9999).toFixed(1)
}

/**
 * 格式化正确率（限制在0-100%之间）
 * @param {number} score - 正确率（0-1 或 0-100）
 */
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

/**
 * 获取进度条状态
 * @param {number} score - 正确率
 */


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
    if (res.code === 0 && res.data) {
      userProfile.value = res.data
    }
  } catch (error) {
    console.error('获取用户画像失败:', error)
    ElMessage.error('获取用户画像失败')
  } finally {
    loading.value.profile = false
  }
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
})
</script>

<style scoped>
.page-title {
  margin: 0 0 24px;
  color: #303133;
  font-size: 22px;
  font-weight: 600;
}

.profile-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
  gap: 24px;
}

/* 卡片通用样式 */
.el-card {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.el-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.card-header .el-icon {
  color: #909399;
  font-size: 18px;
}

/* 基本信息卡片 */
.info-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-item .label {
  font-size: 14px;
  color: #606266;
  width: 80px;
  font-weight: 500;
}

.info-item .value {
  font-size: 14px;
  color: #303133;
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
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.stat-item:hover {
  background: #ecf5ff;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #409eff;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: #606266;
}

.progress-section {
  margin-top: 16px;
}

.progress-label {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
  font-weight: 500;
}

/* 知识点分析卡片 */
.tags-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.tag-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.group-title {
  font-size: 14px;
  font-weight: 500;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.tag-item {
  margin: 0;
  font-size: 12px;
}

.empty-tip {
  font-size: 13px;
  color: #909399;
}

/* 修改密码卡片 */
.password-content {
  max-width: 450px;
  margin: 0 auto;
}

.form-buttons {
  margin-top: 20px;
  text-align: right;
}

.form-buttons .el-button {
  margin-left: 12px;
}
</style>