<template>
  <div class="login-page">
    <!-- 顶部系统标题栏 -->
    <header class="system-header">
      <div class="header-content">
        <div class="logo">
          <div class="logo-icon"></div>
          <div class="logo-text">
            <h1>基于RAG的个性化学习推荐系统</h1>
            <p>RAG-based Personalized Learning Recommendation System</p>
          </div>
        </div>
      </div>
    </header>

    <!-- 主体内容区 -->
    <main class="main-content">
      <!-- 左侧背景插画区 -->
      <div class="left-banner">
        <div class="banner-content">
          <div class="illustration">
            <div class="hand left-hand"></div>
            <div class="hand right-hand"></div>
            <div class="birds">
              <div class="bird bird-1"></div>
              <div class="bird bird-2"></div>
              <div class="bird bird-3"></div>
              <div class="bird bird-4"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧登录卡片 -->
      <div class="right-login">
        <div class="login-card">
          <h2 class="login-title">用户登录</h2>

          <el-form
            ref="loginFormRef"
            :model="loginForm"
            :rules="loginRules"
            class="login-form"
            @keyup.enter="handleLogin"
          >
            <el-form-item prop="username">
              <el-input
                v-model="loginForm.username"
                placeholder="请输入用户名"
                size="large"
                :prefix-icon="User"
                class="login-input"
              />
            </el-form-item>

            <el-form-item prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
                size="large"
                :prefix-icon="Lock"
                show-password
                class="login-input"
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                size="large"
                class="login-button"
                :loading="loading"
                @click="handleLogin"
              >
                登录
              </el-button>
            </el-form-item>

            <div class="login-links">
              <el-button type="text" @click="goToRegister">立即注册</el-button>
              <span class="divider">|</span>
              <el-button type="text" @click="handleForgetPassword">忘记密码</el-button>
            </div>
          </el-form>
        </div>
      </div>
    </main>

    <!-- 底部信息栏 -->
    <footer class="system-footer">
      <div class="footer-content">
        <div class="service-info">
          <span>技术支持热线：</span>
          <span class="phone">17838930575</span>
          <span class="work-time">周一至周五 8:30-17:30</span>
        </div>
        <div class="copyright">
          Copyright © 2026 All rights reserved. 毕业设计 | 版权所有
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()

const loginFormRef = ref(null)
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return

  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await userStore.login(loginForm)
        ElMessage.success('登录成功')
        router.push('/redirect')
      } catch (error) {
        console.error('登录失败:', error)
      } finally {
        loading.value = false
      }
    }
  })
}

const goToRegister = () => {
  router.push('/register')
}

const handleForgetPassword = () => {
  ElMessage.info('请联系管理员重置密码')
}
</script>

<style scoped>
/* 全局重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.login-page {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
  overflow: hidden;
}

/* 顶部系统标题栏 */
.system-header {
  height: 80px;
  background: linear-gradient(90deg, #c8102e 0%, #d92b3a 100%);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 10;
}

.header-content {
  max-width: 1200px;
  height: 100%;
  margin: 0 auto;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 15px;
}

.logo-icon {
  width: 50px;
  height: 50px;
  background: #fff;
  border-radius: 4px;
  position: relative;
}

.logo-icon::before {
  content: '';
  position: absolute;
  top: 10px;
  left: 10px;
  width: 15px;
  height: 15px;
  background: #c8102e;
}

.logo-icon::after {
  content: '';
  position: absolute;
  bottom: 10px;
  right: 10px;
  width: 15px;
  height: 15px;
  background: #c8102e;
}

.logo-text h1 {
  color: #fff;
  font-size: 24px;
  font-weight: 600;
  line-height: 1.2;
}

.logo-text p {
  color: rgba(255, 255, 255, 0.8);
  font-size: 12px;
  margin-top: 2px;
}

/* 主体内容区 */
.main-content {
  flex: 1;
  display: flex;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  padding: 40px 20px;
  gap: 60px;
}

/* 左侧背景插画区 */
.left-banner {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.banner-content {
  width: 100%;
  height: 100%;
  position: relative;
  background: linear-gradient(135deg, #fefefe 0%, #f0f4f8 100%);
  border-radius: 12px;
  overflow: hidden;
}

.illustration {
  width: 100%;
  height: 100%;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hand {
  width: 200px;
  height: 250px;
  position: absolute;
  border-radius: 50% 50% 50% 50% / 60% 60% 40% 40%;
  opacity: 0.8;
}

.left-hand {
  left: 15%;
  top: 20%;
  background: linear-gradient(135deg, #ff9a56 0%, #ff6b35 100%);
  transform: rotate(-15deg);
}

.right-hand {
  right: 15%;
  bottom: 20%;
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
  transform: rotate(15deg);
}

.birds {
  position: absolute;
  top: 30%;
  right: 30%;
}

.bird {
  width: 30px;
  height: 30px;
  background: #c8102e;
  border-radius: 50% 50% 50% 0;
  position: absolute;
  opacity: 0.7;
}

.bird-1 {
  top: 0;
  left: 0;
  transform: rotate(-45deg);
}

.bird-2 {
  top: 20px;
  left: 40px;
  transform: rotate(-30deg);
  width: 20px;
  height: 20px;
}

.bird-3 {
  top: 50px;
  left: 20px;
  transform: rotate(-60deg);
  width: 15px;
  height: 15px;
}

.bird-4 {
  top: 30px;
  left: -20px;
  transform: rotate(-20deg);
  width: 25px;
  height: 25px;
}

/* 右侧登录卡片 */
.right-login {
  width: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-card {
  width: 100%;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  padding: 40px;
}

.login-title {
  text-align: center;
  font-size: 22px;
  font-weight: 600;
  color: #333;
  margin-bottom: 30px;
}

.login-form {
  width: 100%;
}

.login-input {
  height: 48px;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
  transition: all 0.3s;
}

.login-input:focus {
  border-color: #c8102e;
  box-shadow: 0 0 0 2px rgba(200, 16, 46, 0.1);
}

.login-button {
  width: 100%;
  height: 48px;
  background: linear-gradient(90deg, #c8102e 0%, #d92b3a 100%);
  border: none;
  font-size: 16px;
  font-weight: 500;
  border-radius: 4px;
  transition: all 0.3s;
}

.login-button:hover {
  background: linear-gradient(90deg, #b00e29 0%, #c8102e 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(200, 16, 46, 0.2);
}

.login-links {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 20px;
  font-size: 14px;
  color: #606266;
}

.login-links .el-button {
  padding: 0;
  color: #c8102e;
  font-size: 14px;
}

.login-links .el-button:hover {
  color: #d92b3a;
}

.divider {
  margin: 0 10px;
  color: #dcdfe6;
}

/* 底部信息栏 */
.system-footer {
  height: 60px;
  background: #f5f7fa;
  border-top: 1px solid #e4e7ed;
}

.footer-content {
  max-width: 1200px;
  height: 100%;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  font-size: 14px;
  color: #606266;
}

.service-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.phone {
  color: #c8102e;
  font-size: 18px;
  font-weight: 600;
}

.work-time {
  color: #909399;
}

/* 响应式适配 */
@media (max-width: 992px) {
  .main-content {
    flex-direction: column;
    gap: 30px;
    padding: 20px;
  }

  .left-banner {
    display: none;
  }

  .right-login {
    width: 100%;
    max-width: 400px;
    margin: 0 auto;
  }

  .logo-text h1 {
    font-size: 20px;
  }

  .logo-text p {
    display: none;
  }

  .footer-content {
    flex-direction: column;
    gap: 10px;
    padding: 10px 20px;
    height: auto;
  }
}
</style>