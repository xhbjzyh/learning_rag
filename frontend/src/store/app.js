import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  // 状态
  const isLoading = ref(false)
  const sidebarCollapsed = ref(false)

  // 设置加载状态
  const setLoading = (loading) => {
    isLoading.value = loading
  }

  // 切换侧边栏
  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  return {
    isLoading,
    sidebarCollapsed,
    setLoading,
    toggleSidebar
  }
})