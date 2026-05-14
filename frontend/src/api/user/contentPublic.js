import axios from 'axios'
import { ElMessage } from 'element-plus'
import { getToken } from '@/utils/storage'
import { useUserStore } from '@/store/user'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000
})

request.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

request.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res.code !== 0) {
      ElMessage.error(res.msg || '请求失败')
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

export default {
  // 获取公共分类列表
  getCategoryList() {
    return request({
      url: '/user/content/public/category/list',
      method: 'get'
    })
  },

  // 获取公共文档列表（按分类ID）
  getDocumentList(categoryId) {
    return request({
      url: '/user/content/public/document/list',
      method: 'get',
      params: { category_id: categoryId }
    })
  },

  // 获取文档详情
  getDocumentDetail(docId) {
    return request({
      url: `/user/content/public/document/${docId}`,
      method: 'get'
    })
  },

  // 获取文档知识点列表
  getDocumentPoints(docId) {
    return request({
      url: `/user/content/public/document/${docId}/points`,
      method: 'get'
    })
  },

  // 下载文档
downloadDocument(docId, fileName) {
  const token = getToken()
  if (!token) {
    ElMessage.error('请先登录')
    return
  }

  // ✅ 修复：使用相对路径，让request实例自动处理baseURL和token
  request({
    url: `/user/content/public/document/${docId}/download`,
    method: 'get',
    responseType: 'blob' // 关键：指定响应类型为二进制流
  }).then(response => {
    // 创建blob对象并触发下载
    const url = window.URL.createObjectURL(new Blob([response]))
    const link = document.createElement('a')
    link.href = url
    link.download = fileName
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('下载成功')
  }).catch(error => {
    console.error('下载失败:', error)
    ElMessage.error('下载失败')
  })
}

}