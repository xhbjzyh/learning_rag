<template>
  <div class="layout-container">
    <!-- 侧边栏 -->
    <el-aside width="200px" class="layout-aside">
      <div class="logo">RAG 个性化学习系统</div>
      <el-menu
        :default-active="activeMenu"
        mode="vertical"
        style="height: 100%; border-right: none;"
        @select="handleMenuSelect"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/chat">
          <el-icon><ChatDotRound /></el-icon>
          <span>AI 问答</span>
        </el-menu-item>
        <el-menu-item index="/knowledge">
          <el-icon><Document /></el-icon>
          <span>知识库</span>
        </el-menu-item>
        <el-menu-item index="/personal">
          <el-icon><User /></el-icon>
          <span>个人中心</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container class="layout-main">
      <!-- 顶部导航栏 -->
      <el-header class="layout-header">
        <div class="header-left"></div>
        <div class="header-right">
          <span>欢迎：{{ username }}</span>
          <el-button type="text" @click="goToPersonal">个人中心</el-button>
          <el-button type="text" @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>

      <!-- 页面内容 -->
      <el-main class="layout-content">
        <RouterView />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Odometer, ChatDotRound, Document, User } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 🔥 修复1：加判空保护
const username = computed(() => userStore?.username || '用户')
const activeMenu = ref(route.path)

// 🔥 修复2：监听路由变化，更新菜单高亮
watch(() => route.path, (newPath) => {
  activeMenu.value = newPath
}, { immediate: true })

// 🔥 修复3：手动处理菜单跳转，确保100%能跳转
const handleMenuSelect = (index) => {
  console.log('点击菜单:', index)
  router.push(index)
}

// 去个人中心
const goToPersonal = () => {
  router.push('/personal')
}

// 退出登录
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    userStore.logout()
    ElMessage.success('退出登录成功')
    router.push('/login')
  } catch {
    // 用户取消
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
  display: flex;
}
.layout-aside {
  background: #001529;
  display: flex;
  flex-direction: column;
}
.logo {
  height: 60px;
  line-height: 60px;
  color: #fff;
  font-size: 16px;
  font-weight: bold;
  text-align: center;
  border-bottom: 1px solid #002140;
}
.layout-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.layout-header {
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}
.layout-content {
  flex: 1;
  padding: 20px;
  background: #f0f2f5;
  overflow-y: auto;
}
</style>