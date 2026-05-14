import request from '@/api/index'

export default {
  // 获取配置列表
  getConfigList(params = {}) {
    return request.get('/admin/system-config/list', { params })
  },

  // 获取单个配置
  getConfig(key) {
    return request.get(`/admin/system-config/${key}`)
  },

  // 创建配置
  createConfig(data) {
    return request.post('/admin/system-config/create', data)
  },

  // 更新配置
  updateConfig(id, data) {
    return request.put(`/admin/system-config/update/${id}`, data)
  },

  // 删除配置
  deleteConfig(id) {
    return request.delete(`/admin/system-config/delete/${id}`)
  },

  // 初始化大模型配置
  initLLMConfig() {
    return request.post('/admin/system-config/init-llm-config')
  }
}
