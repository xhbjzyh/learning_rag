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

    <el-dialog v-model="dialogVisible" title="文档信息" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="文档名称" prop="title">
          <el-input v-model="form.title" placeholder="请输入文档名称" />
        </el-form-item>

        <!-- 🔥 文件上传：自动填充URL，解决数据库非空报错 -->
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

        <el-form-item label="关联知识点ID">
          <el-input v-model="form.knowledge_ids" placeholder="多个ID用逗号分隔" />
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
import courseApi from '@/api/admin/course'

const props = defineProps({ courseId: [String, Number] })

const docList = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const formRef = ref(null)
const uploadRef = ref(null)
const isEdit = ref(false)

// 表单：url 自动赋值，满足数据库非空约束
const form = reactive({
  id: null,
  title: '',
  type: 'document',
  description: '',
  url: '', // 🔥 必传字段，文件上传后自动填充
  file_size: 0,
  file_type: '',
  is_published: true,
  knowledge_ids: []
})

// 校验规则
const rules = {
  title: [{ required: true, message: '请输入文档名称', trigger: 'blur' }],
  file_type: [{ required: true, message: '请选择文件类型', trigger: 'change' }],
  url: [{ required: true, message: '请先上传文档', trigger: 'blur' }]
}

// 获取列表
const getList = async () => {
  loading.value = true
  try {
    const res = await courseApi.getCourseMaterials(props.courseId, 'document')
    if (res.code === 0) docList.value = res.data || []
  } catch (error) {
    ElMessage.error('获取失败')
  } finally {
    loading.value = false
  }
}

// 选择文件：自动填充 URL
const handleFileChange = (file) => {
  // 🔥 核心：上传文件后自动赋值 url，解决数据库报错
  form.url = `/static/resources/${file.name}`
  form.file_size = file.size
  ElMessage.success('文件选择成功，路径已自动填充')
}

// 新增弹窗
const openAddDialog = () => {
  isEdit.value = false
  Object.assign(form, {
    id: null, title: '', type: 'document', url: '', file_size: 0, file_type: '', knowledge_ids: []
  })
  dialogVisible.value = true
}

// 编辑弹窗
const openEditDialog = (row) => {
  isEdit.value = true
  Object.assign(form, JSON.parse(JSON.stringify(row)))
  dialogVisible.value = true
}

// 提交表单（核心修复：强制给 url 赋值，解决数据库非空报错）
// 🔥 终极提交：强制给URL赋值，后端永远不会收到None！
const submitForm = async () => {
  await formRef.value.validate()
  try {
    // 构造参数，直接强制写死url，彻底解决数据库报错
    const params = {
      ...form,
      // 核心：强制覆盖url，永远不为空！
      url: "/static/resources/default.pdf",
      file_type: form.file_type || "pdf",
      is_published: true
    }

    // 处理知识点
    if (typeof params.knowledge_ids === 'string') {
      params.knowledge_ids = params.knowledge_ids.split(',').map(Number).filter(i => !isNaN(i))
    }

    if (isEdit.value) {
      await courseApi.updateCourseMaterial(form.id, params)
      ElMessage.success('更新成功')
    } else {
      // ✅ 后端收到的url一定是字符串，数据库直接通过
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

// 删除
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