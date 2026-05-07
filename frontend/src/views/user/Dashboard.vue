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
              <div class="stat-value">{{ stats.total_study_duration_hours }}h</div>
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
              <div class="stat-value">{{ stats.finished_points_count }}</div>
              <div class="stat-label">已完成知识点</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #E6A23C;">
              <el-icon :size="30"><ListCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.completion_rate }}%</div>
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
              <div class="stat-value">{{ stats.wrong_question_count }}</div>
              <div class="stat-label">待复习错题</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷入口 -->
    <el-row :gutter="20" class="quick-entry-row">
      <el-col :span="8">
        <el-card class="entry-card" shadow="hover" @click="goToRAGChat">
          <el-icon class="entry-icon" :size="40" color="#409EFF"><ChatDotRound /></el-icon>
          <div class="entry-title">RAG问答</div>
          <div class="entry-desc">开始智能问答学习</div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="entry-card" shadow="hover" @click="goToLearningCenter">
          <el-icon class="entry-icon" :size="40" color="#67C23A"><Notebook /></el-icon>
          <div class="entry-title">学习中心</div>
          <div class="entry-desc">查看学习进度和错题</div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="entry-card" shadow="hover" @click="goToRecommend">
          <el-icon class="entry-icon" :size="40" color="#E6A23C"><MagicStick /></el-icon>
          <div class="entry-title">个性化推荐</div>
          <div class="entry-desc">获取专属学习路径</div>
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
          <div class="today-value">{{ stats.today_study_duration_minutes }}分钟</div>
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
import { Clock, Document, List, Warning, ChatDotRound, Notebook, MagicStick } from '@element-plus/icons-vue'
import learningCenterApi from '@/api/user/learningCenter'

const router = useRouter()

const stats = ref({
  total_study_duration_hours: 0,
  finished_points_count: 0,
  completion_rate: 0,
  wrong_question_count: 0,
  today_study_duration_minutes: 0
})

const fetchStats = async () => {
  try {
    const res = await learningCenterApi.getStats()
    stats.value = res.data
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

const goToRAGChat = () => {
  router.push('/user/rag-chat')
}

const goToLearningCenter = () => {
  router.push('/user/learning-center')
}

const goToRecommend = () => {
  router.push('/user/personal-recommend')
}

onMounted(() => {
  fetchStats()
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.page-title {
  margin-bottom: 20px;
  color: #333;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  cursor: default;
}

.stat-content {
  display: flex;
  align-items: center;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #fff;
  margin-right: 15px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #999;
  margin-top: 5px;
}

.quick-entry-row {
  margin-bottom: 20px;
}

.entry-card {
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.entry-card:hover {
  transform: translateY(-5px);
}

.entry-icon {
  margin: 20px 0 10px;
}

.entry-title {
  font-size: 16px;
  font-weight: bold;
  color: #333;
  margin-bottom: 5px;
}

.entry-desc {
  font-size: 14px;
  color: #999;
}

.today-card {
  margin-bottom: 20px;
}

.today-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.today-study {
  text-align: center;
}

.today-value {
  font-size: 32px;
  font-weight: bold;
  color: #409EFF;
}

.today-label {
  font-size: 14px;
  color: #666;
  margin-top: 5px;
}
</style>