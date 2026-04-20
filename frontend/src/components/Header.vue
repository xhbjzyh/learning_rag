<template>
  <div class="header-container">
    <div class="logo">RAG 个性化学习系统</div>
    <div class="user-info">
      <span>欢迎：{{ userStore.userInfo.username || '用户' }}</span>
      <el-button type="text" @click="$router.push('/personal')">个人中心</el-button>
      <el-button type="text" danger @click="handleLogout">退出登录</el-button>
    </div>
  </div>
</template>

<script setup>
import { useUserStore } from '@/store/user'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const router = useRouter()

// 退出登录
const handleLogout = () => {
  userStore.logout()
  ElMessage.success('退出成功')
  router.push('/login')
}
</script>

<style scoped>
.header-container {
  height: 60px;
  background: #fff;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 999;
}
.logo {
  font-size: 18px;
  font-weight: bold;
  color: #409eff;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
}
</style>