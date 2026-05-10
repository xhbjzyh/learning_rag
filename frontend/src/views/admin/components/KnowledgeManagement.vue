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
      <el-table-column label="所属文档ID" prop="doc_id" width="120" align="center" />
      <el-table-column label="创建时间" prop="create_time" width="200" align="center" />
      <el-table-column label="操作" width="200" align="center">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
          <el-button type="danger" size="small" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新增/编辑知识点弹窗 -->
    <el-dialog v-model="dialogVisible" title="知识点信息" width="700px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="知识点标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入知识点标题" />
        </el-form-item>
        <el-form-item label="所属文档ID" prop="doc_id">
          <el-input v-model.number="form.doc_id" placeholder="请输入关联的知识库文档ID" />
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
          <el-input v-model="form.key_points" type="textarea" rows="2" placeholder="请输入核心要点（JSON格式）" />
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
// 🔥 直接用你已有的课程API，里面已经包含了知识点接口
import courseApi from '@/api/admin/course'

const props = defineProps({
  courseId: [String, Number],
  docId: [String, Number]
})

const knowledgeList = ref([])
const loading = ref(false)
const search = reactive({ keyword: '' })
const dialogVisible = ref(false)
const formRef = ref(null)
const isEdit = ref(false)

const form = reactive({
  id: null,
  doc_id: null,
  user_id: 1,
  title: '',
  content: '',
  key_points: '',
  difficulty: '中等',
  pre_knowledge: '',
  common_mistakes: '',
  related_topics: ''
})

const rules = {
  title: [{ required: true, message: '请输入知识点标题', trigger: 'blur' }],
  doc_id: [{ required: true, message: '请输入关联文档ID', trigger: 'blur' }],
  content: [{ required: true, message: '请输入知识点内容', trigger: 'blur' }],
  difficulty: [{ required: true, message: '请选择难度等级', trigger: 'change' }]
}

// 获取知识点列表
const getList = async () => {
  loading.value = true
  try {
    // 🔥 直接调用 courseApi 里的知识点接口
    const res = await courseApi.getKnowledgeList({
      keyword: search.keyword,
      page: 1,
      size: 100
    })
    if (res.code === 0) {
      knowledgeList.value = res.data.items || []
    }
  } catch (error) {
    ElMessage.error('获取知识点列表失败')
  } finally {
    loading.value = false
  }
}

// 打开新增弹窗
const openAddDialog = () => {
  isEdit.value = false
  Object.assign(form, {
    id: null,
    doc_id: props.docId || null,
    user_id: 1,
    title: '',
    content: '',
    key_points: '',
    difficulty: '中等',
    pre_knowledge: '',
    common_mistakes: '',
    related_topics: ''
  })
  dialogVisible.value = true
}

// 打开编辑弹窗
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
      // 🔥 调用 courseApi
      await courseApi.updateKnowledge(form.id, form)
      ElMessage.success('知识点更新成功')
    } else {
      // 🔥 调用 courseApi
      await courseApi.createKnowledge(form)
      ElMessage.success('知识点创建成功')
    }
    dialogVisible.value = false
    getList()
  } catch (error) {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  }
}

// 删除知识点
const handleDelete = async (id) => {
  await ElMessageBox.confirm('确认删除该知识点？删除后无法恢复', '提示')
  try {
    // 🔥 调用 courseApi
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
/* 沿用你现有页面的样式，保持统一 */
.module-container {
  padding: 10px;
}
.tool-bar {
  display: flex;
  align-items: center;
}
</style>