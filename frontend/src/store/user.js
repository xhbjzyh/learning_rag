import { defineStore } from 'pinia'
import request from '@/utils/request'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: '',
    username: '',
    userId: '',
    roleId: 0
  }),
  getters: {
    isLoggedIn: (state) => !!state.token
  },
  actions: {
    // 初始化用户信息
    initUser() {
      this.token = localStorage.getItem('token') || ''
      this.username = localStorage.getItem('username') || ''
      this.userId = localStorage.getItem('userId') || ''
      this.roleId = parseInt(localStorage.getItem('roleId') || 0)
    },

    // 🔥 核心修复：修正登录接口路径
    async login(loginForm) {
      console.log('开始登录:', loginForm)
      // 你的request.js baseURL已经带了/api，这里直接写/login即可
      const res = await request.post('/login', loginForm)
      console.log('后端登录返回:', res)

      this.setUserInfo(res.data)
      return res
    },

    // 保存用户信息
    setUserInfo(userInfo) {
      console.log('保存用户信息:', userInfo)
      this.token = userInfo.token
      this.username = userInfo.username
      this.userId = userInfo.id
      this.roleId = userInfo.role_id || 0

      // 持久化到本地存储
      localStorage.setItem('token', userInfo.token)
      localStorage.setItem('username', userInfo.username)
      localStorage.setItem('userId', userInfo.id)
      localStorage.setItem('roleId', userInfo.role_id || 0)

      console.log('保存后的Store:', this.$state)
    },

    // 退出登录
    logout() {
      this.token = ''
      this.username = ''
      this.userId = ''
      this.roleId = 0

      // 清除本地存储
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      localStorage.removeItem('userId')
      localStorage.removeItem('roleId')
    }
  }
})