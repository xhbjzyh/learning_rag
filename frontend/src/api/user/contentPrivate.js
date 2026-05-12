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

// 接口定义（已修复路径重复问题）
export default {
  getDocumentList() {
    return request.get('/user/content/private/document/list')
  },
  parseDocument(docId) {
    return request.post(`/user/content/private/document/${docId}/parse`)
  },
  getDocumentPoints(docId) {
    return request.get(`/user/content/private/document/${docId}/points`)
  },
  deleteDocument(docId) {
    return request.delete(`/user/content/private/document/${docId}`)
  },
  applyPublic(docId, remark = '') {
    // 🔥 修复：使用params传递查询参数，而不是拼接到URL
    return request.post(
      `/user/content/apply/document/${docId}`,
      null,  // POST body为空
      {
        params: {
          apply_remark: remark
        }
      }
    )
  }
}