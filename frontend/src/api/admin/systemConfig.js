import request from '@/api/index'

/**
 * 系统配置接口
 */
const systemConfigApi = {
  /**
   * 获取系统配置
   * @returns {Promise}
   */
  getConfig() {
    return request({
      url: '/admin/system/config',
      method: 'get'
    })
  },

  /**
   * 更新系统配置
   * @param {Object} newConfig - 新配置
   * @returns {Promise}
   */
  updateConfig(newConfig) {
    return request({
      url: '/admin/system/config',
      method: 'post',
      data: newConfig
    })
  }
}

export default systemConfigApi