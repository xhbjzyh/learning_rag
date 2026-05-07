<template>
  <div class="auditor-manage">
    <h2 class="page-title">审核员管理</h2>

    <el-card class="table-card" shadow="hover">
      <div class="toolbar">
        <el-button type="primary" @click="openAddDialog">
          <el-icon><Plus /></el-icon>
          新增审核员
        </el-button>
      </div>

      <el-table
        :data="auditorList"
        border
        stripe
        v-loading="loading.list"
        class="data-table"
      >
        <el-table-column prop="id" label="审核员ID" width="100" align="center" />
        <el-table-column prop="username" label="用户名" min-width="150" />
        <el-table-column prop="role_id" label="角色" width="120" align="center">
          <template #default="{ row }">
            <el-tag type="warning" size="small">审核员</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="添加时间" width="180" />
        <el-table-column label="操作" width="120" align="center">
          <template #default="scope">
            <el-button
              size="small"
              type="danger"
              @click="handleDelete(scope.row)"
            >
              移除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page"
        v-model:page-size="size"
        :total="total"
        layout="prev, pager, next, jumper, ->, total"
        @change="loadAuditorList"
        class="pagination"
      />
    </el-card>

    <!-- 新增审核员弹窗 -->
    <el-dialog
      v-model="addDialogVisible"
      title="新增审核员"
      width="450px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="addFormRef"
        :model="addForm"
        :rules="addRules"
        label-width="80px"
        class="add-form"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="addForm.username"
            placeholder="请输入用户名（3-20个字符）"
            size="large"
            clearable
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="addForm.password"
            type="password"
            placeholder="请输入密码（至少6位）"
            size="large"
            show-password
            clearable
          />
        </el-form-item>

        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="addForm.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            size="large"
            show-password
            clearable
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="addDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            @click="handleSubmitAdd"
            :loading="loading.add"
          >
            确认添加
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import auditorManageApi from '@/api/admin/auditorManage.js'

// 数据状态
const auditorList = ref([])
const page = ref(1)
const size = ref(10)
const total = ref(0)

// 加载状态
const loading = ref({
  list: false,
  add: false
})

// 弹窗状态
const addDialogVisible = ref(false)
const addFormRef = ref(null)

// 表单数据
const addForm = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

// 表单验证规则
const validateConfirmPassword = (rule, value, callback) => {
  if (value !== addForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const addRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在3-20个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// ==============================================
// 数据加载函数
// ==============================================
const loadAuditorList = async () => {
  loading.value.list = true
  try {
    const res = await auditorManageApi.getAuditorList({
      page: page.value,
      size: size.value
    })
    if (res.code === 0 && res.data) {
      auditorList.value = res.data.items || []
      total.value = res.data.total || 0
    }
  } catch (error) {
    console.error('获取审核员列表失败:', error)
    ElMessage.error('获取审核员列表失败')
  } finally {
    loading.value.list = false
  }
}

// ==============================================
// 操作函数
// ==============================================
const openAddDialog = () => {
  addForm.username = ''
  addForm.password = ''
  addForm.confirmPassword = ''
  addFormRef.value?.resetFields()
  addDialogVisible.value = true
}

const handleSubmitAdd = async () => {
  if (!addFormRef.value) return

  await addFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value.add = true
      try {
        await auditorManageApi.createAuditor({
          username: addForm.username,
          password: addForm.password
        })
        ElMessage.success('审核员创建成功')
        addDialogVisible.value = false
        loadAuditorList()
      } catch (error) {
        console.error('创建审核员失败:', error)
        ElMessage.error(error.response?.data?.msg || '创建审核员失败')
      } finally {
        loading.value.add = false
      }
    }
  })
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要移除审核员「${row.username}」吗？`,
      '移除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    loading.value.list = true
    await auditorManageApi.deleteAuditor(row.id)
    ElMessage.success('移除成功')
    loadAuditorList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除审核员失败:', error)
      ElMessage.error(error.response?.data?.msg || '删除审核员失败')
    }
  } finally {
    loading.value.list = false
  }
}

// 页面初始化
onMounted(() => {
  loadAuditorList()
})
</script>

<style scoped>
.auditor-manage {
  padding: 24px;
}

.page-title {
  margin: 0 0 24px;
  color: #303133;
  font-size: 22px;
  font-weight: 600;
}

.table-card {
  border-radius: 8px;
}

.toolbar {
  margin-bottom: 16px;
}

.data-table {
  margin-bottom: 16px;
}

.pagination {
  display: flex;
  justify-content: flex-end;
}

.add-form {
  margin-top: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>