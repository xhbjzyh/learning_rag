import request from '@/api/index'

/**
 * 个人中心接口
 */
const personalCenterApi = {
  /**
   * 修改密码
   * @param {Object} data - 密码数据
   * @returns {Promise}
   */
  changePassword(data) {
    return request({
      url: '/user/personal/password',
      method: 'put',
      data
    })
  },

  /**
   * 更新个人信息
   * @param {Object} data - 个人信息
   * @returns {Promise}
   */
  updateInfo(data) {
    return request({
      url: '/user/personal/info',
      method: 'put',
      data
    })
  }
}

export default personalCenterApi