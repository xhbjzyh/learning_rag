import { defineStore } from 'pinia'

export const useAppStore = defineStore('app', {
  state: () => ({
    isCollapse: false
  }),
  actions: {
    toggleCollapse() {
      this.isCollapse = !this.isCollapse
    }
  }
})
