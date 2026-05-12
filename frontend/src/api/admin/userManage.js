import request from '@/api/index'

/**
 * 管理员-用户管理API
 */
const adminUserApi = {
  /**
   * 获取用户列表（分页）
   * @param {Object} params - { page, size }
   */
  getUserList(params) {
    return request({
      url: '/admin/user/list',
      method: 'get',
      params
    })
  },

  /**
   * 获取用户详情
   * @param {number} userId - 用户ID
   */
  getUserDetail(userId) {
    return request({
      url: '/admin/user/detail',
      method: 'get',
      params: { user_id: userId }
    })
  },

  /**
   * 重置用户密码
   * @param {Object} data - { user_id, new_password }
   */
  resetPassword(data) {
    return request({
      url: '/admin/user/reset-password',
      method: 'post',
      data
    })
  },

  /**
   * 删除用户
   * @param {number} userId - 用户ID
   */
  deleteUser(userId) {
    return request({
      url: `/admin/user/${userId}`,
      method: 'delete'
    })
  },

  /**
   * 获取所有用户答题记录
   * @param {Object} params - { user_id: 可选，不传返回所有 }
   */
  getAnswerRecords(params) {
    return request({
      url: '/admin/user/answer-records',
      method: 'get',
      params
    })
  },

  /**
   * 获取所有用户学习记录
   * @param {Object} params - { user_id: 可选，不传返回所有 }
   */
  getLearningRecords(params) {
    return request({
      url: '/admin/user/learning-records',
      method: 'get',
      params
    })
  }
}

export default adminUserApi