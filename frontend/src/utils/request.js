import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
  timeout: 30000, // 🔥 从15秒改成30秒，适配大模型调用耗时
})

// 请求拦截器（加token）
request.interceptors.request.use(
  (config) => {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    if (user.token) {
      config.headers.Authorization = `Bearer ${user.token}`
    }
    return config
  },
  (err) => {
    return Promise.reject(err)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (res) => {
    return res.data // 直接返回data，适配后端格式
  },
  (err) => {
    console.error('接口请求失败：', err)
    ElMessage.error(err.message || '请求失败')
    return Promise.reject(err)
  }
)

export default request