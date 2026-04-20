<template>
  <div class="main-layout">
    <!-- 侧边栏 -->
    <div class="sidebar-container" :class="{ 'is-collapse': appStore.isCollapse }">
      <div class="logo-container">
        <h2 v-if="!appStore.isCollapse">RAG学习系统</h2>
        <h2 v-else>RAG</h2>
      </div>
      <SideMenu />
    </div>

    <!-- 右侧主内容区 -->
    <div class="main-container">
      <!-- 顶部导航 -->
      <PageHeader />
      <!-- 页面内容区，路由在这里渲染 -->
      <div class="page-content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
import { useAppStore } from '@/store/app'
import SideMenu from '@/components/SideMenu.vue'
import PageHeader from '@/components/PageHeader.vue'

const appStore = useAppStore()
</script>

<style scoped lang="scss">
.main-layout {
  width: 100vw;
  height: 100vh;
  display: flex;
  overflow: hidden;

  // 侧边栏样式
  .sidebar-container {
    width: 210px;
    height: 100%;
    background-color: #304156;
    transition: width 0.3s;
    overflow: hidden;

    &.is-collapse {
      width: 64px;
    }

    .logo-container {
      height: 60px;
      display: flex;
      align-items: center;
      justify-content: center;
      background-color: #263445;

      h2 {
        color: #fff;
        font-size: 18px;
        font-weight: 600;
        white-space: nowrap;
        margin: 0;
      }
    }
  }

  // 右侧主内容区
  .main-container {
    flex: 1;
    height: 100%;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background-color: #f0f2f5;

    .page-content {
      flex: 1;
      padding: 20px;
      overflow-y: auto;
    }
  }
}
</style>