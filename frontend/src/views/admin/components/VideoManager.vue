<template>
  <div class="module-container">
    <div class="tool-bar">
      <el-button type="primary" @click="openAddDialog">新增视频</el-button>
      <el-input
        v-model="search.keyword"
        placeholder="搜索视频名称"
        style="width: 260px; margin-left: 10px"
        @keyup.enter="getList"
        clearable
      />
    </div>

    <el-table
      :data="videoList"
      border
      stripe
      style="width: 100%; margin-top: 15px"
      v-loading="loading"
    >
      <el-table-column label="ID" prop="id" width="80" align="center" />
      <el-table-column label="视频名称" prop="title" min-width="200" />
      <el-table-column label="文件类型" prop="file_type" width="120" align="center" />
      <el-table-column label="文件大小" prop="file_size" width="120" align="center">
        <template #default="{ row }">
          {{ row.file_size ? (row.file_size / 1024 / 1024).toFixed(2) : 0 }} MB
        </template>
      </el-table-column>
      <el-table-column label="视频时长" prop="duration" width="120" align="center">
        <template #default="{ row }">
          {{ row.duration ? Math.floor(row.duration / 60) + '分' + (row.duration % 60) + '秒' : '0秒' }}
        </template>
      </el-table-column>
      <el-table-column label="关联课程知识点" width="180" align="center">
        <template #default="{ row }">
          {{ row.course_knowledge_ids?.join(', ') || '未关联' }}
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

    <el-dialog v-model="dialogVisible" title="视频信息" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="视频名称" prop="title">
          <el-input v-model="form.title" placeholder="请输入视频名称" />
        </el-form-item>

        <!-- 🔥 修复：正确绑定file字段，添加limit限制 -->
        <el-form-item label="上传视频" prop="file">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :show-file-list="true"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :limit="1"
            accept=".mp4,.avi,.mov,.mkv,.flv,.wmv"
          >
            <el-button type="primary">选择视频文件</el-button>
            <template #tip>
              <div class="el-upload__tip">支持 MP4/AVI/MOV/MKV/FLV/WMV 格式</div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item label="文件链接" prop="url">
          <el-input v-model="form.url" placeholder="自动填充文件路径" disabled />
        </el-form-item>

        <el-form-item label="文件类型" prop="file_type">
          <el-select v-model="form.file_type" placeholder="请选择文件类型">
            <el-option label="MP4" value="mp4" />
            <el-option label="AVI" value="avi" />
            <el-option label="MOV" value="mov" />
            <el-option label="MKV" value="mkv" />
          </el-select>
        </el-form-item>

        <el-form-item label="视频时长" prop="duration">
          <el-input v-model.number="form.duration" placeholder="单位：秒" />
        </el-form-item>

        <el-form-item label="封面图链接" prop="cover_url">
          <el-input v-model="form.cover_url" placeholder="请输入封面地址（可选）" />
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" rows="3" placeholder="请输入视频描述" />
        </el-form-item>

        <!-- 统一：课程知识点关联 -->
        <el-form-item label="关联课程知识点ID" prop="course_knowledge_ids">
          <el-input
            v-model="form.course_knowledge_ids"
            placeholder="例：1,2,3  多个用逗号分隔"
            clearable
          />
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
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import courseApi from '@/api/admin/course'

const props = defineProps({
  courseId: [String, Number],
})

const emit = defineEmits(['refresh'])
const videoList = ref([])
const loading = ref(false)
const search = reactive({ keyword: '' })
const dialogVisible = ref(false)
const formRef = ref(null)
const uploadRef = ref(null)
const isEdit = ref(false)

// 🔥 修复：添加file字段，用于表单校验
const form = reactive({
  id: null,
  title: '',
  type: 'video', // 固定视频类型
  description: '',
  url: '',
  file: null, // 🔥 新增：存储选中的文件对象
  file_size: 0,
  file_type: '',
  duration: 0,
  cover_url: '',
  sort_order: 0,
  is_published: true,
  course_knowledge_ids: '',
  // 废弃旧结构
  video: null,
  document: null,
  exercise: null,
  knowledge_ids: []
})

