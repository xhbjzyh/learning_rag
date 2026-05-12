<template>
  <div class="module-container">
    <div class="tool-bar">
      <el-button type="primary" @click="openAddDialog">新增文档</el-button>
    </div>

    <el-table
      :data="docList"
      border
      stripe
      style="width: 100%; margin-top: 15px"
      v-loading="loading"
    >
      <el-table-column label="ID" prop="id" width="80" align="center" />
      <el-table-column label="文档名称" prop="title" min-width="200" />
      <el-table-column label="文件类型" prop="file_type" width="120" align="center" />
      <el-table-column label="文件大小" prop="file_size" width="120" align="center">
        <template #default="{ row }">
          {{ row.file_size ? (row.file_size / 1024).toFixed(2) : 0 }} KB
        </template>
      </el-table-column>
      <!-- 仅展示：课程知识点关联 -->
      <el-table-column label="关联课程知识点" width="180" align="center">
        <template #default="{ row }">
          {{ row.course_knowledge_ids?.join(', ') || '未关联' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" align="center">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
          <el-button type="danger" size="small" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" title="文档信息" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="文档名称" prop="title">
          <el-input v-model="form.title" placeholder="请输入文档名称" />
        </el-form-item>

        <el-form-item label="上传文档" prop="file">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :show-file-list="true"
            :on-change="handleFileChange"
            accept=".pdf,.docx,.pptx,.xlsx"
          >
            <el-button type="primary">选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">支持 PDF/Word/PPT/Excel</div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item label="文件链接" prop="url">
          <el-input v-model="form.url" placeholder="自动填充文件路径" disabled />
        </el-form-item>

        <el-form-item label="文件类型" prop="file_type">
          <el-select v-model="form.file_type" placeholder="请选择文件类型">
            <el-option label="PDF" value="pdf" />
            <el-option label="Word" value="docx" />
            <el-option label="PPT" value="pptx" />
            <el-option label="Excel" value="xlsx" />
          </el-select>
        </el-form-item>

        <!-- 🔥 仅保留：课程知识点ID（唯一关联字段） -->
        <el-form-item label="关联课程知识点ID" prop="course_knowledge_ids">
          <el-input
            v-model="form.course_knowledge_ids"
            placeholder="例：1,2,3  多个用逗号分隔"
            clearable
          />
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
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import courseApi from '@/api/admin/course'

const props = defineProps({
  courseId: [String, Number],
})

const docList = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const formRef = ref(null)
const uploadRef = ref(null)
const isEdit = ref(false)

// 🔥 仅保留：课程知识点关联字段
const form = reactive({
  id: null,
  title: '',
  type: 'document',
  url: '',
  file_size: 0,
  file_type: '',
  is_published: true,
  course_knowledge_ids: '', // 仅课程知识点
})

const rules = {
  title: [{ required: true, message: '请输入文档名称', trigger: 'blur' }],
  file_type: [{ required: true, message: '请选择文件类型', trigger: 'change' }],
  url: [{ required: true, message: '请先上传文档', trigger: 'blur' }]
}

// 页面刷新/切换课程 自动加载列表
const getList = async () => {
  if (!props.courseId) return
  loading.value = true
  try {
    const res = await courseApi.getCourseMaterials(props.courseId, 'document')
    if (res.code === 0) {
      docList.value = res.data?.items || res.data || []
    }
  } catch (error) {
    ElMessage.error('获取文档列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => getList())
watch(() => props.courseId, () => getList())

// 文件选择自动填充路径
const handleFileChange = (file) => {
  form.url = `/static/resources/${file.name}`
  form.file_size = file.size
  ElMessage.success('文件选择成功')
}

// 新增弹窗
const openAddDialog = () => {
  isEdit.value = false
  Object.assign(form, {
    id: null, title: '', url: '', file_size: 0, file_type: '',
    course_knowledge_ids: ''
  })
  dialogVisible.value = true
}

// 编辑弹窗：仅回显课程知识点
const openEditDialog = (row) => {
  isEdit.value = true
  Object.assign(form, {
    ...row,
    course_knowledge_ids: row.course_knowledge_ids?.join(',') || '',
  })
  dialogVisible.value = true
}

// 🔥 核心提交：仅提交 课程知识点 给后端
// 🔥 修复：多知识点ID处理，过滤空值/0/无效数字
const submitForm = async () => {
  await formRef.value.validate()
  try {
    const params = {
      ...form,
      url: form.url || "/static/resources/default.pdf",
      file_type: form.file_type || "pdf",
      is_published: true,
      // 核心修复：支持 1,2,3 格式，自动过滤空值，绝不提交空数组
      course_knowledge_ids: form.course_knowledge_ids
        ? form.course_knowledge_ids
            .split(',')
            .map(item => Number(item.trim())) // 去空格+转数字
            .filter(kid => !isNaN(kid) && kid > 0) // 只保留有效ID
        : [] // 无输入则为空数组（主动清空）
    }

    if (isEdit.value) {
      await courseApi.updateCourseMaterial(form.id, params)
      ElMessage.success('更新成功')
    } else {
      await courseApi.createCourseMaterial(props.courseId, params)
      ElMessage.success('创建成功！')
    }

    dialogVisible.value = false
    getList()
  } catch (error) {
    ElMessage.error('操作失败')
    console.error(error)
  }
}

// 删除文档
const handleDelete = async (id) => {
  await ElMessageBox.confirm('确定删除？')
  try {
    await courseApi.deleteCourseMaterial(id)
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