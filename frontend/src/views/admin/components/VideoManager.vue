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
      <el-table-column label="视频时长" prop="video.duration" width="120" align="center" />
      <el-table-column label="视频链接" prop="video.video_url" min-width="250" />
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
        <el-form-item label="视频链接" prop="video.video_url">
          <el-input v-model="form.video.video_url" placeholder="请输入视频地址" />
        </el-form-item>
        <el-form-item label="视频时长" prop="video.duration">
          <el-input v-model.number="form.video.duration" placeholder="单位：秒" />
        </el-form-item>
        <el-form-item label="封面图链接" prop="video.cover_url">
          <el-input v-model="form.video.cover_url" placeholder="请输入封面地址" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" rows="3" placeholder="请输入视频描述" />
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
// ✅ 关键：用默认导入，不写命名导入
import courseApi from '@/api/admin/course'

const props = defineProps({ courseId: [String, Number] })
const emit = defineEmits(['refresh'])

const videoList = ref([])
const loading = ref(false)
const search = reactive({ keyword: '' })
const dialogVisible = ref(false)
const formRef = ref(null)
const isEdit = ref(false)

// 表单数据（按API结构定义）
const form = reactive({
  id: null,
  title: '',
  type: 'video',
  description: '',
  url: '',
  sort_order: 0,
  is_published: true,
  video: {
    video_url: '',
    duration: 0,
    cover_url: ''
  },
  document: null,
  exercise: null,
  knowledge_ids: []
})

// 表单校验
const rules = {
  title: [{ required: true, message: '请输入视频名称', trigger: 'blur' }],
  'video.video_url': [{ required: true, message: '请输入视频链接', trigger: 'blur' }]
}

// ✅ 关键：调用时用 courseApi.xxx
const getList = async () => {
  loading.value = true
  try {
    const res = await courseApi.getCourseMaterials(props.courseId, 'video')
    if (res.code === 0) {
      videoList.value = res.data || []
    }
  } catch (error) {
    ElMessage.error('获取视频列表失败')
  } finally {
    loading.value = false
  }
}

// 新增
const openAddDialog = () => {
  isEdit.value = false
  // 重置表单
  Object.assign(form, {
    id: null,
    title: '',
    type: 'video',
    description: '',
    sort_order: 0,
    is_published: true,
    video: { video_url: '', duration: 0, cover_url: '' },
    document: null,
    exercise: null,
    knowledge_ids: []
  })
  dialogVisible.value = true
}

// 编辑
const openEditDialog = (row) => {
  isEdit.value = true
  // 深拷贝避免污染原数据
  Object.assign(form, JSON.parse(JSON.stringify(row)))
  dialogVisible.value = true
}

// 提交表单
const submitForm = async () => {
  await formRef.value.validate()
  try {
    if (isEdit.value) {
      await courseApi.updateCourseMaterial(form.id, form)
      ElMessage.success('视频更新成功')
    } else {
      await courseApi.createCourseMaterial(props.courseId, form)
      ElMessage.success('视频创建成功')
    }
    dialogVisible.value = false
    getList()
  } catch (error) {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  }
}

// 删除
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