<template>
  <div class="module-container">
    <div class="tool-bar">
      <el-button type="primary" @click="openAddDialog">新增习题</el-button>
      <el-input
        v-model="search.keyword"
        placeholder="搜索习题名称"
        style="width: 260px; margin-left: 10px"
        @keyup.enter="getList"
        clearable
      />
    </div>

    <el-table
      :data="exerciseList"
      border
      stripe
      style="width: 100%; margin-top: 15px"
      v-loading="loading"
    >
      <el-table-column label="ID" prop="id" width="80" align="center" />
      <el-table-column label="习题名称" prop="title" min-width="200" />
      <el-table-column label="题型" prop="type" width="120" align="center">
        <template #default="{ row }">
          <el-tag :type="row.type === 'single_choice' ? 'primary' : row.type === 'multiple_choice' ? 'success' : 'info'">
            {{ row.type === 'single_choice' ? '单选题' : row.type === 'multiple_choice' ? '多选题' : '判断题' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="关联知识点ID" width="200" align="center">
        <template #default="{ row }">
          {{ row.course_knowledge_ids?.join(', ') || '未关联' }}
        </template>
      </el-table-column>
      <el-table-column label="创建时间" prop="create_time" width="180" align="center" />
      <el-table-column label="操作" width="200" align="center">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
          <el-button type="danger" size="small" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" title="习题信息" width="700px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="习题名称" prop="title">
          <el-input v-model="form.title" placeholder="请输入习题名称" />
        </el-form-item>
        <el-form-item label="题型" prop="type">
          <el-select v-model="form.type" placeholder="请选择题型" style="width: 100%">
            <el-option label="单选题" value="single_choice" />
            <el-option label="多选题" value="multiple_choice" />
            <el-option label="判断题" value="true_false" />
          </el-select>
        </el-form-item>
        <el-form-item label="难度" prop="difficulty">
          <el-select v-model="form.difficulty" placeholder="请选择难度" style="width: 100%">
            <el-option label="简单" value="easy" />
            <el-option label="中等" value="medium" />
            <el-option label="困难" value="hard" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联知识库知识点ID" prop="knowledge_ids">
          <el-input
            v-model="form.knowledge_ids"
            placeholder="多个ID用逗号分隔，例如：1,2,3"
            clearable
          />
        </el-form-item>
        <el-form-item label="关联课程知识点ID" prop="course_knowledge_ids">
          <el-input
            v-model="form.course_knowledge_ids"
            placeholder="多个ID用逗号分隔，例如：1,2,3"
            clearable
          />
        </el-form-item>
        <el-form-item label="答案解析" prop="analysis">
          <el-input v-model="form.analysis" type="textarea" rows="3" placeholder="请输入答案解析" />
        </el-form-item>

        <!-- 选项管理（仅选择题需要） -->
        <template v-if="form.type === 'single_choice' || form.type === 'multiple_choice'">
          <el-divider>选项设置</el-divider>
          <el-form-item label="选项列表">
            <div v-for="(option, index) in form.options" :key="index" class="option-item">
              <el-input
                v-model="option.option_label"
                placeholder="标签(A/B/C/D)"
                style="width: 80px; margin-right: 10px"
              />
              <el-input
                v-model="option.option_content"
                placeholder="选项内容"
                style="flex: 1; margin-right: 10px"
              />
              <el-checkbox v-if="form.type === 'single_choice'" v-model="option.is_correct">正确</el-checkbox>
              <el-checkbox v-else v-model="option.is_correct">正确</el-checkbox>
              <el-button
                type="danger"
                size="small"
                @click="removeOption(index)"
                :disabled="form.options.length <= 2"
              >
                删除
              </el-button>
            </div>
            <el-button type="primary" size="small" @click="addOption" style="margin-top: 10px">
              添加选项
            </el-button>
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
// 🔥 新增：导入 onMounted 钩子（核心修复）
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import courseApi from '@/api/admin/course'

const props = defineProps({ courseId: [String, Number] })
const emit = defineEmits(['refresh'])

const exerciseList = ref([])
const loading = ref(false)
const search = reactive({ keyword: '' })
const dialogVisible = ref(false)
const formRef = ref(null)
const isEdit = ref(false)

// 🔥 表单补充后端必填字段（type/difficulty/analysis）
const form = reactive({
  id: null,
  title: '',
  type: 'single_choice', // 默认单选题（必填）
  difficulty: 'medium', // 使用英文难度
  analysis: '',
  knowledge_ids: '', // 知识库知识点ID
  course_knowledge_ids: '', // 课程知识点ID
  options: [
    { option_label: 'A', option_content: '', is_correct: false },
    { option_label: 'B', option_content: '', is_correct: false }
  ]
})

const rules = {
  title: [{ required: true, message: '请输入习题名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择题型', trigger: 'change' }],
  difficulty: [{ required: true, message: '请选择难度', trigger: 'change' }]
}

// 获取习题列表
const getList = async () => {
  loading.value = true
  try {
    const res = await courseApi.getCourseExercises(props.courseId)
    if (res.code === 0) {
      exerciseList.value = res.data || []
    }
  } catch (error) {
    ElMessage.error('获取习题列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 🔥 核心修复：页面挂载时自动调用获取列表
onMounted(() => {
  getList()
})

const openAddDialog = () => {
  isEdit.value = false
  Object.assign(form, {
    id: null,
    title: '',
    type: 'single_choice',
    difficulty: 'medium',
    analysis: '',
    knowledge_ids: '',
    course_knowledge_ids: '',
    options: [
      { option_label: 'A', option_content: '', is_correct: false },
      { option_label: 'B', option_content: '', is_correct: false }
    ]
  })
  dialogVisible.value = true
}

const openEditDialog = (row) => {
  isEdit.value = true
  Object.assign(form, {
    ...row,
    knowledge_ids: Array.isArray(row.knowledge_ids) ? row.knowledge_ids.join(',') : (row.knowledge_ids || ''),
    course_knowledge_ids: Array.isArray(row.course_knowledge_ids) ? row.course_knowledge_ids.join(',') : (row.course_knowledge_ids || ''),
    options: row.options && row.options.length > 0 ? row.options : [
      { option_label: 'A', option_content: '', is_correct: false },
      { option_label: 'B', option_content: '', is_correct: false }
    ]
  })
  dialogVisible.value = true
}

// 添加选项
const addOption = () => {
  const labels = ['A', 'B', 'C', 'D', 'E', 'F']
  const nextLabel = labels[form.options.length] || String.fromCharCode(65 + form.options.length)
  form.options.push({
    option_label: nextLabel,
    option_content: '',
    is_correct: false
  })
}

// 删除选项
const removeOption = (index) => {
  if (form.options.length > 2) {
    form.options.splice(index, 1)
  }
}

const submitForm = async () => {
  await formRef.value.validate()

  try {
    // 验证选项（仅选择题）
    if (form.type === 'single_choice' || form.type === 'multiple_choice') {
      const hasEmptyOption = form.options.some(opt => !opt.option_content.trim())
      if (hasEmptyOption) {
        ElMessage.error('请填写所有选项内容')
        return
      }

      const hasCorrect = form.options.some(opt => opt.is_correct)
      if (!hasCorrect) {
        ElMessage.error('请至少选择一个正确答案')
        return
      }
    }

    // 解析知识点ID（支持多个）
    const parseIds = (idStr) => {
      if (!idStr || idStr.trim() === '') return []
      return idStr.split(',')
        .map(item => item.trim())
        .filter(item => item !== '')
        .map(item => {
          const num = Number(item)
          return isNaN(num) ? null : num
        })
        .filter(item => item !== null)
    }

    const params = {
      id: form.id, // 🔥 编辑时必须包含id（后端必填）
      title: form.title,
      type: form.type,
      difficulty: form.difficulty,
      analysis: form.analysis || null,
      knowledge_ids: parseIds(form.knowledge_ids),
      course_knowledge_ids: parseIds(form.course_knowledge_ids),
      options: (form.type === 'single_choice' || form.type === 'multiple_choice')
        ? form.options.map((opt, index) => ({
            option_label: opt.option_label,
            option_content: opt.option_content,
            is_correct: opt.is_correct,
            order: index + 1
          }))
        : [] // 判断题不需要选项
    }

    console.log('提交的参数:', params) // 调试日志

    if (isEdit.value) {
      await courseApi.updateCourseExercise(form.id, params)
      ElMessage.success('习题更新成功')
    } else {
      await courseApi.createCourseExercise(props.courseId, params)
      ElMessage.success('习题创建成功')
    }
    dialogVisible.value = false
    getList()
    emit('refresh')
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error(error.response?.data?.detail || (isEdit.value ? '更新失败' : '创建失败'))
  }
}

const handleDelete = async (id) => {
  await ElMessageBox.confirm('确认删除该习题？删除后无法恢复', '提示')
  try {
    await courseApi.deleteCourseExercise(id)
    ElMessage.success('删除成功')
    getList()
  } catch (error) {
    ElMessage.error('删除失败')
    console.error(error)
  }
}

defineExpose({ getList })
</script>

<style scoped>
.module-container {
  padding: 15px;
}
.tool-bar {
  display: flex;
  align-items: center;
}
.option-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
  gap: 10px;
}
</style>