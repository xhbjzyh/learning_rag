<template>
  <div class="sidebar">
    <!-- Logo -->
    <div class="sidebar-logo">
      <h2 v-if="!sidebarCollapsed">RAG学习系统</h2>
      <h2 v-else>RAG</h2>
    </div>

    <!-- 菜单 -->
    <el-menu
      :default-active="activeMenu"
      :collapse="sidebarCollapsed"
      :unique-opened="true"
      router
      background-color="#304156"
      text-color="#bfcbd9"
      active-text-color="#409EFF"
    >
      <!-- 超级管理员菜单 -->
      <template v-if="isSuperAdmin">
        <el-menu-item index="/admin/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>
        <el-menu-item index="/admin/user-manage">
          <el-icon><User /></el-icon>
          <template #title>用户管理</template>
        </el-menu-item>
        <el-menu-item index="/admin/auditor-manage">
          <el-icon><UserFilled /></el-icon>
          <template #title>审核员管理</template>
        </el-menu-item>
        <el-menu-item index="/admin/content-global">
          <el-icon><Document /></el-icon>
          <template #title>内容管理</template>
        </el-menu-item>
        <el-menu-item index="/admin/course-manage">
          <el-icon><Notebook /></el-icon>
          <template #title>课程管理</template>
        </el-menu-item>
        <el-menu-item index="/admin/audit-manage">
          <el-icon><Check /></el-icon>
          <template #title>审核管理</template>
        </el-menu-item>
        <el-menu-item index="/admin/system-config">
          <el-icon><Setting /></el-icon>
          <template #title>系统配置</template>
        </el-menu-item>
      </template>

      <!-- 审核员菜单 -->
      <template v-else-if="isAuditor">
        <el-menu-item index="/auditor/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>
        <!-- 🔥 用100%存在的 List 图标，避免报错 -->
        <el-menu-item index="/auditor/audit-workbench">
          <el-icon><List /></el-icon>
          <template #title>审核工作台</template>
        </el-menu-item>
        <el-menu-item index="/auditor/public-content">
          <el-icon><Document /></el-icon>
          <template #title>公共内容</template>
        </el-menu-item>
      </template>

      <!-- 普通用户菜单 -->
      <template v-else>
        <el-menu-item index="/user/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>
        <el-menu-item index="/user/rag-chat">
          <el-icon><ChatDotRound /></el-icon>
          <template #title>RAG问答</template>
        </el-menu-item>
        <el-menu-item index="/user/public-content">
          <el-icon><Document /></el-icon>
          <template #title>公共内容</template>
        </el-menu-item>
        <el-menu-item index="/user/learning-center">
          <el-icon><Notebook /></el-icon>
          <template #title>学习中心</template>
        </el-menu-item>
        <el-menu-item index="/user/personal-recommend">
          <el-icon><MagicStick /></el-icon>
          <template #title>个性化推荐</template>
        </el-menu-item>
        <el-menu-item index="/user/user-profile">
          <el-icon><User /></el-icon>
          <template #title>个人中心</template>
        </el-menu-item>
      </template>
    </el-menu>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/store/app'
import { useUserStore } from '@/store/user'
import { isSuperAdmin as checkIsSuperAdmin, isAuditor as checkIsAuditor } from '@/utils/auth'
// 🔥 导入所有100%存在的图标，删掉所有错误图标
import {
  DataAnalysis, User, UserFilled, Document, List, Check, Setting,
  ChatDotRound, Notebook, MagicStick
} from '@element-plus/icons-vue'

const route = useRoute()
const appStore = useAppStore()
const userStore = useUserStore()

const sidebarCollapsed = computed(() => appStore.sidebarCollapsed)
const activeMenu = computed(() => route.path)
const isSuperAdmin = computed(() => checkIsSuperAdmin(userStore.roleId))
const isAuditor = computed(() => checkIsAuditor(userStore.roleId))
</script>

<style scoped>
.sidebar {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.sidebar-logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #263445;
  color: #fff;
  font-size: 16px;
  font-weight: bold;
}

.sidebar-logo h2 {
  margin: 0;
  font-size: 16px;
}

.el-menu {
  border-right: none;
  flex: 1;
  overflow-y: auto;
}
</style>