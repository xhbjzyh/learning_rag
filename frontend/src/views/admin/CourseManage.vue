<template>
  <div class="course-manage-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>课程管理</h2>
      <div class="btn-group">
        <!-- 新增：课程分类管理按钮 -->
        <el-button type="success" @click="openCategoryDialog">
          <el-icon><List /></el-icon> 课程分类管理
        </el-button>
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon> 新增课程
        </el-button>
      </div>
    </div>

    <!-- 搜索栏 -->
    <el-card class="search-card" shadow="hover">
      <el-form :model="queryParams" inline @keyup.enter="getList">
        <el-form-item label="课程标题">
          <el-input v-model="queryParams.title" placeholder="请输入课程标题" clearable />
        </el-form-item>
        <el-form-item label="课程分类">
          <el-select v-model="queryParams.category_id" placeholder="请选择分类" clearable style="width:180px">
            <el-option v-for="item in categoryList" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="难度">
          <el-select v-model="queryParams.difficulty" placeholder="请选择难度" clearable style="width:120px">
            <el-option label="简单" value="简单" />
            <el-option label="中等" value="中等" />
            <el-option label="困难" value="困难" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="getList">搜索</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 课程列表 -->
    <el-card class="table-card" shadow="hover">
      <el-table v-loading="loading" :data="tableData" border stripe>
        <el-table-column label="ID" prop="id" width="80" align="center" />
        <el-table-column label="课程封面" align="center" width="120">
          <template #default="{ row }">
            <el-image
              :src="row?.cover_url || 'https://picsum.photos/200/120'"
              fit="cover"
              style="width:80px;height:50px;border-radius:4px"
              preview-teleported
            />
          </template>
        </el-table-column>
        <el-table-column label="课程标题" prop="title" min-width="200" />
        <el-table-column label="讲师" prop="lecturer" width="120" align="center" />
        <el-table-column label="课程分类" width="150" align="center">
          <template #default="{ row }">
            {{ getCategoryName(row?.category_id) }}
          </template>
        </el-table-column>
        <el-table-column label="难度" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row?.difficulty === '简单' ? 'success' : row?.difficulty === '中等' ? 'warning' : 'danger'">
              {{ row?.difficulty || '未设置' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="发布状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="row?.is_published ? 'success' : 'info'">
              {{ row?.is_published ? '已发布' : '未发布' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" prop="create_time" width="180" align="center" />

        <!-- 🔥 这里已经修复：课程表格 操作列 + 详情按钮 -->
        <el-table-column label="操作" width="300" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="info" size="small" @click="handleDetail(row.id)">详情</el-button>
            <el-button type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" size="small" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>

      </el-table>

      <!-- 分页 -->
      <div class="pagination-box">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="size"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="getList"
          @current-change="getList"
        />
      </div>
    </el-card>

    <!-- 新增/编辑 课程弹窗 -->
    <el-dialog v-model="dialogVisible" title="课程信息" width="600px" append-to-body>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="课程标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入课程标题" />
        </el-form-item>
        <el-form-item label="课程封面">
          <el-upload
            :action="uploadUrl"
            :headers="uploadHeaders"
            :show-file-list="false"
            :on-success="handleUploadSuccess"
            accept="image/*"
          >
            <el-image
              :src="form.cover_url || 'https://picsum.photos/200/120'"
              fit="cover"
              style="width:120px;height:80px;border-radius:4px;cursor:pointer"
            />
          </el-upload>
        </el-form-item>
        <el-form-item label="讲师名称" prop="lecturer">
          <el-input v-model="form.lecturer" placeholder="请输入讲师名称" />
        </el-form-item>
        <el-form-item label="课程分类" prop="category_id">
          <el-select v-model="form.category_id" placeholder="请选择分类" style="width:100%">
            <el-option v-for="item in categoryList" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="课程难度" prop="difficulty">
          <el-select v-model="form.difficulty" style="width:100%">
            <el-option label="简单" value="简单" />
            <el-option label="中等" value="中等" />
            <el-option label="困难" value="困难" />
          </el-select>
        </el-form-item>
        <el-form-item label="课程描述">
          <el-input v-model="form.description" type="textarea" rows="3" placeholder="请输入课程描述" />
        </el-form-item>
        <el-form-item label="发布状态" prop="is_published">
          <el-switch v-model="form.is_published" active-text="已发布" inactive-text="未发布" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确认保存</el-button>
      </template>
    </el-dialog>

    <!-- ==================== 课程分类管理弹窗 ==================== -->
    <el-dialog v-model="categoryDialogVisible" title="课程分类管理" width="650px">
      <el-button type="primary" @click="openAddCategory" style="margin-bottom:12px">
        <el-icon><Plus /></el-icon> 新增分类
      </el-button>

      <el-table :data="categoryTreeData" border row-key="id" lazy>
        <el-table-column label="分类ID" prop="id" width="80" align="center" />
        <el-table-column label="分类名称" prop="name" min-width="150" />
        <el-table-column label="分类描述" prop="description" min-width="200" />
        <el-table-column label="层级" prop="level" width="80" align="center" />
        <el-table-column label="排序" prop="sort_order" width="80" align="center" />
        <el-table-column label="操作" width="200" align="center">
          <template #default="{ row }">
            <el-button type="text" @click="openEditCategory(row)">编辑</el-button>
            <el-button type="text" danger @click="handleDeleteCategory(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 新增/编辑 分类弹窗 -->
    <el-dialog v-model="categoryFormVisible" :title="categoryEdit ? '编辑分类' : '新增分类'" width="500px">
      <el-form :model="categoryForm" :rules="categoryRules" ref="categoryFormRef" label-width="100px">
        <el-form-item label="分类名称" prop="name">
          <el-input v-model="categoryForm.name" placeholder="请输入分类名称" />
        </el-form-item>
        <el-form-item label="父分类">
          <el-select v-model="categoryForm.parent_id" placeholder="请选择父分类" style="width:100%">
            <el-option label="一级分类" :value="0" />
            <el-option v-for="item in categoryList" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="categoryForm.description" type="textarea" rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="categoryForm.sort_order" :min="0" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="categoryFormVisible = false">取消</el-button>
        <el-button type="primary" :loading="categoryLoading" @click="submitCategory">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, List } from '@element-plus/icons-vue'
import courseApi from '@/api/admin/course.js'
import { getToken } from '@/utils/storage'


// 导入依赖（保持不变）

const handleDetail = (id) => {
  // 跳转到独立的根路由，新开标签页
  window.open(`/course-detail/${id}`, '_blank')
}


// ==================== 基础变量 ====================
const formRef = ref(null)
const loading = ref(false)
const dialogVisible = ref(false)
const submitLoading = ref(false)
const isEdit = ref(false)
const editId = ref(null)

const page = ref(1)
const size = ref(10)
const total = ref(0)

const tableData = ref([])
const categoryList = ref([])
const categoryTreeData = ref([])

const queryParams = reactive({
  title: '',
  category_id: null,
  difficulty: ''
})

const form = reactive({
  title: '',
  cover_url: '',
  lecturer: '',
  category_id: null,
  difficulty: '中等',
  description: '',
  is_published: true
})

const rules = {
  title: [{ required: true, message: '请输入课程标题', trigger: 'blur' }],
  category_id: [{ required: true, message: '请选择课程分类', trigger: 'change' }]
}

const uploadUrl = ref('/api/common/upload')
const uploadHeaders = ref({ Authorization: 'Bearer ' + getToken() })

// ==================== 课程分类管理 ====================
const categoryDialogVisible = ref(false)
const categoryFormVisible = ref(false)
const categoryEdit = ref(false)
const categoryLoading = ref(false)
const categoryFormRef = ref(null)
const editCategoryId = ref(null)

const categoryForm = reactive({
  name: '',
  description: '',
  parent_id: 0,
  sort_order: 0
})

const categoryRules = {
  name: [{ required: true, message: '请输入分类名称', trigger: 'blur' }]
}

// 树形结构扁平化
const flattenTree = (tree, result = []) => {
  tree.forEach(item => {
    result.push({ id: item.id, name: item.name })
    if (item.children && item.children.length) {
      flattenTree(item.children, result)
    }
  })
  return result
}

// 获取分类列表
const getCategoryList = async () => {
  try {
    const res = await courseApi.getCourseCategories()
    categoryTreeData.value = res.data
    categoryList.value = flattenTree(res.data)
  } catch (err) {
    ElMessage.error('获取课程分类失败')
  }
}

// 打开分类弹窗
const openCategoryDialog = () => {
  getCategoryList()
  categoryDialogVisible.value = true
}

// 新增分类
const openAddCategory = () => {
  categoryEdit.value = false
  editCategoryId.value = null
  Object.assign(categoryForm, { name: '', description: '', parent_id: 0, sort_order: 0 })
  categoryFormVisible.value = true
}

// 编辑分类
const openEditCategory = (row) => {
  categoryEdit.value = true
  editCategoryId.value = row.id
  Object.assign(categoryForm, row)
  categoryFormVisible.value = true
}

// 提交分类
const submitCategory = async () => {
  await categoryFormRef.value.validate()
  categoryLoading.value = true
  try {
    if (categoryEdit.value) {
      await courseApi.updateCourseCategory(editCategoryId.value, categoryForm)
      ElMessage.success('编辑成功')
    } else {
      await courseApi.createCourseCategory(categoryForm)
      ElMessage.success('新增成功')
    }
    categoryFormVisible.value = false
    getCategoryList()
  } catch (err) {
    ElMessage.error('操作失败')
  } finally {
    categoryLoading.value = false
  }
}

// 删除分类
const handleDeleteCategory = async (id) => {
  await ElMessageBox.confirm('删除后无法恢复，确定删除？', '提示', { type: 'warning' })
  try {
    await courseApi.deleteCourseCategory(id)
    ElMessage.success('删除成功')
    getCategoryList()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '删除失败')
  }
}

// ==================== 课程列表 ====================
const getList = async () => {
  loading.value = true
  try {
    const params = { ...queryParams, page: page.value, size: size.value }
    const res = await courseApi.getCourseList(params)
    if (res.code === 0) {
      tableData.value = res.data.items || []
      total.value = res.data.total || 0
    } else {
      ElMessage.error(res.msg || '获取课程列表失败')
    }
  } catch (err) {
    console.error(err)
    ElMessage.error('获取课程列表失败')
  } finally {
    loading.value = false
  }
}

// 获取分类名称
const getCategoryName = (id) => {
  if (!id) return '未分类'
  const item = categoryList.value.find(i => i.id === id)
  return item ? item.name : '未分类'
}

// 重置搜索
const resetQuery = () => {
  queryParams.title = ''
  queryParams.category_id = null
  queryParams.difficulty = ''
  getList()
}

// 新增课程
const handleAdd = () => {
  isEdit.value = false
  editId.value = null
  Object.assign(form, {
    title: '', cover_url: '', lecturer: '', category_id: null,
    difficulty: '中等', description: '', is_published: true
  })
  dialogVisible.value = true
}

// 编辑课程
const handleEdit = (row) => {
  isEdit.value = true
  editId.value = row.id
  Object.assign(form, row)
  dialogVisible.value = true
}

// 上传成功
const handleUploadSuccess = (res) => {
  form.cover_url = res.data.url
  ElMessage.success('上传成功')
}

// 提交保存
const handleSubmit = async () => {
  await formRef.value.validate()
  submitLoading.value = true
  try {
    if (isEdit.value) {
      await courseApi.updateCourse(editId.value, form)
      ElMessage.success('修改成功')
    } else {
      await courseApi.createCourse(form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    getList()
  } catch (err) {
    ElMessage.error('保存失败')
  } finally {
    submitLoading.value = false
  }
}

// 删除课程
const handleDelete = async (id) => {
  await ElMessageBox.confirm('确定删除该课程吗？', '提示', { type: 'warning' })
  try {
    await courseApi.deleteCourse(id)
    ElMessage.success('删除成功')
    getList()
  } catch (err) {
    ElMessage.error('删除失败')
  }
}

// 初始化
onMounted(() => {
  getCategoryList()
  getList()
})
</script>

<style scoped>
.course-manage-container {
  padding: 20px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
}
.btn-group {
  display: flex;
  gap: 10px;
}
.search-card {
  margin-bottom: 20px;
}
.table-card {
  padding: 20px;
}
.pagination-box {
  margin-top: 20px;
  text-align: right;
}
</style>