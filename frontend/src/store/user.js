import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import authApi from '@/api/common/auth'
import { getToken, setToken, removeToken, getUserInfo, setUserInfo, clearStorage } from '@/utils/storage'

export const useUserStore = defineStore('user', () => {
  // 状态
  const token = ref(getToken())
  const userInfo = ref(getUserInfo())

  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  const roleId = computed(() => userInfo.value?.role_id)
  const username = computed(() => userInfo.value?.username)

  // 登录
  const login = async (loginData) => {
    const res = await authApi.login(loginData)
    token.value = res.data.access_token
    userInfo.value = res.data.user_info
    setToken(res.data.access_token)
    setUserInfo(res.data.user_info)
    return res
  }

  // 获取用户信息
  const fetchUserInfo = async () => {
    const res = await authApi.getUserInfo()
    userInfo.value = res.data
    setUserInfo(res.data)
    return res
  }

  // 登出
  const logout = () => {
    token.value = ''
    userInfo.value = null
    clearStorage()
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    roleId,
    username,
    login,
    fetchUserInfo,
    logout
  }
})