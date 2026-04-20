<template>
  <div class="personal-box">
    <div class="title">个人中心</div>

    <el-card class="info-card">
      <template #header>
        <span>用户信息</span>
      </template>
      <div class="info-item">
        <span>用户名：</span>
        <span>{{ userStore.userInfo.username }}</span>
      </div>
      <div class="info-item">
        <span>角色：</span>
        <!-- 🔥 动态角色显示，根据role_id映射 -->
        <span>{{ getRoleName(userStore.userInfo.role_id) }}</span>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { useUserStore } from '@/store/user'
const userStore = useUserStore()

// 🔥 角色映射（和你后端的角色ID对应）
const roleMap = {
  1: '超级管理员',
  2: '审核员',
  3: '普通用户'
}

// 根据role_id获取角色名称
const getRoleName = (roleId) => {
  return roleMap[roleId] || '未知角色'
}
</script>

<style scoped>
.personal-box {
  max-width: 800px;
  margin: 0 auto;
}
.title {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 20px;
}
.info-card {
  margin-bottom: 20px;
}
.info-item {
  padding: 10px 0;
  font-size: 16px;
}
</style>