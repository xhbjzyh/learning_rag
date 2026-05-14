<template>
  <div class="course-detail">
    <!-- 顶部课程信息 -->
    <div class="course-header">
      <div class="header-content">
        <div class="course-cover">
          <img :src="getFullImageUrl(courseDetail.cover_url)" :alt="courseDetail.title" />
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

        <!-- 配套习题 -->
        <el-tab-pane label="配套习题" name="exercise">
          <div class="exercise-header-actions">
            <el-button type="primary" :icon="Notebook" @click="goToWrongBook">
              查看我的错题本
            </el-button>
          </div>
          <div class="exercise-list">
            <el-empty v-if="exerciseList.length === 0" description="暂无习题" />
            <el-card
              v-for="exercise in exerciseList"
              :key="exercise.id"
              class="exercise-card"
              @click="openExercise(exercise)"
            >
              <div class="exercise-content">
                <div class="exercise-header">
                  <h4 class="exercise-title">
                    <el-icon><Document /></el-icon>
                    {{ getKnowledgePointName(exercise) }}
                  </h4>
                  <div class="exercise-meta">
                    <el-tag :type="getDifficultyTag(formatDifficulty(exercise.difficulty))" size="small">
                      {{ formatDifficulty(exercise.difficulty) }}
                    </el-tag>
                    <el-tag type="info" size="small">{{ formatExerciseType(exercise.type) }}</el-tag>
                    <span class="exercise-score">{{ exercise.score || 0 }}分</span>
                  </div>
                </div>
                <div v-if="exercise.knowledge_points && exercise.knowledge_points.length > 0" class="knowledge-tags">
                  <el-tag
                    v-for="kp in exercise.knowledge_points.slice(0, 3)"
                    :key="kp.id"
                    size="small"
                    type="success"
                    effect="plain"
                  >
                    {{ kp.title || kp.name }}
                  </el-tag>
                </div>
              </div>
            </el-card>
          </div>
        </el-tab-pane>

        <!-- 个性化推荐 -->
        <el-tab-pane label="个性化推荐" name="recommendation">
          <div class="recommendation-section">
            <!-- 头部操作栏 -->
            <div class="recommendation-header">
              <h3 class="section-title">
                <el-icon><TrendCharts /></el-icon>
                个性化学习建议
              </h3>
              <el-button
                type="primary"
                :icon="Refresh"
                :loading="loadingRecommendations || loadingMastery"
                @click="refreshRecommendations"
              >
                重新生成推荐
              </el-button>
            </div>

            <!-- 加载状态 -->
            <div v-if="loadingRecommendations || loadingMastery" class="loading-container">
              <el-skeleton :rows="5" animated />
            </div>

            <!-- 空状态 -->
            <el-empty v-else-if="combinedRecommendations.length === 0" description="暂无学习记录，开始学习吧！" />

            <!-- 推荐列表 -->
            <div v-else class="recommendation-list">
              <el-card
                v-for="item in combinedRecommendations"
                :key="item.knowledge_id"
                class="recommendation-card"
                shadow="hover"
              >
                <div class="card-content">
                  <!-- 左侧：知识点信息 -->
                  <div class="knowledge-info">
                    <h4 class="knowledge-title">{{ item.knowledge_title }}</h4>
                    <div class="knowledge-meta">
                      <el-tag :type="getDifficultyTag(item.difficulty)" size="small">
                        {{ formatDifficulty(item.difficulty) }}
                      </el-tag>
                      <el-tag :type="getMasteryTag(item.mastery_score)" size="small">
                        {{ item.mastery_level }}
                      </el-tag>
                    </div>
                  </div>

                  <!-- 中间：掌握情况 -->
                  <div class="mastery-details">
                    <div class="mastery-score">
                      <span class="score-label">综合掌握：</span>
                      <span class="score-value" :style="{ color: getProgressColor(item.mastery_score) }">
                        {{ item.mastery_score }}分
                      </span>
                    </div>
                    <el-progress
                      :percentage="item.mastery_score"
                      :color="getProgressColor(item.mastery_score)"
                      :stroke-width="8"
                    />
                    <div class="dimension-scores" v-if="item.video_mastery !== undefined">
                      <span>视频：{{ item.video_mastery }}分</span>
                      <span>习题：{{ item.exercise_mastery }}分</span>
                    </div>
                  </div>

                  <!-- 右侧：推荐理由和操作 -->
                  <div class="recommendation-action">
                    <div class="reason-box" v-if="item.reason">
                      <el-icon><ChatDotRound /></el-icon>
                      <span class="reason-text">{{ item.reason }}</span>
                    </div>
                    <el-button
                      type="primary"
                      size="small"
                      @click="goToKnowledge(item.knowledge_id)"
                    >
                      去学习
                    </el-button>
                  </div>
                </div>
              </el-card>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 视频播放弹窗 -->
    <el-dialog
      v-model="videoDialogVisible"
      title="视频学习"
      width="90%"
      :close-on-click-modal="false"
      @closed="handleVideoDialogClosed"
    >
      <div v-if="currentVideo && videoDialogVisible" class="video-player">
        <video
          ref="videoRef"
          :src="`http://127.0.0.1:8000${currentVideo.url}`"
          controls
          style="width: 100%; height:75vh; object-fit:contain; background:#000"
          @timeupdate="handleVideoTimeUpdate"
          @ended="handleVideoEnded"
        />
      </div>
      <template #footer>
        <el-button @click="closeVideoDialog">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 知识点详情弹窗 -->
    <el-dialog v-model="knowledgeDialogVisible" title="知识点详情" width="60%">
      <div v-if="currentKnowledge" class="knowledge-detail">
        <h3>{{ currentKnowledge.title }}</h3>
        <div class="knowledge-content-detail">
          {{ currentKnowledge.content }}
        </div>
        <div class="knowledge-footer">
          <el-tag :type="getDifficultyTag(currentKnowledge.difficulty)">
            {{ currentKnowledge.difficulty }}
          </el-tag>
        </div>
      </div>
      <template #footer>
        <el-button @click="knowledgeDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="goToKnowledge(currentKnowledge.id)">
          去问答学习
        </el-button>
      </template>
    </el-dialog>

    <!-- 习题答题弹窗 -->
    <el-dialog v-model="exerciseDialogVisible" title="答题" width="70%" :close-on-click-modal="false">
      <div v-if="currentExercise" class="exercise-detail">
        <h3>{{ currentExercise.title || '未命名习题' }}</h3>
        <div class="exercise-info">
          <el-tag :type="getDifficultyTag(formatDifficulty(currentExercise.difficulty))">{{ formatDifficulty(currentExercise.difficulty) }}</el-tag>
          <el-tag type="info">{{ formatExerciseType(currentExercise.type) }}</el-tag>
          <span>分值：{{ currentExercise.score || 0 }}分</span>
        </div>

        <!-- 🔥 新增：答题结果显示区域 -->
        <div v-if="submitResult" class="submit-result" :class="submitResult.is_correct ? 'correct' : 'wrong'">
          <div class="result-header">
            <el-icon v-if="submitResult.is_correct" :size="24" color="#67c23a"><CircleCheck /></el-icon>
            <el-icon v-else :size="24" color="#f56c6c"><CircleClose /></el-icon>
            <span class="result-text">
              {{ submitResult.is_correct ? '回答正确！' : '回答错误' }}
            </span>
            <span v-if="!submitResult.is_correct" class="correct-answer">
              正确答案：{{ submitResult.correct_answer }}
            </span>
          </div>
          <div v-if="submitResult.analysis" class="result-analysis">
            <p class="analysis-title">📖 答案解析：</p>
            <p class="analysis-content">{{ submitResult.analysis }}</p>
          </div>
        </div>

        <div class="exercise-answer">
          <el-input
            v-if="currentExercise.type === 'short_answer'"
            v-model="userAnswer"
            type="textarea"
            :rows="5"
            placeholder="请输入答案"
            :disabled="!!submitResult"
          />
          <el-radio-group v-else-if="currentExercise.type === 'single_choice'" v-model="userAnswer" :disabled="!!submitResult">
            <el-radio
              :label="opt.option_label"
              v-for="(opt, idx) in currentExercise.options"
              :key="`radio-${idx}`"
            >
              {{ opt.option_label }}. {{ opt.option_content }}
            </el-radio>
          </el-radio-group>
          <el-checkbox-group v-else-if="currentExercise.type === 'multiple_choice'" v-model="userAnswer" :disabled="!!submitResult">
            <el-checkbox
              :label="opt.id"
              v-for="(opt, idx) in currentExercise.options"
              :key="`checkbox-${idx}`"
            >
              {{ opt.option_label }}. {{ opt.option_content }}
            </el-checkbox>
          </el-checkbox-group>
        </div>
      </div>
      <template #footer>
        <el-button @click="closeExerciseDialog">关闭</el-button>
        <el-button v-if="!submitResult" type="success" @click="submitExercise">提交答案</el-button>
        <el-button v-else type="primary" @click="nextExercise">下一题</el-button>
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
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, View, VideoPlay, Document, ArrowLeft, Notebook, TrendCharts, DataAnalysis, Refresh, ChatDotRound } from '@element-plus/icons-vue'
import courseApi from '@/api/user/course.js'
import learningSessionTracker from '@/utils/learningSession'

