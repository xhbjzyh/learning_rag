<template>
  <div class="register-container">
    <div class="register-box">
      <h2>用户注册</h2>
      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        label-width="80px"
        size="large"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="registerForm.username" placeholder="请输入用户名" clearable />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="registerForm.password" type="password" placeholder="请输入密码" show-password clearable />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="registerForm.confirmPassword" type="password" placeholder="请确认密码" show-password clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleRegister" style="width: 100%">注册</el-button>
          <div style="text-align: center; margin-top: 15px;">
            <el-button link @click="$router.push('/login')">已有账号？去登录</el-button>
          </div>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const router = useRouter()
const registerFormRef = ref()
const loading = ref(false)

const registerForm = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

const registerRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }, { min: 6, message: '密码至少6位' }],
  confirmPassword: [{ required: true, message: '请确认密码', trigger: 'blur' }, { validator: (r, v, c) => v === registerForm.password ? c() : c(new Error('密码不一致')), trigger: 'blur' }]
}

// 🔥 核心修复：把 confirmPassword 一起传给后端
const handleRegister = async () => {
  try {
    await registerFormRef.value.validate()
    loading.value = true

    const res = await request.post('/user/register', {
      username: registerForm.username,
      password: registerForm.password,
      confirm_password: registerForm.confirmPassword
    })

    ElMessage.success('注册成功！')
    router.push('/login')
  } catch (err) {
    console.error(err)
    ElMessage.error('注册失败：' + (err.response?.data?.msg || '未知错误'))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.register-container{width:100vw;height:100vh;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);}
.register-box{width:480px;padding:40px;background:#fff;border-radius:12px;box-shadow:0 10px 40px rgba(0,0,0,0.2);}
</style>