// 🔥 修复：校验规则正确绑定file字段
const rules = {
  title: [{ required: true, message: '请输入视频名称', trigger: 'blur' }],
  file: [{ required: true, message: '请先上传视频文件', trigger: 'change' }],
  file_type: [{ required: true, message: '请选择文件类型', trigger: 'change' }],
  url: [{ required: true, message: '请先上传视频', trigger: 'blur' }]
}

// 统一列表加载逻辑
const getList = async () => {
  if (!props.courseId) return
  loading.value = true
  try {
    const res = await courseApi.getCourseMaterials(props.courseId, 'video')
    if (res.code === 0) {
      videoList.value = res.data?.items || res.data || []
    }
  } catch (error) {
    ElMessage.error('获取视频列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => getList())
watch(() => props.courseId, () => getList())

// 🔥 核心修复：正确处理文件选择，赋值给form.file
const handleFileChange = (file, fileList) => {
  // 只保留最新选择的文件
  if (fileList.length > 1) {
    fileList.splice(0, fileList.length - 1)
  }

  // 🔥 关键：将原始文件对象赋值给form.file，触发校验通过
  form.file = file.raw
  // 自动填充文件路径
  form.url = `/static/videos/${file.name}`
  // 自动填充文件大小
  form.file_size = file.size
  // 自动识别文件类型（提取扩展名）
  const ext = file.name.split('.').pop().toLowerCase()
  form.file_type = ext
  ElMessage.success('视频文件选择成功')
}

// 🔥 新增：处理文件删除，清空form.file
const handleFileRemove = () => {
  form.file = null
  form.url = ''
  form.file_size = 0
  form.file_type = ''
}

// 新增弹窗
const openAddDialog = () => {
  isEdit.value = false
  // 统一重置表单
  Object.assign(form, {
    id: null,
    title: '',
    type: 'video',
    description: '',
    url: '',
    file: null, // 🔥 重置文件字段
    file_size: 0,
    file_type: '',
    duration: 0,
    cover_url: '',
    sort_order: 0,
    is_published: true,
    course_knowledge_ids: ''
  })
  // 清空上传列表
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
  dialogVisible.value = true
}

// 编辑弹窗
const openEditDialog = (row) => {
  isEdit.value = true
  Object.assign(form, {
    ...row,
    // 统一知识点回显
    course_knowledge_ids: row.course_knowledge_ids?.join(',') || '',
    // 编辑模式不需要上传文件
    file: null
  })
  dialogVisible.value = true
}

// 🔥 修复：提交时排除file字段（后端不需要原始文件对象）
const submitForm = async () => {
  await formRef.value.validate()
  try {
    // 🔥 关键：排除file字段，只提交后端需要的参数
    const { file, ...params } = form
    const submitParams = {
      ...params,
      is_published: form.is_published,
      // 统一知识点处理
      course_knowledge_ids: form.course_knowledge_ids
        ? form.course_knowledge_ids
            .split(',')
            .map(item => Number(item.trim()))
            .filter(kid => !isNaN(kid) && kid > 0)
        : []
    }

    if (isEdit.value) {
      await courseApi.updateCourseMaterial(form.id, submitParams)
      ElMessage.success('视频更新成功')
    } else {
      await courseApi.createCourseMaterial(props.courseId, submitParams)
      ElMessage.success('视频创建成功！')
    }

    dialogVisible.value = false
    getList()
    emit('refresh')
  } catch (error) {
    ElMessage.error('操作失败')
    console.error(error)
  }
}

// 删除视频
const handleDelete = async (id) => {
  await ElMessageBox.confirm('确认删除该视频？删除后无法恢复', '提示')
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