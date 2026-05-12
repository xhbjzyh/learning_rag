<template>
  <div class="dashboard">
    <h2 class="page-title">学习仪表盘</h2>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #409EFF;">
              <el-icon :size="30"><Clock /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_study_duration_hours || 0 }}h</div>
              <div class="stat-label">总学习时长</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #67C23A;">
              <el-icon :size="30"><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.finished_points_count || 0 }}</div>
              <div class="stat-label">已完成知识点</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #E6A23C;">
              <el-icon :size="30"><List /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.completion_rate || 0 }}%</div>
              <div class="stat-label">完成率</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #F56C6C;">
              <el-icon :size="30"><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.wrong_question_count || 0 }}</div>
              <div class="stat-label">待复习错题</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷入口 -->
    <el-row :gutter="20" class="quick-entry-row">
      <el-col :span="12">
        <el-card class="entry-card" shadow="hover" @click="goToRAGChat">
          <el-icon class="entry-icon" :size="40" color="#409EFF"><ChatDotRound /></el-icon>
          <div class="entry-title">RAG问答</div>
          <div class="entry-desc">开始智能问答学习</div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="entry-card" shadow="hover" @click="goToLearningCenter">
          <el-icon class="entry-icon" :size="40" color="#67C23A"><Notebook /></el-icon>
          <div class="entry-title">学习中心</div>
          <div class="entry-desc">查看学习进度和错题</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 今日学习 -->
    <el-card class="today-card">
      <template #header>
        <div class="card-header">
          <span>今日学习</span>
        </div>
      </template>
      <div class="today-content">
        <div class="today-study">
          <div class="today-value">{{ stats.today_study_duration_minutes || 0 }}分钟</div>
          <div class="today-label">今日已学习</div>
        </div>
        <el-button type="primary" @click="goToRAGChat">继续学习</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Clock, Document, List, Warning, ChatDotRound, Notebook } from '@element-plus/icons-vue'
import learningCenterApi from '@/api/user/learningCenter.js'

const router = useRouter()
const loading = ref(false)

const stats = ref({
  total_study_duration_hours: 0,
  finished_points_count: 0,
  completion_rate: 0,
  wrong_question_count: 0,
  today_study_duration_minutes: 0
})

const fetchStats = async () => {
  loading.value = true
  try {
    const res = await learningCenterApi.getStats()
    console.log('📊 学习统计数据:', res)

    // 🔥 处理后端返回的数据格式
    if (res && res.code === 0 && res.data) {
      const data = res.data

      // 总学习时长（秒转小时）
      const totalSeconds = data.total_study_duration || 0
      stats.value.total_study_duration_hours = (totalSeconds / 3600).toFixed(1)

      // 已完成知识点/资源
      stats.value.finished_points_count = data.finished_points_count || 0

      // 完成率
      stats.value.completion_rate = data.completion_rate || 0

      // 待复习错题数
      stats.value.wrong_question_count = data.wrong_question_count || 0

      // 今日学习时长（秒转分钟）
      const todaySeconds = data.today_study_duration || 0
      stats.value.today_study_duration_minutes = Math.floor(todaySeconds / 60)

      console.log('✅ 统计数据已更新:', stats.value)
    } else {
      console.warn('⚠️ 获取统计数据失败:', res?.msg || '未知错误')
    }
  } catch (error) {
    console.error('❌ 获取学习统计失败:', error)
  } finally {
    loading.value = false
  }
}

const goToRAGChat = () => {
  router.push('/user/rag-chat')
}

const goToLearningCenter = () => {
  router.push('/user/learning-center')
}

onMounted(() => {
  fetchStats()  // 🔥 启用统计数据获取
  console.log('✅ Dashboard 页面已加载')
})

</script>

<style scoped>
.dashboard {
  padding: 0;
}

.page-title {
  margin-bottom: 24px;
  color: #303133;
  font-size: 24px;
  font-weight: 600;
  padding-bottom: 16px;
  border-bottom: 2px solid #409EFF;
}

.stats-row {
  margin-bottom: 24px;
}

.stat-card {
  cursor: default;
  border-radius: 12px;
  transition: all 0.3s ease;
  border: 1px solid #e4e7ed;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(64, 158, 255, 0.15);
  border-color: #409EFF;
}

.stat-content {
  display: flex;
  align-items: center;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #fff;
  margin-right: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 6px;
}

.quick-entry-row {
  margin-bottom: 24px;
}

.entry-card {
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 12px;
  border: 2px solid transparent;
  padding: 30px 20px;
}

.entry-card:hover {
  transform: translateY(-6px);
  border-color: #409EFF;
  box-shadow: 0 12px 32px rgba(64, 158, 255, 0.2);
}

.entry-icon {
  margin: 0 0 16px;
  transition: all 0.3s ease;
}

.entry-card:hover .entry-icon {
  transform: scale(1.1);
}

.entry-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.entry-desc {
  font-size: 14px;
  color: #909399;
}

.today-card {
  margin-bottom: 20px;
  border-radius: 12px;
  border: 1px solid #e4e7ed;
}

.today-card :deep(.el-card__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px 12px 0 0;
  padding: 16px 20px;
}

.today-card :deep(.el-card__header .card-header span) {
  color: white;
  font-weight: 600;
  font-size: 16px;
}

.today-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30px 20px;
}

.today-study {
  text-align: center;
}

.today-value {
  font-size: 36px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.today-label {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .stats-row .el-col {
    margin-bottom: 16px;
  }

  .quick-entry-row .el-col {
    margin-bottom: 16px;
  }

  .stat-value {
    font-size: 24px;
  }

  .today-value {
    font-size: 28px;
  }
}
</style>