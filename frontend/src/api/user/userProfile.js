import request from '@/api/index'

/**
 * 个人中心-用户画像/信息模块API
 */
const userProfileApi = {
  /**
   * 获取用户画像（包含学习统计、强弱标签等）
   */
  getUserProfile() {
    return request({
      url: '/user/profile/profile',
      method: 'get'
    })
  },

  /**
   * 获取当前用户基本信息
   */
  getUserInfo() {
    return request({
      url: '/common/info',
      method: 'get'
    })
  },

  /**
   * 修改用户密码
   * @param {Object} data - { old_password, new_password, confirm_new_password }
   */
  updatePassword(data) {
    return request({
      url: '/common/password',
      method: 'put',
      data
    })
  }
}

export default userProfileApi