const router = useRouter()
const route = useRoute()

// 默认封面
const defaultCover = 'https://via.placeholder.com/400x300?text=课程封面'

// 🔥 新增：获取完整的图片URL
const getFullImageUrl = (url) => {
  if (!url) return defaultCover
  // 如果已经是完整URL，直接返回
  if (url.startsWith('http')) return url
  // 否则拼接基础URL
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  return `${baseUrl}${url}`
}

// 核心数据
const courseDetail = ref({})
const activeTab = ref('video')
const exerciseList = ref([])

// 视频播放
const videoDialogVisible = ref(false)
const currentVideo = ref(null)
const videoRef = ref(null)

// 知识点弹窗
const knowledgeDialogVisible = ref(false)
const currentKnowledge = ref(null)

// 习题弹窗
const exerciseDialogVisible = ref(false)
const currentExercise = ref(null)
const userAnswer = ref('')
const submitResult = ref(null)  // 🔥 新增：存储提交结果
const lastReportedProgress = ref(null)
const lastReportedTime = ref(null)

// 个性化推荐相关
const learningPath = ref([])
const masteryList = ref([])
const loadingRecommendations = ref(false)
const loadingMastery = ref(false)

// 合并推荐和掌握情况
const combinedRecommendations = computed(() => {
  // 以掌握情况为基础，合并学习路径的推荐理由
  const masteryMap = new Map()

  // 先添加所有掌握情况
  masteryList.value.forEach(item => {
    masteryMap.set(item.knowledge_id, { ...item })
  })

  // 再合并学习路径的推荐理由
  learningPath.value.forEach(item => {
    if (masteryMap.has(item.knowledge_id)) {
      // 已存在，更新推荐理由
      const existing = masteryMap.get(item.knowledge_id)
      existing.reason = item.reason
      existing.learning_path_order = item.mastery_score // 用于排序
    } else {
      // 不存在，添加新项
      masteryMap.set(item.knowledge_id, {
        ...item,
        mastery_level: item.level || '未学习'
      })
    }
  })

  // 转换为数组并按掌握度排序（低的优先）
  const result = Array.from(masteryMap.values())
  result.sort((a, b) => a.mastery_score - b.mastery_score)

  return result
})

