<template>
  <div class="admin-user-manage">
    <h2 class="page-title">用户管理</h2>

    <el-tabs v-model="activeTab" type="border-card" class="manage-tabs">
      <!-- 1. 用户列表 -->
      <el-tab-pane label="用户列表" name="list">
        <div class="table-container" v-loading="loading.list">
          <el-table :data="userList" border stripe>
            <el-table-column label="用户ID" prop="id" width="80" />
            <el-table-column label="用户名" prop="username" min-width="100" />
            <el-table-column label="角色" prop="role_id" width="100">
              <template #default="{ row }">
                <el-tag :type="getRoleTag(row.role_id)" size="small">
                  {{ getRoleName(row.role_id) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" prop="is_active" width="100">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
                  {{ row.is_active ? '正常' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="注册时间" prop="create_time" min-width="100" />
            <el-table-column label="操作" width="420">
              <template #default="{ row }">
                <el-button type="primary" size="small" @click="viewUserDetail(row)">查看详情</el-button>
                <el-button type="warning" size="small" @click="openResetPasswordDialog(row)">重置密码</el-button>
                <el-button type="danger" size="small" @click="deleteUser(row.id)">删除</el-button>
                <el-button type="info" size="small" @click="viewUserAnswerRecords(row)">查看答题</el-button>
                <el-button type="success" size="small" @click="viewUserLearningRecords(row)">查看学习</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-model:current-page="userPage"
            v-model:page-size="userSize"
            :total="userTotal"
            layout="prev, pager, next, jumper, ->, total"
            @change="loadUserList"
            class="pagination"
          />
        </div>
      </el-tab-pane>

      <!-- 2. 答题记录 -->
      <el-tab-pane label="答题记录" name="answer">
        <!-- 🔥 新增：筛选提示条 -->
        <div class="filter-bar" v-if="currentViewUser">
          <el-alert
            :title="`当前查看：用户「${currentViewUser.username}」的答题记录`"
            type="info"
            show-icon
            :closable="true"
            @close="clearUserFilter"
            style="margin-bottom: 16px;"
          />
        </div>

        <div class="table-container" v-loading="loading.answer">
          <el-table :data="answerRecords" border stripe>
            <el-table-column label="记录ID" prop="id" width="80" />
            <el-table-column label="用户ID" prop="user_id" width="80" />
            <el-table-column label="习题ID" prop="exercise_id" width="100" />
            <el-table-column label="用户答案" prop="user_answer" />
            <el-table-column label="正确答案" prop="correct_answer" />
            <el-table-column label="是否正确" prop="is_correct" width="100">
              <template #default="{ row }">
                <el-tag :type="row.is_correct ? 'success' : 'danger'" size="small">
                  {{ row.is_correct ? '正确' : '错误' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="答题时间" prop="create_time" min-width="180" />
          </el-table>
        </div>
      </el-tab-pane>

      <!-- 3. 学习记录 -->
      <el-tab-pane label="学习记录" name="learning">
        <!-- 🔥 新增：筛选提示条 -->
        <div class="filter-bar" v-if="currentViewUser">
          <el-alert
            :title="`当前查看：用户「${currentViewUser.username}」的学习记录`"
            type="info"
            show-icon
            :closable="true"
            @close="clearUserFilter"
            style="margin-bottom: 16px;"
          />
        </div>

        <div class="table-container" v-loading="loading.learning">
          <el-table :data="learningRecords" border stripe>
            <el-table-column label="记录ID" prop="id" width="80" />
            <el-table-column label="用户ID" prop="user_id" width="80" />
            <el-table-column label="知识点ID" prop="point_id" width="100" />
            <el-table-column label="学习时长(秒)" prop="learn_duration" width="120" />
            <el-table-column label="是否完成" prop="is_finished" width="100">
              <template #default="{ row }">
                <el-tag :type="row.is_finished ? 'success' : 'warning'" size="small">
                  {{ row.is_finished ? '已完成' : '进行中' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="创建时间" prop="create_time" min-width="180" />
          </el-table>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 重置密码弹窗 -->
    <el-dialog v-model="resetPasswordDialogVisible" title="重置用户密码" width="400px">
      <el-form :model="resetPasswordForm" label-width="100px">
        <el-form-item label="用户名" disabled>
          <el-input v-model="resetPasswordForm.username" disabled />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="resetPasswordForm.new_password"
            type="password"
            placeholder="请输入新密码（6-20位）"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="resetPasswordDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmResetPassword" :loading="loading.reset">确认重置</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 用户详情弹窗 -->
    <el-dialog v-model="userDetailDialogVisible" title="用户详情" width="600px">
      <div v-if="currentUserDetail" class="detail-content">
        <div class="detail-item">
          <span class="label">用户ID：</span>
          <span class="value">{{ currentUserDetail.id }}</span>
        </div>
        <div class="detail-item">
          <span class="label">用户名：</span>
          <span class="value">{{ currentUserDetail.username }}</span>
        </div>
        <div class="detail-item">
          <span class="label">角色：</span>
          <span class="value">{{ getRoleName(currentUserDetail.role_id) }}</span>
        </div>
        <div class="detail-item">
          <span class="label">状态：</span>
          <span class="value">{{ currentUserDetail.is_active ? '正常' : '禁用' }}</span>
        </div>
        <div class="detail-item">
          <span class="label">注册时间：</span>
          <span class="value">{{ currentUserDetail.create_time }}</span>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="userDetailDialogVisible = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import adminUserApi from '@/api/admin/userManage.js'

// 标签页控制
const activeTab = ref('list')

// 🔥 新增：当前正在查看的用户
const currentViewUser = ref(null)

// 加载状态
const loading = ref({
  list: false,
  answer: false,
  learning: false,
  reset: false
})

// 用户列表数据
const userList = ref([])
const userPage = ref(1)
const userSize = ref(10)
const userTotal = ref(0)

// 答题记录数据
const answerRecords = ref([])

// 学习记录数据
const learningRecords = ref([])

// 重置密码弹窗
const resetPasswordDialogVisible = ref(false)
const resetPasswordForm = ref({
  user_id: null,
  username: '',
  new_password: ''
})

// 用户详情弹窗
const userDetailDialogVisible = ref(false)
const currentUserDetail = ref(null)

// ==============================================
// 工具函数
// ==============================================
const getRoleName = (roleId) => {
  const map = { 1: '超级管理员', 2: '审核员', 3: '普通用户' }
  return map[roleId] || '未知'
}

const getRoleTag = (roleId) => {
  const map = { 1: 'danger', 2: 'warning', 3: 'success' }
  return map[roleId] || 'info'
}

// ==============================================
// 数据加载函数（🔥 支持用户ID筛选）
// ==============================================
const loadUserList = async () => {
  loading.value.list = true
  try {
    const res = await adminUserApi.getUserList({
      page: userPage.value,
      size: userSize.value
    })
    if (res.code === 0 && res.data) {
      userList.value = res.data.items || []
      userTotal.value = res.data.total || 0
    }
  } catch (error) {
    console.error('加载用户列表失败:', error)
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value.list = false
  }
}

// 🔥 修改：支持传递用户ID，只加载该用户的答题记录
const loadAnswerRecords = async (userId = null) => {
  loading.value.answer = true
  try {
    const params = userId ? { user_id: userId } : {}
    const res = await adminUserApi.getAnswerRecords(params)
    if (res.code === 0 && res.data) {
      answerRecords.value = res.data || []
    }
  } catch (error) {
    console.error('加载答题记录失败:', error)
    ElMessage.error('加载答题记录失败')
  } finally {
    loading.value.answer = false
  }
}

// 🔥 修改：支持传递用户ID，只加载该用户的学习记录
const loadLearningRecords = async (userId = null) => {
  loading.value.learning = true
  try {
    const params = userId ? { user_id: userId } : {}
    const res = await adminUserApi.getLearningRecords(params)
    if (res.code === 0 && res.data) {
      learningRecords.value = res.data || []
    }
  } catch (error) {
    console.error('加载学习记录失败:', error)
    ElMessage.error('加载学习记录失败')
  } finally {
    loading.value.learning = false
  }
}

// ==============================================
// 操作函数
// ==============================================
// 查看用户详情
const viewUserDetail = async (row) => {
  try {
    const res = await adminUserApi.getUserDetail(row.id)
    if (res.code === 0 && res.data) {
      currentUserDetail.value = res.data
      userDetailDialogVisible.value = true
    }
  } catch (error) {
    console.error('获取用户详情失败:', error)
    ElMessage.error('获取用户详情失败')
  }
}

// 打开重置密码弹窗
const openResetPasswordDialog = (row) => {
  resetPasswordForm.value = {
    user_id: row.id,
    username: row.username,
    new_password: ''
  }
  resetPasswordDialogVisible.value = true
}

// 确认重置密码
const confirmResetPassword = async () => {
  if (!resetPasswordForm.value.new_password) {
    ElMessage.warning('请输入新密码')
    return
  }
  if (resetPasswordForm.value.new_password.length < 6 || resetPasswordForm.value.new_password.length > 20) {
    ElMessage.warning('密码长度需在6-20位之间')
    return
  }

  loading.value.reset = true
  try {
    await adminUserApi.resetPassword({
      user_id: resetPasswordForm.value.user_id,
      new_password: resetPasswordForm.value.new_password
    })
    ElMessage.success('密码重置成功')
    resetPasswordDialogVisible.value = false
  } catch (error) {
    console.error('重置密码失败:', error)
    ElMessage.error('重置密码失败')
  } finally {
    loading.value.reset = false
  }
}

// 删除用户
const deleteUser = async (userId) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除该用户吗？删除后无法恢复！',
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await adminUserApi.deleteUser(userId)
    ElMessage.success('用户删除成功')
    loadUserList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除用户失败:', error)
      ElMessage.error('删除用户失败')
    }
  }
}

// 🔥 新增：查看指定用户的答题记录（后端筛选，更高效）
const viewUserAnswerRecords = (row) => {
  currentViewUser.value = row
  activeTab.value = 'answer'
  // 直接传递用户ID给后端，只加载该用户的数据
  loadAnswerRecords(row.id)
}

// 🔥 新增：查看指定用户的学习记录（后端筛选，更高效）
const viewUserLearningRecords = (row) => {
  currentViewUser.value = row
  activeTab.value = 'learning'
  // 直接传递用户ID给后端，只加载该用户的数据
  loadLearningRecords(row.id)
}

// 🔥 新增：清除用户筛选，查看所有记录
const clearUserFilter = () => {
  currentViewUser.value = null
  // 重新加载所有记录
  if (activeTab.value === 'answer') {
    loadAnswerRecords()
  } else if (activeTab.value === 'learning') {
    loadLearningRecords()
  }
}

// 监听标签页切换
watch(activeTab, (newTab) => {
  if (newTab === 'answer') {
    // 如果有当前查看的用户，只加载该用户的记录
    loadAnswerRecords(currentViewUser.value?.id)
  } else if (newTab === 'learning') {
    // 如果有当前查看的用户，只加载该用户的记录
    loadLearningRecords(currentViewUser.value?.id)
  } else if (newTab === 'list') {
    // 切换回用户列表时清除筛选
    currentViewUser.value = null
  }
})

// 页面初始化
onMounted(() => {
  loadUserList()
})
</script>

<style scoped>
.page-title {
  margin: 0 0 24px;
  color: #303133;
  font-size: 22px;
  font-weight: 600;
}

.table-container {
  min-height: 400px;
}

.pagination {
  text-align: center;
  margin: 20px 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.detail-item .label {
  font-size: 14px;
  color: #606266;
  width: 100px;
  font-weight: 500;
}

.detail-item .value {
  font-size: 14px;
  color: #303133;
}

.filter-bar {
  margin-bottom: 16px;
}
</style>