<template>
  <el-menu
    :default-active="activeMenu"
    :collapse="isCollapse"
    background-color="#304156"
    text-color="#bfcbd9"
    active-text-color="#409eff"
    :unique-opened="true"
    router
  >
    <el-menu-item index="/dashboard">
      <el-icon><data-analysis /></el-icon>
      <template #title>系统仪表盘</template>
    </el-menu-item>
    <el-menu-item index="/knowledge">
      <el-icon><folder-opened /></el-icon>
      <template #title>知识库管理</template>
    </el-menu-item>
    <el-menu-item index="/chat">
      <el-icon><chat-dot-round /></el-icon>
      <template #title>对话问答</template>
    </el-menu-item>
  </el-menu>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/store/app'
import {
  DataAnalysis,
  FolderOpened,
  ChatDotRound
} from '@element-plus/icons-vue'

const route = useRoute()
const appStore = useAppStore()

// 侧边栏折叠状态
const isCollapse = computed(() => appStore.isCollapse)
// 当前激活的菜单，和路由path绑定
const activeMenu = computed(() => route.path)
</script>

<style scoped>
.el-menu {
  border: none;
  height: 100%;
}
</style>