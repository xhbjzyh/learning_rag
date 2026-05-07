<template>
  <div class="auditor-personal">
    <h2 class="page-title">管理员个人工作台</h2>

    <!-- 管理员信息卡片 -->
    <el-card class="info-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>个人信息</span>
          <el-tag type="primary">管理员</el-tag>
        </div>
      </template>

      <div class="info-list">
        <div class="info-item">
          <span class="label">管理员ID：</span>
          <span class="value">{{ userInfo.id || '-' }}</span>
        </div>
        <div class="info-item">
          <span class="label">登录账号：</span>
          <span class="value">{{ userInfo.username || '-' }}</span>
        </div>
        <div class="info-item">
          <span class="label">角色权限：</span>
          <span class="value">{{ userInfo.role_id === 1 ? '超级管理员' : '管理员' }}</span>
        </div>
      </div>

      <div style="text-align:right; margin-top:15px;">
        <el-button type="primary" @click="openChangePwd">修改密码</el-button>
      </div>
    </el-card>

    <!-- 修改密码弹窗 -->
    <el-dialog v-model="dialogVisible" title="修改管理员密码" width="460px">
      <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="100px">
        <el-form-item label="旧密码" prop="old_password">
          <el-input v-model="pwdForm.old_password" type="password" placeholder="请输入旧密码" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="pwdForm.new_password" type="password" placeholder="请输入新密码（≥6位）" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_new_password">
          <el-input v-model="pwdForm.confirm_new_password" type="password" placeholder="请再次输入新密码" show-password />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="loading" @click="submitPwd">确认修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
// 🔥 直接引入你项目已有的 admin 接口
import adminApi from '@/api/admin/index.js'

// 数据
const userInfo = ref({})
const dialogVisible = ref(false)
const loading = ref(false)
const pwdFormRef = ref(null)

// 密码表单
const pwdForm = reactive({
  old_password: '',
  new_password: '',
  confirm_new_password: ''
})

// 验证规则
const pwdRules = reactive({
  old_password: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  new_password: [{ required: true, message: '请输入新密码', trigger: 'blur', min: 6 }],
  confirm_new_password: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: (_, v, cb) => v === pwdForm.new_password ? cb() : cb(new Error('两次密码不一致')), trigger: 'blur' }
  ]
})

// 获取管理员信息
const getAdminInfo = async () => {
  try {
    const res = await adminApi.getUserInfo()
    userInfo.value = res.data
  } catch (e) {
    ElMessage.error('获取信息失败')
  }
}

// 提交修改密码
const submitPwd = async () => {
  await pwdFormRef.value.validate()
  loading.value = true
  try {
    const res = await adminApi.updatePassword(pwdForm)
    ElMessage.success('密码修改成功！')
    dialogVisible.value = false
  } catch (e) {
    ElMessage.error('旧密码错误或网络异常')
  } finally {
    loading.value = false
  }
}

// 打开弹窗
const openChangePwd = () => {
  dialogVisible.value = true
}

// 初始化
onMounted(() => {
  getAdminInfo()
})
</script>

<style scoped>
.page-title {
  margin-bottom: 20px;
  color: #333;
}
.info-card {
  max-width: 600px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.info-item {
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}
.info-item:last-child {
  border-bottom: none;
}
</style>