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
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 响应拦截器
request.interceptors.response.use((response) => {
  const res = response.data
  if (res.code !== 0) {
    ElMessage.error(res.msg || '操作失败')
    return Promise.reject(res.msg)
  }
  return res
})

// 导出所有接口（完全匹配Swagger）
export default {
  // ========== 仪表盘统计 ==========
  getDashboardStats() {
    return request.get('/admin/stats/dashboard')
  },

  // ========== 用户管理 ==========
  getUserList() {
    return request.get('/admin/user/list')
  },
  updateUserStatus(userId, status) {
    return request.put(`/admin/user/${userId}/status`, { status })
  },
  updateUserRole(userId, roleId) {
    return request.put(`/admin/user/${userId}/role`, { roleId })
  },

  // ========== 审核员管理 ==========
  getAuditorList() {
    return request.get('/admin/auditor/list')
  },
  addAuditor(data) {
    return request.post('/admin/auditor', data)
  },
  deleteAuditor(auditorId) {
    return request.delete(`/admin/auditor/${auditorId}`)
  },

  // ========== 文档审核（完全匹配最新Swagger接口） ==========
  // 获取待审核列表
  getPendingAuditList() {
    return request.get('/auditor/audit/pending')
  },
  // 获取审核历史记录
  getAuditHistory() {
    return request.get('/auditor/audit/history')
  },
  // 获取审核统计数据
  getAuditStats() {
    return request.get('/auditor/audit/stats')
  },
  // 审核文档公开申请（PUT方法，查询参数传递）
  auditApply(applyId, auditStatus, auditRemark = '') {
    // 构建查询参数
    const params = { audit_status: auditStatus }
    if (auditRemark) {
      params.audit_remark = auditRemark
    }
    return request.put(`/auditor/audit/apply/${applyId}`, null, { params })
  },

  // ========== 内容全局管理（完全匹配Swagger接口） ==========
  // 分类管理
  createCategory(data) {
    return request.post('/admin/content/category', data)
  },
  getCategoryList() {
    return request.get('/admin/content/category/list')
  },
  updateCategory(categoryId, categoryName, description = '') {
    return request.put(`/admin/content/category/${categoryId}`, null, {
      params: { category_name: categoryName, description }
    })
  },
  deleteCategory(categoryId) {
    return request.delete(`/admin/content/category/${categoryId}`)
  },

  // 知识点管理
  getKnowledgeList(page = 1, size = 10) {
    return request.get('/admin/content/knowledge/list', {
      params: { page, size }
    })
  },
  getKnowledgeDetail(pointId) {
    return request.get(`/admin/content/knowledge/point/${pointId}`)
  },
  updateKnowledge(pointId, data) {
    return request.post(`/admin/content/knowledge/point/${pointId}`, null, {
      params: data
    })
  },
  deleteKnowledge(pointId) {
    return request.delete(`/admin/content/knowledge/point/${pointId}`)
  },

  // ========== 内容全局管理（完全匹配Swagger接口） ==========
  // 文档管理
  getDocumentList(params) {
    return request.get('/admin/content/document/list', { params })
  },
  getDocumentDetail(docId) {
    return request.get(`/admin/content/document/${docId}`)
  },
  deleteDocument(docId) {
    return request.delete(`/admin/content/document/${docId}`)
  },
  // 文档下载（特殊处理：绕过响应拦截器）
  downloadDocument(docId) {
    // 直接使用原生fetch下载，避免Axios响应拦截器的问题
    const token = localStorage.getItem('token')
    const url = `/api/admin/content/document/${docId}/download`

    return fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  },

  // ========== 系统审计 ==========
  getAuditLogList() {
    return request.get('/admin/audit-log/list')
  },

  // ====================== ✅ 新增：管理员个人中心接口 ======================
  /**
   * 获取当前登录管理员信息
   */
  getUserInfo() {
    return request.get('/common/info')
  },
  /**
   * 修改管理员密码
   * @param {Object} data - 密码参数
   */
  updatePassword(data) {
    return request.put('/common/password', data)
  }
}
