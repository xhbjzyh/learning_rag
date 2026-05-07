import axios from 'axios'
import { ElMessage } from 'element-plus'
import { getToken } from '@/utils/storage'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 请求拦截器
request.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}, (error) => Promise.reject(error))

// 响应拦截器
request.interceptors.response.use((response) => {
  const res = response.data
  if (res.code !== 0) {
    ElMessage.error(res.msg || '请求失败')
    return Promise.reject(new Error(res.msg || '请求失败'))
  }
  return res
}, (error) => {
  ElMessage.error(error.response?.data?.msg || '服务异常')
  return Promise.reject(error)
})

// 接口定义（和你43-45行完全一致，无任何多余代码）
export default {
  getDocumentList() {
    return request.get('/user/content/private/content/private/document/list')
  },
  parseDocument(docId) {
    return request.post(`/user/content/private/content/private/document/${docId}/parse`)
  },
  getDocumentPoints(docId) {
    return request.get(`/user/content/private/content/private/document/${docId}/points`)
  },
  deleteDocument(docId) {
    return request.delete(`/user/content/private/content/private/document/${docId}`)
  },
  applyPublic(docId) {
    return request.post(`/user/content/apply/content/apply/document/${docId}`)
  }
}