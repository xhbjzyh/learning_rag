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
      <el-table-column label="关联习题ID" prop="exercise.exercise_id" width="150" align="center" />
      <el-table-column label="发布状态" prop="is_published" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_published ? 'success' : 'info'">
            {{ row.is_published ? '已发布' : '未发布' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" align="center">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
          <el-button type="danger" size="small" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" title="习题信息" width="500px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="习题名称" prop="title">
          <el-input v-model="form.title" placeholder="请输入习题名称" />
        </el-form-item>
        <el-form-item label="关联习题ID" prop="exercise.exercise_id">
          <el-input v-model.number="form.exercise.exercise_id" placeholder="请输入习题ID" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" rows="3" placeholder="请输入习题描述" />
        </el-form-item>
        <el-form-item label="发布状态" prop="is_published">
          <el-switch v-model="form.is_published" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
// ✅ 修复：默认导入API
import courseApi from '@/api/admin/course'

const props = defineProps({ courseId: [String, Number] })
const emit = defineEmits(['refresh'])

const exerciseList = ref([])
const loading = ref(false)
const search = reactive({ keyword: '' })
const dialogVisible = ref(false)
const formRef = ref(null)
const isEdit = ref(false)

const form = reactive({
  id: null,
  title: '',
  type: 'exercise',
  description: '',
  url: '',
  sort_order: 0,
  is_published: true,
  exercise: {
    exercise_id: 0
  },
  video: null,
  document: null,
  knowledge_ids: []
})

const rules = {
  title: [{ required: true, message: '请输入习题名称', trigger: 'blur' }],
  'exercise.exercise_id': [{ required: true, message: '请输入习题ID', trigger: 'blur' }]
}

// 获取列表
const getList = async () => {
  loading.value = true
  try {
    // ✅ 修复：API调用 + 变量名
    const res = await courseApi.getCourseMaterials(props.courseId, 'exercise')
    if (res.code === 0) {
      exerciseList.value = res.data || []
    }
  } catch (error) {
    ElMessage.error('获取习题列表失败')
  } finally {
    loading.value = false
  }
}

const openAddDialog = () => {
  isEdit.value = false
  Object.assign(form, {
    id: null,
    title: '',
    type: 'exercise',
    description: '',
    sort_order: 0,
    is_published: true,
    exercise: { exercise_id: 0 },
    video: null,
    document: null,
    knowledge_ids: []
  })
  dialogVisible.value = true
}

const openEditDialog = (row) => {
  isEdit.value = true
  Object.assign(form, JSON.parse(JSON.stringify(row)))
  dialogVisible.value = true
}

const submitForm = async () => {
  await formRef.value.validate()
  try {
    if (isEdit.value) {
      // ✅ 修复：API调用
      await courseApi.updateCourseMaterial(form.id, form)
      ElMessage.success('习题更新成功')
    } else {
      await courseApi.createCourseMaterial(props.courseId, form)
      ElMessage.success('习题创建成功')
    }
    dialogVisible.value = false
    getList()
  } catch (error) {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  }
}

const handleDelete = async (id) => {
  await ElMessageBox.confirm('确认删除该习题？删除后无法恢复', '提示')
  try {
    // ✅ 修复：API调用
    await courseApi.deleteCourseMaterial(id)
    ElMessage.success('删除成功')
    getList()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

defineExpose({ getList })
</script>