<template>
  <div class="module-container">
    <div class="tool-bar">
      <el-button type="primary" @click="openAddDialog">新增知识点</el-button>
      <el-input
        v-model="search.keyword"
        placeholder="搜索知识点标题"
        style="width: 260px; margin-left: 10px"
        @keyup.enter="getList"
        clearable
      />
    </div>

    <el-table
      :data="knowledgeList"
      border
      stripe
      style="width: 100%; margin-top: 15px"
      v-loading="loading"
    >
      <el-table-column label="知识点ID" prop="id" width="100" align="center" />
      <el-table-column label="知识点标题" prop="title" min-width="250" />
      <el-table-column label="难度等级" prop="difficulty" width="120" align="center">
        <template #default="{ row }">
          <el-tag :type="
            row.difficulty === '简单' ? 'success' :
            row.difficulty === '中等' ? 'warning' : 'danger'
          ">
            {{ row.difficulty }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="排序序号" prop="sort_order" width="120" align="center" />
      <el-table-column label="创建时间" prop="create_time" width="200" align="center" />
      <el-table-column label="操作" width="200" align="center">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
          <el-button type="danger" size="small" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" title="知识点信息" width="700px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="课程ID" prop="course_id" v-show="false">
          <el-input v-model.number="form.course_id" disabled />
        </el-form-item>

        <el-form-item label="知识点标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入知识点标题" />
        </el-form-item>

        <el-form-item label="排序序号" prop="sort_order">
          <el-input v-model.number="form.sort_order" placeholder="请输入排序序号" />
        </el-form-item>

        <el-form-item label="难度等级" prop="difficulty">
          <el-select v-model="form.difficulty" placeholder="请选择难度">
            <el-option label="简单" value="简单" />
            <el-option label="中等" value="中等" />
            <el-option label="困难" value="困难" />
          </el-select>
        </el-form-item>

        <el-form-item label="知识点内容" prop="content">
          <el-input v-model="form.content" type="textarea" rows="5" placeholder="请输入知识点详细内容" />
        </el-form-item>

        <el-form-item label="核心要点" prop="key_points">
          <!-- 🔥 修复：绑定为 form.key_points -->
          <el-input v-model="form.key_points" type="textarea" rows="2" placeholder="请输入核心要点" />
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
// 🔥 修复：导入 onMounted，页面刷新自动加载数据
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import courseApi from '@/api/admin/course'

const props = defineProps({
  courseId: [String, Number],
})

const knowledgeList = ref([])
const loading = ref(false)
const search = reactive({ keyword: '' })
const dialogVisible = ref(false)
const formRef = ref(null)
const isEdit = ref(false)

const form = reactive({
  id: null,
  course_id: null,
  title: '',
  content: '',
  key_points: '',
  difficulty: '中等',
  sort_order: 0
})

const rules = {
  course_id: [{ required: true, message: '课程ID不能为空', trigger: 'blur' }],
  title: [{ required: true, message: '请输入知识点标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入知识点内容', trigger: 'blur' }],
  difficulty: [{ required: true, message: '请选择难度等级', trigger: 'change' }]
}

// 获取列表（匹配API）
const getList = async () => {
  if (!props.courseId) return ElMessage.warning('请选择课程')
  loading.value = true
  try {
    const res = await courseApi.getKnowledgeList(props.courseId)
    if (res.code === 0) {
      knowledgeList.value = res.data || []
    }
  } catch (error) {
    ElMessage.error('获取知识点列表失败')
  } finally {
    loading.value = false
  }
}

// 🔥 核心修复：页面刷新/初始化时 自动加载知识点列表
onMounted(() => {
  getList()
})

// 打开新增
const openAddDialog = () => {
  isEdit.value = false
  Object.assign(form, {
    id: null,
    course_id: props.courseId,
    title: '',
    content: '',
    key_points: '',
    difficulty: '中等',
    sort_order: 0
  })
  dialogVisible.value = true
}

// 打开编辑
const openEditDialog = (row) => {
  isEdit.value = true
  Object.assign(form, JSON.parse(JSON.stringify(row)))
  dialogVisible.value = true
}

// 提交表单
const submitForm = async () => {
  await formRef.value.validate()
  try {
    if (isEdit.value) {
      await courseApi.updateKnowledge(form.id, form)
      ElMessage.success('更新成功')
    } else {
      await courseApi.createKnowledge(form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    getList()
  } catch (error) {
    console.error(error)
    ElMessage.error('操作失败')
  }
}

// 删除
const handleDelete = async (id) => {
  await ElMessageBox.confirm('确认删除？')
  try {
    await courseApi.deleteKnowledge(id)
    ElMessage.success('删除成功')
    getList()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

defineExpose({ getList })
</script>

<style scoped>
.module-container { padding: 10px; }
.tool-bar { display: flex; align-items: center; }
</style>