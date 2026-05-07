<template>
  <div class="personal-workspace">
    <h2 class="page-title">个人工作台</h2>

    <!-- 1. 用户信息卡片 -->
    <el-card class="info-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>个人信息</span>
          <el-tag size="small" type="success">已登录</el-tag>
        </div>
      </template>

      <div class="info-list">
        <div class="info-item">
          <span class="label">用户ID：</span>
          <span class="value">{{ userInfo.id || '-' }}</span>
        </div>
        <div class="info-item">
          <span class="label">用户名：</span>
          <span class="value">{{ userInfo.username || '-' }}</span>
        </div>
        <div class="info-item">
          <span class="label">角色ID：</span>
          <span class="value">{{ userInfo.role_id || '-' }}</span>
        </div>
        <div class="info-item">
          <span class="label">创建时间：</span>
          <span class="value">{{ formatDate(userInfo.create_time) || '-' }}</span>
        </div>
      </div>

      <div class="action-bar">
        <el-button type="primary" @click="openPasswordDialog">
          <el-icon><Lock /></el-icon>
          修改密码
        </el-button>
      </div>
    </el-card>

    <!-- 2. 修改密码弹窗 -->
    <el-dialog
      v-model="passwordDialogVisible"
      title="修改登录密码"
      width="450px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="旧密码" prop="old_password">
          <el-input
            v-model="passwordForm.old_password"
            type="password"
            placeholder="请输入旧密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="passwordForm.new_password"
            type="password"
            placeholder="请输入新密码（不少于6位）"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认新密码" prop="confirm_new_password">
          <el-input
            v-model="passwordForm.confirm_new_password"
            type="password"
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="passwordDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            :loading="submitLoading"
            @click="submitPasswordForm"
          >
            确认修改
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Lock } from '@element-plus/icons-vue'
import request from '@/api/index' // 你的项目封装的axios请求工具

// ====================== 1. 响应式变量定义 ======================
// 用户信息
const userInfo = ref({})
// 修改密码弹窗控制
const passwordDialogVisible = ref(false)
// 密码表单数据
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_new_password: ''
})
// 表单引用（用于验证）
const passwordFormRef = ref(null)
// 提交加载状态
const submitLoading = ref(false)

// ====================== 2. 表单验证规则 ======================
const formRules = reactive({
  old_password: [
    { required: true, message: '请输入旧密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirm_new_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
})

// ====================== 3. 工具函数 ======================
// 格式化时间
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 重置密码表单
const resetPasswordForm = () => {
  passwordFormRef.value?.resetFields()
  passwordForm.old_password = ''
  passwordForm.new_password = ''
  passwordForm.confirm_new_password = ''
}

// ====================== 4. 接口请求 ======================
/**
 * 获取当前用户信息（页面加载时调用）
 */
const fetchUserInfo = async () => {
  try {
    const res = await request({
      url: '/api/common/info',
      method: 'GET'
    })
    if (res.code === 0) {
      userInfo.value = res.data
    } else {
      ElMessage.error(res.msg || '获取用户信息失败')
    }
  } catch (err) {
    console.error('获取用户信息失败:', err)
    ElMessage.error('网络异常，请稍后重试')
  }
}

/**
 * 提交修改密码请求
 */
const submitPasswordForm = async () => {
  // 1. 表单验证
  await passwordFormRef.value.validate()

  submitLoading.value = true
  try {
    const res = await request({
      url: '/api/common/password',
      method: 'PUT',
      data: {
        old_password: passwordForm.old_password,
        new_password: passwordForm.new_password,
        confirm_new_password: passwordForm.confirm_new_password
      }
    })

    if (res.code === 0) {
      ElMessage.success('密码修改成功，请重新登录')
      passwordDialogVisible.value = false
      resetPasswordForm()
      // 可选：修改成功后跳转登录页
      // setTimeout(() => {
      //   router.push('/login')
      // }, 1500)
    } else {
      ElMessage.error(res.msg || '密码修改失败')
    }
  } catch (err) {
    console.error('修改密码失败:', err)
    ElMessage.error('网络异常，请稍后重试')
  } finally {
    submitLoading.value = false
  }
}

// ====================== 5. 弹窗控制 ======================
const openPasswordDialog = () => {
  resetPasswordForm()
  passwordDialogVisible.value = true
}

// ====================== 6. 页面生命周期 ======================
onMounted(() => {
  fetchUserInfo()
})
</script>

<style scoped>
.personal-workspace {
  padding: 20px;
}

.page-title {
  margin-bottom: 20px;
  color: #303133;
  font-size: 22px;
  font-weight: 600;
}

.info-card {
  max-width: 600px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-list {
  padding: 10px 0;
}

.info-item {
  display: flex;
  padding: 12px 0;
  border-bottom: 1px solid #ebeef5;
}

.info-item:last-child {
  border-bottom: none;
}

.label {
  width: 100px;
  color: #909399;
  font-weight: 500;
}

.value {
  color: #303133;
  flex: 1;
}

.action-bar {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>