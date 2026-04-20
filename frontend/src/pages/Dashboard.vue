<template>
  <div class="dashboard-page">
    <!-- 无权限提示 -->
    <div v-if="!hasPermission" class="no-permission">
      <el-empty description="您没有权限访问该页面，仅管理员和审核员可查看" />
      <el-button type="primary" @click="$router.push('/chat')" style="margin-top: 20px">
        前往AI问答
      </el-button>
    </div>

    <!-- 有权限：仪表盘内容 -->
    <template v-else>
      <!-- 统计卡片 -->
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-number">{{ stats.userCount }}</div>
              <div class="stat-label">注册用户数</div>
            </div>
            <div class="stat-icon" style="background: #409eff">
              <el-icon :size="40"><User /></el-icon>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-number">{{ stats.knowledgeCount }}</div>
              <div class="stat-label">知识点总数</div>
            </div>
            <div class="stat-icon" style="background: #67c23a">
              <el-icon :size="40"><Document /></el-icon>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-number">{{ stats.chatCount }}</div>
              <div class="stat-label">AI问答次数</div>
            </div>
            <div class="stat-icon" style="background: #e6a23c">
              <el-icon :size="40"><ChatDotRound /></el-icon>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-number">{{ stats.onlineCount }}</div>
              <div class="stat-label">当前在线</div>
            </div>
            <div class="stat-icon" style="background: #f56c6c">
              <el-icon :size="40"><Connection /></el-icon>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 图表区域 -->
      <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="12">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span>问答趋势（近7天）</span>
              </div>
            </template>
            <div class="chart-placeholder">
              <el-empty description="后续可对接ECharts图表" />
            </div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span>知识点分类占比</span>
              </div>
            </template>
            <div class="chart-placeholder">
              <el-empty description="后续可对接ECharts图表" />
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 最近活动 -->
      <el-row style="margin-top: 20px">
        <el-col :span="24">
          <el-card class="activity-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span>最近活动</span>
              </div>
            </template>
            <el-timeline>
              <el-timeline-item
                v-for="(activity, index) in activities"
                :key="index"
                :timestamp="activity.timestamp"
                :type="activity.type"
              >
                {{ activity.content }}
              </el-timeline-item>
            </el-timeline>
          </el-card>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useUserStore } from '@/store/user'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'
import { User, Document, ChatDotRound, Connection } from '@element-plus/icons-vue'

const userStore = useUserStore()

// 权限判断
const hasPermission = computed(() => {
  return userStore.roleId === 1 || userStore.roleId === 2
})

// 统计数据
const stats = ref({
  userCount: 0,
  knowledgeCount: 0,
  chatCount: 0,
  onlineCount: 0
})

// 最近活动
const activities = ref([
  {
    content: '全量同步知识库完成',
    timestamp: '2026-04-15 17:00:00',
    type: 'info'
  }
])

// 获取统计数据
const getStatsData = async () => {
  if (!hasPermission.value) return
  try {
    const res = await request.get('/stats/overview')
    stats.value = {
      userCount: res.data.user_count || 0,
      knowledgeCount: res.data.knowledge_count || 0,
      chatCount: res.data.chat_count || 0,
      onlineCount: res.data.online_count || 0
    }
  } catch (err) {
    console.error(err)
    // 如果接口报错，用模拟数据
    stats.value = {
      userCount: 128,
      knowledgeCount: 256,
      chatCount: 1024,
      onlineCount: 15
    }
  }
}

onMounted(() => {
  if (hasPermission.value) {
    getStatsData()
  }
})
</script>

<style scoped>
.dashboard-page {
  max-width: 1400px;
  margin: 0 auto;
}
.no-permission {
  height: 60vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.stat-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.stat-content {
  flex: 1;
}
.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
}
.stat-label {
  font-size: 14px;
  color: #909399;
}
.stat-icon {
  width: 80px;
  height: 80px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}
.chart-card {
  margin-bottom: 20px;
}
.chart-placeholder {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.activity-card {
  margin-bottom: 20px;
}
</style>