import axios from 'axios'
import { ElMessage } from 'element-plus'
import { getToken, removeToken } from '@/utils/storage'
import { useUserStore } from '@/store/user'

// 创建axios实例
const request = axios.create({
  baseURL: '/api', // 开发环境使用代理
  timeout: 30000 // 请求超时时间：30秒
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    // 在发送请求之前做些什么
    const token = getToken()
    if (token) {
      // 添加Token到请求头
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    // 对请求错误做些什么
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器 ✅【核心修复：兼容裸数据 + 标准格式】
request.interceptors.response.use(
  (response) => {
    const res = response.data

    // ==============================================
    // 修复点：如果后端返回裸数据（无code字段，如习题列表）
    // 直接返回数据，不做code校验
    // ==============================================
    if (res.code === undefined) {
      return res
    }

    // 原有逻辑：标准接口（有code字段）继续校验
    if (res.code !== 0) {
      ElMessage.error(res.msg || '请求失败')

      // 401: 未登录或Token过期
      if (res.code === 401) {
        const userStore = useUserStore()
        userStore.logout()
        window.location.href = '/login'
      }
      return Promise.reject(new Error(res.msg || '请求失败'))
    }

    return res
  },
  (error) => {
    console.error('响应错误:', error)

    if (error.response) {
      switch (error.response.status) {
        case 401:
          ElMessage.error('未登录或登录已过期，请重新登录')
          const userStore = useUserStore()
          userStore.logout()
          window.location.href = '/login'
          break
        case 403:
          ElMessage.error('无权限访问')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          ElMessage.error('服务器错误')
          break
        default:
          ElMessage.error(error.response.data?.msg || '请求失败')
      }
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }

    return Promise.reject(error)
  }
)

export default request