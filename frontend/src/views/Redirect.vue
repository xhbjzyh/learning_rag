<template>
  <div class="redirect-container">
    <el-icon class="loading-icon" :size="40">
      <Loading />
    </el-icon>
    <p class="redirect-text">正在跳转...</p>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { Loading } from '@element-plus/icons-vue'
import { RoleEnum } from '@/utils/auth'

const router = useRouter()
const userStore = useUserStore()

onMounted(() => {
  const roleId = userStore.roleId

  if (roleId === RoleEnum.SUPER_ADMIN) {
    // 超级管理员
    router.replace('/admin/dashboard')
  } else if (roleId === RoleEnum.AUDITOR) {
    // 审核员
    router.replace('/auditor/dashboard')
  } else if (roleId === RoleEnum.USER) {
    // 普通用户
    router.replace('/user/dashboard')
  } else {
    // 未知角色，退回登录页
    router.replace('/login')
  }
})
</script>

<style scoped>
.redirect-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: #f0f2f5;
}

.loading-icon {
  color: #409EFF;
  animation: rotating 1.5s linear infinite;
}

@keyframes rotating {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.redirect-text {
  margin-top: 20px;
  font-size: 16px;
  color: #666;
}
</style>