<template>
  <div class="course-detail">
    <!-- 顶部课程信息 -->
    <div class="course-header">
      <div class="header-content">
        <div class="course-cover">
          <img :src="courseDetail.cover_url || defaultCover" :alt="courseDetail.title" />
        </div>
        <div class="course-info">
          <h1 class="course-title">{{ courseDetail.title }}</h1>
          <p class="course-desc">{{ courseDetail.description }}</p>
          <div class="course-meta">
            <span class="meta-item">
              <el-icon><User /></el-icon>
              讲师：{{ courseDetail.lecturer || '未知' }}
            </span>
            <span class="meta-item">
              <el-icon><View /></el-icon>
              {{ courseDetail.view_count }} 次学习
            </span>
            <span v-if="courseDetail.user_progress" class="meta-item progress">
              学习进度：{{ courseDetail.user_progress.progress.toFixed(0) }}%
            </span>
          </div>
          <div class="course-actions">
            <el-button type="primary" size="large" @click="startLearning">
              开始学习
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 内容标签页 -->
    <div class="course-content">
      <el-tabs v-model="activeTab" type="border-card">
        <!-- 学习视频 -->
        <el-tab-pane label="学习视频" name="video">
          <div class="resource-list">
            <div v-if="videoResources.length === 0" class="empty-data">
              <el-empty description="暂无视频资源" />
            </div>
            <el-card
              v-for="resource in videoResources"
              :key="resource.id"
              class="resource-card"
              shadow="hover"
              @click="playVideo(resource)"
            >
              <div class="resource-content">
                <div class="resource-icon video-icon">
                  <el-icon :size="40"><VideoPlay /></el-icon>
                </div>
                <div class="resource-info">
                  <h4 class="resource-title">{{ resource.title }}</h4>
                  <p class="resource-desc">{{ resource.description || '暂无描述' }}</p>
                  <span class="resource-duration">
                    {{ formatDuration(resource.duration) }}
                  </span>
                </div>
              </div>
            </el-card>
          </div>
        </el-tab-pane>

        <!-- 书籍资料 -->
        <el-tab-pane label="书籍资料" name="book">
          <div class="resource-list">
            <div v-if="bookResources.length === 0" class="empty-data">
              <el-empty description="暂无书籍资料" />
            </div>
            <el-card
              v-for="resource in bookResources"
              :key="resource.id"
              class="resource-card"
              shadow="hover"
              @click="openResource(resource)"
            >
              <div class="resource-content">
                <div class="resource-icon book-icon">
                  <el-icon :size="40"><Document /></el-icon>
                </div>
                <div class="resource-info">
                  <h4 class="resource-title">{{ resource.title }}</h4>
                  <p class="resource-desc">{{ resource.description || '暂无描述' }}</p>
                  <span v-if="resource.file_size" class="resource-size">
                    {{ formatFileSize(resource.file_size) }}
                  </span>
                </div>
              </div>
            </el-card>
          </div>
        </el-tab-pane>

        <!-- 知识点列表 -->
        <el-tab-pane label="知识点列表" name="knowledge">
          <div class="knowledge-list">
            <div v-if="courseDetail.knowledge_points?.length === 0" class="empty-data">
              <el-empty description="暂无知识点" />
            </div>
            <el-card
              v-for="kp in courseDetail.knowledge_points"
              :key="kp.id"
              class="knowledge-card"
              shadow="hover"
              @click="goToKnowledge(kp.id)"
            >
              <div class="knowledge-content">
                <h4 class="knowledge-title">{{ kp.title }}</h4>
                <p class="knowledge-desc">{{ kp.content }}</p>
                <el-tag :type="getDifficultyTag(kp.difficulty)" size="small">
                  {{ kp.difficulty }}
                </el-tag>
              </div>
            </el-card>
          </div>
        </el-tab-pane>

        <!-- 配套习题 -->
        <el-tab-pane label="配套习题" name="exercise">
          <div class="exercise-list">
            <div v-if="courseDetail.exercises?.length === 0" class="empty-data">
              <el-empty description="暂无习题" />
            </div>
            <el-card
              v-for="exercise in courseDetail.exercises"
              :key="exercise.id"
              class="exercise-card"
              shadow="hover"
              @click="openExercise(exercise)"
            >
              <div class="exercise-content">
                <div class="exercise-header">
                  <h4 class="exercise-title">{{ exercise.title }}</h4>
                  <div class="exercise-meta">
                    <el-tag :type="getDifficultyTag(exercise.difficulty)" size="small">
                      {{ exercise.difficulty }}
                    </el-tag>
                    <el-tag type="info" size="small">{{ exercise.type }}</el-tag>
                    <span class="exercise-score">{{ exercise.score }}分</span>
                  </div>
                </div>
              </div>
            </el-card>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 视频播放弹窗 -->
    <el-dialog v-model="videoDialogVisible" title="视频学习" width="80%" :close-on-click-modal="false">
      <div v-if="currentVideo" class="video-player">
        <video
          ref="videoRef"
          :src="currentVideo.url"
          controls
          style="width: 100%; max-height: 500px"
          @timeupdate="handleVideoTimeUpdate"
          @ended="handleVideoEnded"
        />
      </div>
      <template #footer>
        <el-button @click="closeVideoDialog">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 返回按钮 -->
    <div class="back-button">
      <el-button type="primary" :icon="ArrowLeft" @click="goBack">
        返回学习中心
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, View, VideoPlay, Document, ArrowLeft } from '@element-plus/icons-vue'
import courseApi from '@/api/user/course.js'


const router = useRouter()
const route = useRoute()

// 默认封面
const defaultCover = 'https://via.placeholder.com/400x300?text=课程封面'

// 课程详情
const courseDetail = ref({})
const activeTab = ref('video')