// 计算属性
const videoResources = computed(() => courseDetail.value.resources?.filter(r => r.type === 'video') || [])
const bookResources = computed(() => courseDetail.value.resources?.filter(r => r.type !== 'video') || [])

// 获取知识点名称（用于习题列表展示）
const getKnowledgePointName = (exercise) => {
  if (!exercise.knowledge_points || exercise.knowledge_points.length === 0) {
    return `习题 ${exercise.id}`
  }
  // 取第一个知识点的标题
  const firstKp = exercise.knowledge_points[0]
  return firstKp.title || firstKp.name || `习题 ${exercise.id}`
}

// 加载个性化推荐
const loadRecommendations = async () => {
  const courseId = route.params.id
  loadingRecommendations.value = true

  try {
    const res = await courseApi.getCourseRecommendations(courseId)
    if (res.code === 0) {
      learningPath.value = res.data.learning_path || []
      console.log('学习路径数据:', learningPath.value)
    }
  } catch (error) {
    console.error('加载推荐失败:', error)
  } finally {
    loadingRecommendations.value = false
  }
}

// 加载知识点掌握情况
const loadMastery = async () => {
  const courseId = route.params.id
  loadingMastery.value = true

  try {
    const res = await courseApi.getCourseMastery(courseId)
    if (res.code === 0) {
      masteryList.value = res.data.mastery_list || []
      console.log('掌握情况数据:', masteryList.value)
    }
  } catch (error) {
    console.error('加载掌握情况失败:', error)
  } finally {
    loadingMastery.value = false
  }
}

