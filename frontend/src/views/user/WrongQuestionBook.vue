<template>
  <div class="wrong-question-book">
    <h2 class="page-title">
      <el-icon><Notebook /></el-icon>
      我的错题本
    </h2>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon wrong-icon">
            <el-icon :size="32"><WarningFilled /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ total }}</div>
            <div class="stat-label">错题总数</div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon practice-icon">
            <el-icon :size="32"><Reading /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ practicedCount }}</div>
            <div class="stat-label">已练习</div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon mastered-icon">
            <el-icon :size="32"><CircleCheck /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ masteredCount }}</div>
            <div class="stat-label">已掌握</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-select v-model="filterDifficulty" placeholder="难度筛选" clearable style="width: 150px">
        <el-option label="简单" value="easy" />
        <el-option label="中等" value="medium" />
        <el-option label="困难" value="hard" />
      </el-select>
      <el-select v-model="filterType" placeholder="题型筛选" clearable style="width: 150px">
        <el-option label="单选题" value="single_choice" />
        <el-option label="多选题" value="multiple_choice" />
        <el-option label="简答题" value="short_answer" />
      </el-select>
      <el-button type="primary" :icon="Refresh" @click="loadWrongQuestions">刷新</el-button>
    </div>

    <!-- 错题列表 -->
    <div class="question-list">
      <el-empty v-if="wrongQuestions.length === 0 && !loading" description="暂无错题，继续保持！" />

      <el-skeleton v-if="loading" :rows="5" animated />

      <el-card
        v-else
        v-for="item in wrongQuestions"
        :key="item.id"
        class="question-card"
        shadow="hover"
      >
        <div class="question-header">
          <div class="question-meta">
            <el-tag :type="getDifficultyTag(item.difficulty)" size="small">
              {{ formatDifficulty(item.difficulty) }}
            </el-tag>
            <el-tag type="info" size="small">{{ formatType(item.type) }}</el-tag>
            <span class="course-name">{{ item.course_title }}</span>
          </div>
          <div class="question-actions">
            <el-button type="success" size="small" :icon="CircleCheck" @click="handleMaster(item)">
              已掌握
            </el-button>
            <el-button type="warning" size="small" :icon="MagicStick" @click="handleGeneratePractice(item)">
              AI专项练习
            </el-button>
            <el-button type="danger" size="small" :icon="Delete" @click="handleRemove(item)">
              删除
            </el-button>
          </div>
        </div>

        <div class="question-content">
          <h4 class="question-title">{{ item.exercise_title }}</h4>
          <div class="question-detail">
            <p><strong>题目：</strong>{{ item.question_content }}</p>
            <div v-if="item.options && item.options.length > 0" class="options-list">
              <strong>选项：</strong>
              <ul>
                <li v-for="opt in item.options" :key="opt.id">
                  {{ opt.option_label }}. {{ opt.option_content }}
                </li>
              </ul>
            </div>
            <p><strong>你的答案：</strong><span class="wrong-answer">{{ item.user_answer }}</span></p>
            <p><strong>正确答案：</strong><span class="correct-answer">{{ item.correct_answer }}</span></p>
            <p v-if="item.explanation"><strong>解析：</strong>{{ item.explanation }}</p>
          </div>
        </div>

        <div class="question-footer">
          <span class="error-time">
            <el-icon><Clock /></el-icon>
            错误时间：{{ formatTime(item.create_time) }}
          </span>
          <span class="practice-count">
            <el-icon><TrendCharts /></el-icon>
            练习次数：{{ item.practice_count || 0 }}
          </span>
        </div>
      </el-card>
    </div>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :total="total"
      :page-sizes="[10, 20, 50]"
      layout="total, sizes, prev, pager, next, jumper"
      @current-change="loadWrongQuestions"
      @size-change="handleSizeChange"
      class="pagination"
    />

    <!-- AI专项练习对话框 -->
    <el-dialog v-model="practiceDialogVisible" title="AI专项练习" width="70%" :close-on-click-modal="false">
      <div v-if="generating" class="generating-tip">
        <el-icon class="is-loading" :size="40"><Loading /></el-icon>
        <p>AI正在为你生成专属练习题...</p>
      </div>
      <div v-else-if="practiceQuestion" class="practice-content">
        <h3>{{ practiceQuestion.title }}</h3>
        <div class="practice-info">
          <el-tag :type="getDifficultyTag(practiceQuestion.difficulty)">
            {{ formatDifficulty(practiceQuestion.difficulty) }}
          </el-tag>
          <el-tag type="info">{{ formatType(practiceQuestion.type) }}</el-tag>
        </div>
        <div class="practice-question">
          <p class="question-text">{{ practiceQuestion.question }}</p>
          <el-radio-group v-if="practiceQuestion.type === 'single_choice'" v-model="practiceAnswer">
            <el-radio
              v-for="opt in practiceQuestion.options"
              :key="opt.id"
              :label="opt.option_label"
              class="option-item"
            >
              {{ opt.option_label }}. {{ opt.option_content }}
            </el-radio>
          </el-radio-group>
          <el-checkbox-group v-else-if="practiceQuestion.type === 'multiple_choice'" v-model="practiceAnswer">
            <el-checkbox
              v-for="opt in practiceQuestion.options"
              :key="opt.id"
              :label="opt.option_label"
              class="option-item"
            >
              {{ opt.option_label }}. {{ opt.option_content }}
            </el-checkbox>
          </el-checkbox-group>
          <el-input
            v-else
            v-model="practiceAnswer"
            type="textarea"
            :rows="4"
            placeholder="请输入答案"
          />
        </div>

        <!-- 新增：答题结果显示区域 -->
        <div v-if="showResult" class="result-section" :class="isCorrect ? 'correct' : 'wrong'">
          <div class="result-header">
            <el-icon v-if="isCorrect" :size="24" color="#67c23a"><CircleCheck /></el-icon>
            <el-icon v-else :size="24" color="#f56c6c"><CircleClose /></el-icon>
            <span class="result-text">{{ isCorrect ? '回答正确！' : '回答错误' }}</span>
          </div>
          <div v-if="!isCorrect" class="correct-answer">
            <strong>正确答案：</strong>{{ practiceQuestion.correct_answer }}
          </div>
          <div v-if="practiceQuestion.explanation" class="explanation">
            <strong>📖 答案解析：</strong>
            <p>{{ practiceQuestion.explanation }}</p>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="closePracticeDialog">关闭</el-button>
        <el-button
          v-if="!generating && practiceQuestion && !showResult"
          type="primary"
          @click="submitPracticeAnswer"
        >
          提交答案
        </el-button>
        <el-button
          v-if="showResult"
          type="success"
          @click="generateNextPractice"
        >
          再来一题
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Notebook,
  WarningFilled,
  Reading,
  CircleCheck,
  Refresh,
  MagicStick,
  Delete,
  Clock,
  TrendCharts,
  Loading
} from '@element-plus/icons-vue'
import courseApi from '@/api/user/course.js'

