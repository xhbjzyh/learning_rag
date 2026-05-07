<template>
  <div class="personal-recommend">
    <h2 class="page-title">个性化推荐</h2>

    <!-- 标签页切换：知识点推荐 / 学习路径 -->
    <el-tabs v-model="activeTab" type="border-card" class="recommend-tabs">
      <!-- 1. 个性化推荐知识点 -->
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

      <!-- 2. 个性化学习路径 -->
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Guide } from '@element-plus/icons-vue'
import personalRecommendApi from '@/api/user/personalRecommend.js'

// 标签页控制
const activeTab = ref('knowledge')

// 参数控制
const topK = ref(10) // 知识点推荐数量，默认10，最大20
const maxLength = ref(10) // 学习路径长度，默认10，最大20

// 数据存储
const personalRecommendList = ref([])
const learningPathList = ref([])

// 加载状态
const loading = ref({
  personal: false,
  path: false
})

// ==============================================
// 工具函数：难度标签样式（和学习中心保持一致）
// ==============================================
const getDifficultyTag = (difficulty) => {
  const map = {
    '简单': 'success',
    '中等': 'warning',
    '困难': 'danger'
  }
  return map[difficulty] || 'info'
}

// ==============================================
// 1. 加载个性化推荐知识点
// ==============================================
const loadPersonalRecommend = async () => {
  loading.value.personal = true
  try {
    const res = await personalRecommendApi.getPersonalRecommend({ top_k: topK.value })
    // 处理后端响应格式：{ code:0, msg:"success", data:[] }
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
    // 处理后端响应格式：{ code:0, msg:"success", data:[] }
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