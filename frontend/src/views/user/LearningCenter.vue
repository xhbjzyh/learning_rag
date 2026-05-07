<template>
  <div class="learning-center">
    <h2 class="page-title">学习中心</h2>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- 习题练习 -->
      <el-tab-pane label="习题练习" name="exercise">
        <div class="exercise-header">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索习题..."
            style="width: 300px"
            clearable
          />
        </div>

        <div class="exercise-list">
          <div v-if="exerciseList.length === 0" class="empty-data">暂无习题</div>
          <el-card
            v-for="exercise in exerciseList"
            :key="exercise.id"
            class="exercise-card"
            shadow="hover"
          >
            <div class="exercise-title">
              <span class="title-text">{{ exercise.title }}</span>
              <el-tag :type="getDifficultyTag(exercise.difficulty)" size="small">
                {{ exercise.difficulty }}
              </el-tag>
            </div>
            <div class="exercise-options">
              <div v-for="(opt, index) in exercise.options" :key="opt.id" class="option-item">
                <span class="option-label">{{ String.fromCharCode(65 + index) }}.</span>
                <span class="option-content">{{ opt.option_content }}</span>
              </div>
            </div>
            <div class="footer">
              <el-button type="primary" @click="openExerciseDialog(exercise)">
                开始答题
              </el-button>
            </div>
          </el-card>
        </div>

        <el-pagination
          v-model:current-page="exercisePage"
          v-model:page-size="exerciseSize"
          :total="exerciseTotal"
          layout="prev, pager, next, jumper, ->, total"
          @change="loadExerciseList"
          class="pagination"
        />
      </el-tab-pane>

      <!-- 答题记录 -->
      <el-tab-pane label="我的答题记录" name="records">
        <div v-if="answerRecords.length === 0" class="empty-data">暂无答题记录</div>
        <el-table v-else :data="answerRecords" border stripe>
          <el-table-column label="习题题目" prop="exercise_title" min-width="300" />
          <el-table-column label="我的答案" prop="user_answer" />
          <el-table-column label="正确答案" prop="correct_answer" />
          <el-table-column label="是否正确" prop="is_correct">
            <template #default="{ row }">
              <el-tag :type="row.is_correct ? 'success' : 'danger'">
                {{ row.is_correct ? '正确' : '错误' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="答题时间" prop="create_time" />
        </el-table>
        <el-pagination
          v-model:current-page="recordPage"
          v-model:page-size="recordSize"
          :total="recordTotal"
          layout="prev, pager, next, jumper, ->, total"
          @change="loadAnswerRecords"
        />
      </el-tab-pane>

      <!-- 错题本 -->
      <el-tab-pane label="我的错题本" name="wrong">
        <div v-if="wrongQuestions.length === 0" class="empty-data">暂无错题记录</div>
        <el-table v-else :data="wrongQuestions" border stripe>
          <el-table-column label="习题题目" prop="exercise_title" min-width="300" />
          <el-table-column label="我的答案" prop="user_answer" />
          <el-table-column label="正确答案" prop="correct_answer" />
          <el-table-column label="错题时间" prop="create_time" />
          <el-table-column label="操作">
            <template #default="{ row }">
              <el-button type="success" size="small" @click="markMastered(row.id)">已掌握</el-button>
              <el-button type="danger" size="small" @click="removeWrong(row.id)">移除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-model:current-page="wrongPage"
          v-model:page-size="wrongSize"
          :total="wrongTotal"
          layout="prev, pager, next, jumper, ->, total"
          @change="loadWrongQuestions"
        />
      </el-tab-pane>
    </el-tabs>

    <!-- 答题弹窗 -->
    <el-dialog v-model="exerciseDialogVisible" title="习题答题" width="600px" :close-on-click-modal="false">
      <div v-if="currentExercise" class="exercise-dialog-content">
        <div class="dialog-title">
          <h3>{{ currentExercise.title }}</h3>
          <el-tag :type="getDifficultyTag(currentExercise.difficulty)" size="small">{{ currentExercise.difficulty }}</el-tag>
        </div>

        <el-radio-group v-model="selectedAnswer" class="dialog-options">
          <el-radio v-for="(opt, index) in currentExercise.options" :key="opt.id" :label="opt.option_label">
            {{ opt.option_label }}. {{ opt.option_content }}
          </el-radio>
        </el-radio-group>

        <div v-if="submitResult" class="submit-result">
          <el-alert :type="submitResult.is_correct ? 'success' : 'error'" :title="submitResult.is_correct ? '回答正确！' : '回答错误'" show-icon />
          <div class="result-detail">
            <p><strong>你的答案：</strong>{{ selectedAnswer }}</p>
            <p><strong>正确答案：</strong>{{ correctAnswer }}</p>
            <p><strong>解析：</strong>{{ currentExercise.analysis }}</p>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="closeDialog">关闭</el-button>
          <el-button type="primary" @click="submitExercise" :disabled="!selectedAnswer || submitResult">提交答案</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import learningCenterApi from '@/api/user/learningCenter.js'

const activeTab = ref('exercise')

// 习题
const exerciseList = ref([])
const exercisePage = ref(1)
const exerciseSize = ref(10)
const exerciseTotal = ref(0)
const searchKeyword = ref('')

// 答题记录
const answerRecords = ref([])
const recordPage = ref(1)
const recordSize = ref(10)
const recordTotal = ref(0)

// 错题本
const wrongQuestions = ref([])
const wrongPage = ref(1)
const wrongSize = ref(10)
const wrongTotal = ref(0)

// 弹窗
const exerciseDialogVisible = ref(false)
const currentExercise = ref(null)
const selectedAnswer = ref('')
const submitResult = ref(null)

// ==============================================
// 动态计算正确答案
// ==============================================
const correctAnswer = computed(() => {
  if (!currentExercise.value?.options) return ''
  const correct = currentExercise.value.options.find(item => item.is_correct)
  return correct ? correct.option_label : ''
})

// ==============================================
// 核心：补全缺失的「开始答题」函数
// ==============================================
const openExerciseDialog = async (exercise) => {
  try {
    // 重置状态
    selectedAnswer.value = ''
    submitResult.value = null
    // 直接使用列表数据
    currentExercise.value = exercise
    // 打开弹窗
    exerciseDialogVisible.value = true
  } catch (error) {
    ElMessage.error('加载习题失败')
  }
}

// 关闭弹窗重置状态
const closeDialog = () => {
  exerciseDialogVisible.value = false
  selectedAnswer.value = ''
  submitResult.value = null
}

// ==============================================
// 统一数据解析函数（修复核心问题）
// ==============================================
const parseResponse = (res) => {
  // 兼容两种格式：
  // 1. 标准格式：{ code: 0, data: { list: [], total: 0 } }
  // 2. 裸数据格式：{ list: [], total: 0 }
  if (res && res.code === 0 && res.data) return res.data
  if (res && res.list !== undefined) return res
  return { list: [], total: 0 }
}

// ==============================================
// 加载习题列表
// ==============================================
const loadExerciseList = async () => {
  try {
    const res = await learningCenterApi.getExerciseList({
      page: exercisePage.value,
      size: exerciseSize.value,
      keyword: searchKeyword.value
    })
    const data = parseResponse(res)
    exerciseList.value = data.list || []
    exerciseTotal.value = data.total || 0
    console.log('习题列表加载成功:', data)
  } catch (error) {
    console.error('加载习题失败:', error)
    ElMessage.error('加载习题失败')
    exerciseList.value = []
    exerciseTotal.value = 0
  }
}

// ==============================================
// 加载答题记录（修复核心问题）
// ==============================================
const loadAnswerRecords = async () => {
  try {
    console.log('开始加载答题记录...')
    const res = await learningCenterApi.getAnswerRecords({
      page: recordPage.value,
      size: recordSize.value
    })
    const data = parseResponse(res)
    answerRecords.value = data.list || []
    recordTotal.value = data.total || 0
    console.log('答题记录加载成功:', data)
  } catch (error) {
    console.error('加载答题记录失败:', error)
    ElMessage.error('加载答题记录失败')
    answerRecords.value = []
    recordTotal.value = 0
  }
}

// ==============================================
// 加载错题本（修复核心问题）
// ==============================================
const loadWrongQuestions = async () => {
  try {
    console.log('开始加载错题本...')
    const res = await learningCenterApi.getWrongQuestions({
      page: wrongPage.value,
      size: wrongSize.value
    })
    const data = parseResponse(res)
    wrongQuestions.value = data.list || []
    wrongTotal.value = data.total || 0
    console.log('错题本加载成功:', data)
  } catch (error) {
    console.error('加载错题本失败:', error)
    ElMessage.error('加载错题本失败')
    wrongQuestions.value = []
    wrongTotal.value = 0
  }
}

// ==============================================
// 提交答案（修复核心问题）
// ==============================================
const submitExercise = async () => {
  if (!selectedAnswer.value) {
    ElMessage.warning('请选择答案')
    return
  }
  try {
    // 1. 动态判断对错
    const isCorrect = correctAnswer.value === selectedAnswer.value
    // 2. 提交后端（包含完整参数）
    const submitData = {
      exercise_id: currentExercise.value.id,
      user_answer: selectedAnswer.value,
      answer_time: Date.now()// 修复：添加答题时间参数
    }
    console.log('提交答案:', submitData)
    const res = await learningCenterApi.submitAnswer(submitData)
    const data = parseResponse(res)
    console.log('提交成功:', data)

    // 3. 赋值结果
    submitResult.value = { is_correct: isCorrect }
    ElMessage.success(isCorrect ? '回答正确！' : '回答错误')

    // 4. 强制刷新记录（修复：添加延迟确保数据同步）
    setTimeout(() => {
      loadAnswerRecords()
      loadWrongQuestions()
    }, 300)
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error('提交失败')
  }
}

// 工具函数
const markMastered = async (id) => {
  try {
    console.log('标记已掌握:', id)
    const res = await learningCenterApi.markMastered(id)
    const data = parseResponse(res)
    ElMessage.success('操作成功')
    loadWrongQuestions()
  } catch (e) {
    console.error('标记失败:', e)
    ElMessage.error('操作失败')
  }
}
const removeWrong = async (id) => {
  try {
    console.log('移除错题:', id)
    const res = await learningCenterApi.removeWrongQuestion(id)
    const data = parseResponse(res)
    ElMessage.success('移除成功')
    loadWrongQuestions()
  } catch (e) {
    console.error('移除失败:', e)
    ElMessage.error('移除失败')
  }
}
const getDifficultyTag = (d) => {
  const map = { 简单: 'success', 中等: 'warning', 困难: 'danger' }
  return map[d] || 'info'
}

watch(searchKeyword, () => { exercisePage.value = 1; loadExerciseList() })
onMounted(() => {
  console.log('页面初始化，加载所有数据...')
  loadExerciseList()
  loadAnswerRecords()
  loadWrongQuestions()
})
</script>

<style scoped>
.page-title { margin: 0 0 20px; font-size: 20px; }
.exercise-header { margin-bottom: 20px; }
.exercise-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 20px; margin-bottom: 20px; }
.exercise-card { height: 100%; }
.exercise-title { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
.empty-data { text-align: center; padding: 40px 0; color: #999; }
.pagination { text-align: center; margin: 20px 0; }
.dialog-footer { display: flex; justify-content: flex-end; gap: 10px; }
</style>