// 错题列表
const wrongQuestions = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 筛选条件
const filterDifficulty = ref('')
const filterType = ref('')

// 统计数据
const practicedCount = computed(() => {
  return wrongQuestions.value.filter(q => q.practice_count > 0).length
})

const masteredCount = computed(() => {
  return wrongQuestions.value.filter(q => q.is_mastered).length
})

// AI练习相关
const practiceDialogVisible = ref(false)
const generating = ref(false)
const practiceQuestion = ref(null)
const practiceAnswer = ref('')
const currentWrongId = ref(null)
const showResult = ref(false)
const isCorrect = ref(false)

// 加载错题列表
const loadWrongQuestions = async () => {
  loading.value = true
  try {
    const res = await courseApi.getWrongQuestionList({
      page: currentPage.value,
      size: pageSize.value
    })
    if (res.code === 0) {
      wrongQuestions.value = res.data.items || []
      total.value = res.data.total || 0
    }
  } catch (error) {
    console.error('加载错题列表失败:', error)
    ElMessage.error('加载错题列表失败')
  } finally {
    loading.value = false
  }
}

// 分页大小变化
const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
  loadWrongQuestions()
}

// 标记已掌握
const handleMaster = async (item) => {
  try {
    await ElMessageBox.confirm('确定将该题标记为已掌握吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'success'
    })

    await courseApi.markWrongMastered(item.id)
    ElMessage.success('标记成功！继续加油！')
    loadWrongQuestions()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('标记失败:', error)
      ElMessage.error('标记失败')
    }
  }
}