// 重新生成推荐
const refreshRecommendations = async () => {
  await Promise.all([
    loadRecommendations(),
    loadMastery()
  ])
  ElMessage.success('推荐已更新')
}

// 加载习题列表
const loadExerciseList = async () => {
  const courseId = route.params.id
  try {
    const res = await courseApi.getExerciseList({
      course_id: courseId,
      page: 1,
      size: 10
    })
    if (res.code === 0) {
      exerciseList.value = res.data.items || []
      console.log('习题列表数据:', exerciseList.value) // 调试日志
    }
  } catch (error) {
    console.error('加载习题列表失败:', error)
    exerciseList.value = []
  }
}

// 加载课程详情
const loadCourseDetail = async () => {
  const courseId = route.params.id
  try {
    const res = await courseApi.getCourseDetail(courseId)
    if (res.code === 0) {
      courseDetail.value = res.data
      await loadExerciseList()
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
  console.log('🔥🔥🔥 playVideo 被调用', resource)
  console.log('🔥 courseDetail.value:', courseDetail.value)
  console.log('🔥 knowledge_points:', courseDetail.value.knowledge_points)
  console.log('🔥 course_knowledge_points:', courseDetail.value.course_knowledge_points)

  currentVideo.value = resource
  videoDialogVisible.value = true

  // 🔥 修复：开始跟踪学习会话
  let pointId = null

  // 优先使用知识点ID
  if (courseDetail.value.knowledge_points && courseDetail.value.knowledge_points.length > 0) {
    pointId = courseDetail.value.knowledge_points[0].id
    console.log('🔥 使用 knowledge_points[0].id:', pointId)
  } else if (courseDetail.value.course_knowledge_points && courseDetail.value.course_knowledge_points.length > 0) {
    pointId = courseDetail.value.course_knowledge_points[0].id
    console.log('🔥 使用 course_knowledge_points[0].id:', pointId)
  } else {
    // 🔥 兜底方案：使用课程ID作为临时知识点ID
    pointId = courseDetail.value.id
    console.warn('⚠️ 未找到知识点，使用课程ID作为临时ID:', pointId)
  }

  console.log('🔥 准备启动学习会话，pointId:', pointId)
  console.log('🔥 当前 tracker 状态:', learningSessionTracker)
  learningSessionTracker.startSession(pointId)
  console.log('🔥 startSession 调用后状态:', {
    isTracking: learningSessionTracker.isTracking,
    currentPointId: learningSessionTracker.currentPointId,
    sessionStartTime: learningSessionTracker.sessionStartTime
  })
}

// 视频进度更新
const handleVideoTimeUpdate = async () => {
  if (!videoRef.value || !currentVideo.value) return;
  const currentTime = videoRef.value.currentTime;
  const duration = videoRef.value.duration;
  const progress = (currentTime / duration) * 100;

  // 🔥 修复：改为每3秒上报一次，或者进度变化超过10%时上报
  const shouldReport = Math.floor(currentTime) % 3 === 0 ||
                       (lastReportedProgress.value && progress - lastReportedProgress.value >= 10);

  if (shouldReport) {
    try {
      // 🔥 关键修复：计算本次上报间隔的学习时长（秒）
      // 使用 Math.max(1, ...) 确保至少有1秒，避免0值
      const studyDuration = lastReportedTime.value
        ? Math.max(1, Math.round(currentTime - lastReportedTime.value))
        : 3;

      // 🔥 调试日志
      console.log('🔥 视频进度上报:', {
        currentTime,
        lastReportedTime: lastReportedTime.value,
        studyDuration,
        watch_position: Math.floor(currentTime),
        progress
      });

      await courseApi.updateResourceProgress({
        resource_id: currentVideo.value.id,
        progress: progress,
        watch_position: Math.floor(currentTime),  // 🔥 新增：传递观看位置（秒）
        study_duration: studyDuration  // 🔥 新增：传递学习时长
      });

      lastReportedProgress.value = progress;
      lastReportedTime.value = currentTime;  // 🔥 记录上次上报时间
    } catch (error) {
      console.error("更新进度失败", error);
    }
  }
};

// 视频结束
const handleVideoEnded = async () => {
  console.log('🔥 视频播放结束')

  try {
    const duration = videoRef.value?.duration || 0;

    // 🔥 修复：确保最后一段时长至少为1秒
    const lastDuration = Math.max(1, Math.round(duration - (lastReportedTime.value || 0)));

    // 🔥 修复：确保结束时上报100%进度
    await courseApi.updateResourceProgress({
      resource_id: currentVideo.value.id,
      progress: 100,
      is_finished: true,
      watch_position: Math.floor(duration),  // 🔥 传递总时长
      study_duration: lastDuration  // 🔥 最后一段时长
    });

    // 🔥 新增：视频学习完成，标记为已掌握
    console.log('🔥 视频学习完成，结束学习会话')
    await learningSessionTracker.endSession({
      isMastered: true,
      sessionType: 'study'
    });

    ElMessage.success("学习完成");

    // 🔥 刷新课程详情，更新进度显示
    loadCourseDetail();
  } catch (error) {
    console.error("更新进度失败", error);
  }
};

// 关闭视频弹窗
const closeVideoDialog = () => {
  console.log('🔥 closeVideoDialog 被调用')

  // 🔥 关键修复：先暂停并重置视频播放器
  if (videoRef.value) {
    videoRef.value.pause()
    videoRef.value.currentTime = 0
    console.log('视频已暂停并重置')
  }

  // 结束学习会话
  console.log('🔥 当前会话状态:', learningSessionTracker)
  learningSessionTracker.endSession({
    isMastered: false,
    sessionType: 'study'
  })

  // 🔥 直接关闭弹窗，v-if 会自动销毁视频元素
  videoDialogVisible.value = false
  currentVideo.value = null

  // 重新加载课程详情以更新进度
  loadCourseDetail()
}

// 🔥 新增：弹窗完全关闭后的回调（确保视频元素已销毁）
const handleVideoDialogClosed = () => {
  console.log('视频弹窗已完全关闭，视频元素已销毁')
  // 清空引用
  videoRef.value = null
  lastReportedTime.value = null
  lastReportedProgress.value = null
}

// 打开资源（文档/书籍）
const openResource = (resource) => {
  // 🔥 新增：开始跟踪文档学习会话
  if (courseDetail.value.knowledge_points && courseDetail.value.knowledge_points.length > 0) {
    const firstPointId = courseDetail.value.knowledge_points[0].id
    learningSessionTracker.startSession(firstPointId)
  } else if (courseDetail.value.course_knowledge_points && courseDetail.value.course_knowledge_points.length > 0) {
    const firstPointId = courseDetail.value.course_knowledge_points[0].id
    learningSessionTracker.startSession(firstPointId)
  }

  window.open(resource.url, '_blank')

  // 🔥 提示用户关闭文档后会自动记录学习时长
  ElMessage.info('请在学习完成后关闭文档窗口，系统将自动记录学习时长')

  // 🔥 监听窗口关闭事件（5秒后检查一次）
  setTimeout(() => {
    learningSessionTracker.endSession({
      isMastered: false,
      sessionType: 'study'
    })
  }, 5000)
}

// 打开知识点详情
const openKnowledge = (kp) => {
  currentKnowledge.value = kp
  knowledgeDialogVisible.value = true

  // 🔥 新增：开始跟踪知识点学习会话
  learningSessionTracker.startSession(kp.id)
}

// 跳转到知识点问答
const goToKnowledge = (pointId) => {
  // 🔥 结束当前学习会话
  learningSessionTracker.endSession({
    isMastered: false,
    sessionType: 'study'
  })

  router.push(`/rag?point_id=${pointId}`)
  knowledgeDialogVisible.value = false
}

// 打开习题
const openExercise = async (exercise) => {
  try {
    const res = await courseApi.getExerciseDetail(exercise.id)
    currentExercise.value = res.code === 0 ? res.data : exercise
  } catch (error) {
    currentExercise.value = exercise
  }
  userAnswer.value = currentExercise.value.type === 'multiple_choice' ? [] : ''
  exerciseDialogVisible.value = true

  // 🔥 新增：开始跟踪习题练习会话
  // 习题可能关联多个知识点，取第一个
  if (currentExercise.value.knowledge_points && currentExercise.value.knowledge_points.length > 0) {
    const firstPointId = currentExercise.value.knowledge_points[0].id
    learningSessionTracker.startSession(firstPointId)
  }
}

// 关闭习题弹窗
const closeExerciseDialog = () => {
  exerciseDialogVisible.value = false
  currentExercise.value = null
  userAnswer.value = ''
  submitResult.value = null  // 🔥 重置提交结果
}

// 提交习题答案
const submitExercise = async () => {
  console.log("答案：", userAnswer.value)
  const isEmpty = !userAnswer.value || (Array.isArray(userAnswer.value) && userAnswer.value.length === 0)
  if (isEmpty) {
    ElMessage.warning('请选择/填写答案！')
    return
  }

  try {
    const res = await courseApi.submitExerciseAnswer({
      exercise_id: currentExercise.value.id,
      user_answer: Array.isArray(userAnswer.value) ? userAnswer.value.join(',') : userAnswer.value.toString()
    })

    if (res.code === 0) {
      const result = res.data

      // 🔥 修复：保存提交结果（在对话框中显示）
      submitResult.value = {
        is_correct: result.is_correct,
        correct_answer: result.correct_answer,
        analysis: result.analysis,
        score: result.score
      }

      // 🔥 新增：根据答题结果结束学习会话
      await learningSessionTracker.endSession({
        isMastered: result.is_correct,
        sessionType: 'practice'
      })

      // 🔥 修复：不再立即关闭对话框，让用户看到结果
      // exerciseDialogVisible.value = false

      // 🔥 可选：仍然显示弹窗提示（但延迟更久）
      setTimeout(() => {
        ElMessageBox.alert(
          `<div style="text-align: left;">
            <p style="font-size: 16px; font-weight: bold; margin-bottom: 15px;">
              ${result.is_correct ? '✅ 回答正确！' : '❌ 回答错误'}
              ${result.is_correct ? `得分：${result.score}分` : `正确答案：${result.correct_answer}`}
            </p>
            ${result.analysis ? `
              <div style="margin-top: 15px; padding: 12px; background: #f5f7fa; border-radius: 4px;">
                <p style="margin: 0 0 8px; font-weight: 600; color: #409eff;">📖 答案解析：</p>
                <p style="margin: 0; line-height: 1.6;">${result.analysis}</p>
              </div>
            ` : '<p style="color: #999; margin-top: 10px;">暂无解析</p>'}
          </div>`,
          '答题结果',
          {
            dangerouslyUseHTMLString: true,
            confirmButtonText: '确定',
            type: result.is_correct ? 'success' : 'error',
            callback: () => {
              // 刷新习题列表（更新掌握情况）
              loadExerciseList()
            }
          }
        )
      }, 500)
    } else {
      ElMessage.error(res.msg || '提交失败')
    }
  } catch (error) {
    console.error('提交答案失败:', error)
    ElMessage.error('提交失败，请稍后重试')
  }
}

// 🔥 新增：下一题
const nextExercise = () => {
  // 关闭当前对话框
  exerciseDialogVisible.value = false
  submitResult.value = null

  // 找到当前习题的索引
  const currentIndex = exerciseList.value.findIndex(ex => ex.id === currentExercise.value.id)

  // 如果有下一题，打开它
  if (currentIndex >= 0 && currentIndex < exerciseList.value.length - 1) {
    openExercise(exerciseList.value[currentIndex + 1])
  } else {
    ElMessage.info('已经是最后一题了')
  }
}

// 返回
const goBack = () => {
  router.push('/user/learning-center')
}

// 跳转到错题本
const goToWrongBook = () => {
  router.push('/user/wrong-question-book')
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

const formatDifficulty = (diff) => {
  const map = { easy: '简单', medium: '中等', hard: '困难' }
  return map[diff] || diff
}

const formatExerciseType = (type) => {
  const map = { single_choice: '单选', multiple_choice: '多选', short_answer: '简答' }
  return map[type] || type
}

// 获取进度条颜色
const getProgressColor = (score) => {
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#e6a23c'
  return '#f56c6c'
}

// 获取掌握程度标签类型
const getMasteryTag = (score) => {
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'danger'
}

// 监听标签页切换
watch(() => activeTab.value, (newVal) => {
  if (newVal === 'exercise' && exerciseList.value.length === 0) loadExerciseList()
  if (newVal === 'recommendation') {
    if (learningPath.value.length === 0 && masteryList.value.length === 0) {
      refreshRecommendations()
    }
  }
})

// 页面卸载时自动保存学习会话
onUnmounted(() => {
  learningSessionTracker.endSession()
})

// 页面初始化
onMounted(() => {
  loadCourseDetail()
  loadRecommendations()
  loadMastery()
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
  padding: 16px;
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

.exercise-header-actions {
  margin-bottom: 16px;
  text-align: right;
}

.exercise-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  width: 100%;
}

.exercise-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.exercise-title .el-icon {
  color: #409eff;
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

.knowledge-tags {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* 个性化推荐样式 */
.recommendation-section {
  padding: 20px 0;
}

.recommendation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.section-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-title .el-icon {
  color: #409eff;
}

.loading-container {
  padding: 40px 20px;
}

.recommendation-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.recommendation-card {
  transition: all 0.3s;
}

.recommendation-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-content {
  display: flex;
  gap: 20px;
  align-items: center;
}

.knowledge-info {
  flex: 0 0 25%;
  min-width: 200px;
}

.knowledge-title {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.knowledge-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.mastery-details {
  flex: 1;
  min-width: 250px;
}

.mastery-score {
  margin-bottom: 8px;
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.score-label {
  font-size: 14px;
  color: #666;
}

.score-value {
  font-size: 20px;
  font-weight: 600;
}

.dimension-scores {
  margin-top: 8px;
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #999;
}

.recommendation-action {
  flex: 0 0 250px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.reason-box {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 10px;
  background: #f0f9ff;
  border-radius: 6px;
  border-left: 3px solid #409eff;
}

.reason-box .el-icon {
  color: #409eff;
  margin-top: 2px;
  flex-shrink: 0;
}

.reason-text {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
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

.knowledge-detail { padding: 10px 0; }
.knowledge-content-detail { margin: 20px 0; font-size: 16px; line-height: 1.8; color: #333; }
.knowledge-footer { text-align: right; }

.exercise-detail { padding: 10px 0; }
.exercise-info { margin: 10px 0 20px; display: flex; gap: 10px; align-items: center; }
.exercise-answer { margin-top: 20px; padding: 16px; background: #f8f9fa; border-radius: 8px; }

/* 🔥 新增：答题结果显示样式 */
.submit-result {
  margin: 20px 0;
  padding: 16px;
  border-radius: 8px;
  border-left: 4px solid;
}

.submit-result.correct {
  background: #f0f9ff;
  border-color: #67c23a;
}

.submit-result.wrong {
  background: #fef0f0;
  border-color: #f56c6c;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.result-text {
  font-size: 16px;
  font-weight: bold;
  flex: 1;
}

.correct-answer {
  color: #f56c6c;
  font-weight: 600;
}

.result-analysis {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e4e7ed;
}

.analysis-title {
  margin: 0 0 8px;
  font-weight: 600;
  color: #409eff;
}

.analysis-content {
  margin: 0;
  line-height: 1.8;
  color: #606266;
  white-space: pre-wrap;
}
</style>