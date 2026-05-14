import request from '@/api/index'

/**
 * 管理员-审核员管理API
 */
const auditorManageApi = {
  /**
   * 创建审核员账号
   * @param {Object} data - { username, password }
   */
  createAuditor(data) {
    return request({
      url: '/admin/auditor/create',
      method: 'post',
      data
    })
  },

  /**
   * 获取审核员列表（分页）
   * @param {Object} params - { page, size }
   */
  getAuditorList(params) {
    return request({
      url: '/admin/auditor/list',
      method: 'get',
      params
    })
  },

  /**
   * 删除审核员
   * @param {number} auditorId - 审核员ID
   */
  deleteAuditor(auditorId) {
    return request({
      url: `/admin/auditor/${auditorId}`,
      method: 'delete'
    })
  }
}

export default auditorManageApi