// 删除错题
const handleRemove = async (item) => {
  try {
    await ElMessageBox.confirm('确定从错题本中删除该题吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await courseApi.removeWrongQuestion(item.id)
    ElMessage.success('删除成功')
    loadWrongQuestions()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 生成AI专项练习
const handleGeneratePractice = async (item) => {
  currentWrongId.value = item.id
  practiceDialogVisible.value = true
  generating.value = true
  practiceQuestion.value = null
  practiceAnswer.value = ''

  try {
    const res = await courseApi.generatePracticeFromWrong(item.id)
    console.log('AI生成练习完整响应:', JSON.stringify(res, null, 2))

    if (res.code === 0) {
      // 后端返回格式：{code: 0, msg: "...", data: {target_type, target_id, exercise, difficulty}}
      let practiceData = res.data?.exercise || res.data

      if (!practiceData) {
        ElMessage.error('生成练习失败：未获取到题目数据')
        practiceDialogVisible.value = false
        return
      }

      console.log('原始题目数据:', JSON.stringify(practiceData, null, 2))

      // 标准化字段名（兼容不同的返回格式）
      practiceQuestion.value = {
        title: practiceData.title || '专项练习题',
        question: practiceData.question || practiceData.content || practiceData.question_content || practiceData.title || '',
        type: practiceData.type || practiceData.exercise_type || 'single_choice',
        difficulty: practiceData.difficulty || 'medium',
        options: practiceData.options || practiceData.choices || [],
        correct_answer: practiceData.correct_answer || practiceData.answer || '',
        explanation: practiceData.explanation || practiceData.analysis || ''
      }

      console.log('=== 题目数据检查 ===')
      console.log('题目标题:', practiceQuestion.value.title)
      console.log('题目内容:', practiceQuestion.value.question)
      console.log('题目内容长度:', practiceQuestion.value.question.length)
      console.log('题目类型:', practiceQuestion.value.type)
      console.log('选项数量:', practiceQuestion.value.options?.length || 0)
      console.log('标准化后的完整题目对象:', practiceQuestion.value)

      // 确保选项数据正确格式化
      if (practiceQuestion.value.options && practiceQuestion.value.options.length > 0) {
        practiceQuestion.value.options = practiceQuestion.value.options.map((opt, index) => ({
          id: opt.id || index + 1,
          option_label: opt.option_label || String.fromCharCode(65 + index), // A, B, C, D...
          option_content: opt.option_content || opt.content || opt.text || '',
          is_correct: opt.is_correct || false
        }))
        console.log('格式化后的选项:', practiceQuestion.value.options)
      } else {
        console.warn('没有选项数据')
      }

    } else {
      ElMessage.error(res.msg || '生成练习失败')
      practiceDialogVisible.value = false
    }
  } catch (error) {
    console.error('生成练习失败:', error)
    ElMessage.error('生成练习失败，请稍后重试')
    practiceDialogVisible.value = false
  } finally {
    generating.value = false
  }
}

// 提交练习答案
const submitPracticeAnswer = () => {
  if (!practiceAnswer.value || (Array.isArray(practiceAnswer.value) && practiceAnswer.value.length === 0)) {
    ElMessage.warning('请选择/填写答案')
    return
  }

  // 判断答案是否正确
  const userAnswer = Array.isArray(practiceAnswer.value)
    ? practiceAnswer.value.join(',')
    : practiceAnswer.value.toString()

  isCorrect.value = userAnswer === practiceQuestion.value.correct_answer
  showResult.value = true

  // 显示提示消息
  if (isCorrect.value) {
    ElMessage.success('🎉 回答正确！太棒了！')
  } else {
    ElMessage.error('❌ 回答错误，请查看答案解析')
  }
}

// 关闭练习对话框
const closePracticeDialog = () => {
  practiceDialogVisible.value = false
  practiceQuestion.value = null
  practiceAnswer.value = ''
  showResult.value = false
  isCorrect.value = false
  currentWrongId.value = null
}

// 生成下一题
const generateNextPractice = async () => {
  // 重置状态
  practiceAnswer.value = ''
  showResult.value = false
  isCorrect.value = false

  // 重新生成题目
  generating.value = true
  try {
    const res = await courseApi.generatePracticeFromWrong(currentWrongId.value)
    console.log('AI生成练习完整响应:', JSON.stringify(res, null, 2))

    if (res.code === 0) {
      let practiceData = res.data?.exercise || res.data

      if (!practiceData) {
        ElMessage.error('生成练习失败：未获取到题目数据')
        return
      }

      console.log('原始题目数据:', JSON.stringify(practiceData, null, 2))

      practiceQuestion.value = {
        title: practiceData.title || '专项练习题',
        question: practiceData.question || practiceData.content || practiceData.question_content || practiceData.title || '',
        type: practiceData.type || practiceData.exercise_type || 'single_choice',
        difficulty: practiceData.difficulty || 'medium',
        options: practiceData.options || practiceData.choices || [],
        correct_answer: practiceData.correct_answer || practiceData.answer || '',
        explanation: practiceData.explanation || practiceData.analysis || ''
      }

      console.log('格式化后的题目:', practiceQuestion.value)

      // 标准化选项格式
      if (practiceQuestion.value.options && practiceQuestion.value.options.length > 0) {
        practiceQuestion.value.options = practiceQuestion.value.options.map(opt => ({
          id: opt.id || Math.random(),
          option_label: opt.option_label || opt.label || opt.key || '',
          option_content: opt.option_content || opt.content || opt.text || '',
          is_correct: opt.is_correct || false
        }))
        console.log('格式化后的选项:', practiceQuestion.value.options)
      } else {
        console.warn('没有选项数据')
      }
    } else {
      ElMessage.error(res.msg || '生成练习失败')
    }
  } catch (error) {
    console.error('生成练习失败:', error)
    ElMessage.error('生成练习失败，请稍后重试')
  } finally {
    generating.value = false
  }
}

// 工具函数
const getDifficultyTag = (d) => {
  const map = { easy: 'success', medium: 'warning', hard: 'danger', 简单: 'success', 中等: 'warning', 困难: 'danger' }
  return map[d] || 'info'
}

const formatDifficulty = (diff) => {
  const map = { easy: '简单', medium: '中等', hard: '困难' }
  return map[diff] || diff
}

const formatType = (type) => {
  const map = { single_choice: '单选题', multiple_choice: '多选题', short_answer: '简答题' }
  return map[type] || type
}

const formatTime = (time) => {
  if (!time) return ''
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  loadWrongQuestions()
})
</script>

<style scoped>
.wrong-question-book {
  padding: 20px;
}

.page-title {
  margin: 0 0 24px;
  font-size: 24px;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  gap: 8px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-2px);
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
  color: #fff;
}

.wrong-icon {
  background: linear-gradient(135deg, #ff6b6b, #ee5a52);
}

.practice-icon {
  background: linear-gradient(135deg, #4facfe, #00f2fe);
}

.mastered-icon {
  background: linear-gradient(135deg, #43e97b, #38f9d7);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #999;
  margin-top: 4px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  align-items: center;
}

.question-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
}

.question-card {
  transition: all 0.3s;
}

.question-card:hover {
  transform: translateX(4px);
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.question-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.course-name {
  font-size: 14px;
  color: #666;
  margin-left: 8px;
}

.question-actions {
  display: flex;
  gap: 8px;
}

.question-content {
  margin-bottom: 16px;
}

.question-title {
  margin: 0 0 12px;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.question-detail {
  font-size: 14px;
  color: #666;
  line-height: 1.8;
}

.question-detail p {
  margin: 8px 0;
}

.options-list ul {
  margin: 8px 0;
  padding-left: 20px;
}

.options-list li {
  margin: 4px 0;
}

.wrong-answer {
  color: #f56c6c;
  font-weight: 500;
}

.correct-answer {
  color: #67c23a;
  font-weight: 500;
}

.question-footer {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #999;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.question-footer span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.pagination {
  display: flex;
  justify-content: center;
}

.generating-tip {
  text-align: center;
  padding: 40px 0;
}

.generating-tip p {
  margin-top: 16px;
  font-size: 16px;
  color: #666;
}

.practice-content h3 {
  margin: 0 0 16px;
  font-size: 18px;
  color: #333;
}

.practice-info {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}

.practice-question {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.practice-question p {
  margin: 0 0 16px;
  font-size: 15px;
  line-height: 1.8;
  color: #333;
}

.question-text {
  font-size: 16px;
  line-height: 1.8;
  color: #303133;
  margin-bottom: 20px;
  padding: 16px;
  background: #fff;
  border-left: 4px solid #409EFF;
  border-radius: 4px;
}

.option-item {
  display: block;
  margin: 12px 0;
  padding: 8px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.option-item:hover {
  background-color: #f5f7fa;
}
</style>