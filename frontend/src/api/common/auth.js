import request from '@/api/index'

/**
 * 认证接口模块
 */
const authApi = {
  /**
   * 用户登录
   * @param {Object} data - 登录数据
   * @param {string} data.username - 用户名
   * @param {string} data.password - 密码
   * @returns {Promise}
   */
  login(data) {
    return request({
      url: '/common/login',
      method: 'post',
      data
    })
  },

  /**
   * 用户注册
   * @param {Object} data - 注册数据
   * @param {string} data.username - 用户名
   * @param {string} data.password - 密码
   * @param {string} data.email - 邮箱（可选）
   * @returns {Promise}
   */
  register(data) {
    return request({
      url: '/common/register',
      method: 'post',
      data
    })
  },

  /**
   * 获取当前用户信息
   * @returns {Promise}
   */
  getUserInfo() {
    return request({
      url: '/common/info',
      method: 'get'
    })
  },

  /**
   * 用户登出
   * @returns {Promise}
   */
  logout() {
    return request({
      url: '/common/logout',
      method: 'post'
    })
  }
}

export default authApi