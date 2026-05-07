import axios from 'axios'
import { ElMessage } from 'element-plus'
import { getToken } from '@/utils/storage'
import { useUserStore } from '@/store/user'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 请求拦截器
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

// 响应拦截器
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

// 🔥 新增：流式请求的辅助方法（不使用 axios，直接用 fetch）
const streamRequest = {
  /**
   * 执行流式请求
   * @param {string} url - 请求路径（不含 baseURL）
   * @param {Object} params - 查询参数
   * @param {Function} onChunk - 每收到一个 chunk 的回调
   * @param {Function} onComplete - 完成时的回调
   * @param {Function} onError - 错误时的回调
   */
  async get(url, params = {}, onChunk, onComplete, onError) {
    try {
      const token = getToken()
      const queryString = new URLSearchParams(params).toString()
      const fullUrl = `${request.defaults.baseURL}${url}${queryString ? '?' + queryString : ''}`

      const response = await fetch(fullUrl, {
        method: 'GET',
        headers: {
          'Authorization': token ? `Bearer ${token}` : ''
        }
      })

      if (!response.ok) {
        throw new Error(`请求失败，状态码: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        if (onChunk) onChunk(chunk)
      }

      if (onComplete) onComplete()
    } catch (error) {
      console.error('流式请求失败:', error)
      if (onError) onError(error)
      throw error
    }
  }
}

// 导出接口方法（全部修复 + 新增）
export default {
  // ========== 原有接口保持不变 ==========
  // RAG问答（非流式）
  answer(params) {
    return request({
      url: '/user/rag/answer',
      method: 'POST',
      data: params,
      timeout: 120000
    })
  },

  // 知识点检索
  search(query, topK = 3) {
    return request({
      url: '/user/rag/search',
      method: 'get',
      params: {
        query: query,
        top_k: topK
      }
    })
  },

  // ========== 🔥 新增接口 ==========
  // 清除对话历史
  clearHistory() {
    return request({
      url: '/user/rag/history/clear',
      method: 'post'
    })
  },

  // ========== 🔥 流式接口（使用 streamRequest） ==========
  /**
   * 流式RAG问答
   * @param {Object} params - { query, kb_type, clear_history }
   * @param {Function} onChunk - 每收到一个 chunk 的回调
   * @param {Function} onComplete - 完成时的回调
   * @param {Function} onError - 错误时的回调
   */
  answerStream(params, onChunk, onComplete, onError) {
    return streamRequest.get(
      '/user/rag/answer/stream',
      params,
      onChunk,
      onComplete,
      onError
    )
  },

  // 导出 streamRequest 供直接使用
  streamRequest
}