// 视频播放
const videoDialogVisible = ref(false)
const currentVideo = ref(null)
const videoRef = ref(null)
const videoStartTime = ref(0)

// 计算属性：视频资源
const videoResources = computed(() => {
  return courseDetail.value.resources?.filter(r => r.type === 'video') || []
})

// 计算属性：书籍资料
const bookResources = computed(() => {
  return courseDetail.value.resources?.filter(r => r.type !== 'video') || []
})

// 加载课程详情
const loadCourseDetail = async () => {
  const courseId = route.params.id
  try {
    const res = await courseApi.getCourseDetail(courseId)
    if (res.code === 0) {
      courseDetail.value = res.data
    }
  } catch (error) {
    console.error('加载课程详情失败:', error)
    ElMessage.error('加载课程详情失败')
  }
}

// 开始学习
const startLearning = () => {
  if (videoResources.value.length > 0) {
    playVideo(videoResources.value[0])
  } else if (courseDetail.value.knowledge_points?.length > 0) {
    activeTab.value = 'knowledge'
  } else {
    ElMessage.info('该课程暂无学习内容')
  }
}

// 播放视频
const playVideo = (resource) => {
  currentVideo.value = resource
  videoDialogVisible.value = true
  videoStartTime.value = Date.now()
}

// 视频时间更新
const handleVideoTimeUpdate = async () => {
  if (!videoRef.value || !currentVideo.value) return

  const currentTime = videoRef.value.currentTime
  const duration = videoRef.value.duration
  const progress = (currentTime / duration) * 100

  // 每10秒更新一次进度
  if (Math.floor(currentTime) % 10 === 0) {
    try {
      await courseApi.updateResourceProgress({
        resource_id: currentVideo.value.id,
        progress: progress,
        watch_duration: 10
      })
    } catch (error) {
      console.error('更新进度失败:', error)
    }
  }
}

// 视频播放结束
const handleVideoEnded = async () => {
  try {
    await courseApi.updateResourceProgress({
      resource_id: currentVideo.value.id,
      progress: 100,
      watch_duration: currentVideo.value.duration || 0
    })
    ElMessage.success('视频学习完成！')
  } catch (error) {
    console.error('更新进度失败:', error)
  }
}

// 关闭视频弹窗
const closeVideoDialog = () => {
  videoDialogVisible.value = false
  currentVideo.value = null
  // 刷新课程详情
  loadCourseDetail()
}

// 打开资源
const openResource = (resource) => {
  window.open(resource.url, '_blank')
}

// 跳转到知识点
const goToKnowledge = (pointId) => {
  // 可以跳转到RAG问答页面，传入知识点ID
  router.push(`/rag?point_id=${pointId}`)
}

// 打开习题
const openExercise = (exercise) => {
  // 可以跳转到习题页面，或者打开弹窗
  ElMessage.info('习题功能开发中')
}

// 返回
// 返回
const goBack = () => {
  // 🔥 修改：从 /learning-center 改为 /user/learning-center
  router.push('/user/learning-center')
}

// 工具函数
const formatDuration = (seconds) => {
  if (!seconds) return '未知时长'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) {
    return `${h}时${m}分${s}秒`
  }
  return `${m}分${s}秒`
}

const formatFileSize = (bytes) => {
  if (!bytes) return ''
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
}

const getDifficultyTag = (d) => {
  const map = { '简单': 'success', '中等': 'warning', '困难': 'danger' }
  return map[d] || 'info'
}

onMounted(() => {
  loadCourseDetail()
})
</script>

<style scoped>
.course-detail {
  padding: 20px;
}

.course-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 40px;
  border-radius: 12px;
  margin-bottom: 32px;
}

.header-content {
  display: flex;
  gap: 40px;
}

.course-cover {
  width: 320px;
  height: 240px;
  flex-shrink: 0;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

.course-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.course-info {
  flex: 1;
  color: #fff;
}

.course-title {
  margin: 0 0 16px;
  font-size: 28px;
  font-weight: 600;
}

.course-desc {
  margin: 0 0 24px;
  font-size: 16px;
  opacity: 0.9;
  line-height: 1.6;
}

.course-meta {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
  font-size: 14px;
  opacity: 0.9;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.meta-item.progress {
  background: rgba(255, 255, 255, 0.2);
  padding: 4px 12px;
  border-radius: 20px;
}

.course-actions {
  display: flex;
  gap: 16px;
}

.course-content {
  margin-bottom: 32px;
}

.resource-list,
.knowledge-list,
.exercise-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 20px;
}

.resource-card,
.knowledge-card,
.exercise-card {
  cursor: pointer;
  transition: all 0.3s;
}

.resource-card:hover,
.knowledge-card:hover,
.exercise-card:hover {
  transform: translateY(-2px);
}

.resource-content {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.resource-icon {
  width: 64px;
  height: 64px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.video-icon {
  background: linear-gradient(135deg, #ff6b6b, #ee5a52);
  color: #fff;
}

.book-icon {
  background: linear-gradient(135deg, #4facfe, #00f2fe);
  color: #fff;
}

.resource-info {
  flex: 1;
}

.resource-title {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.resource-desc {
  margin: 0 0 8px;
  font-size: 14px;
  color: #666;
}

.resource-duration,
.resource-size {
  font-size: 13px;
  color: #999;
}

.knowledge-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.knowledge-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.knowledge-desc {
  margin: 0;
  font-size: 14px;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.exercise-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.exercise-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  flex: 1;
}

.exercise-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.exercise-score {
  font-size: 14px;
  color: #666;
}

.empty-data {
  grid-column: 1 / -1;
  padding: 60px 0;
}

.video-player {
  display: flex;
  justify-content: center;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

.back-button {
  text-align: center;
  padding: 20px 0;
}
</style>