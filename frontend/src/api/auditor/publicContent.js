import request from '@/api/index'

/**
 * 审核员公共内容接口
 */
const auditorPublicContentApi = {
  /**
   * 获取公共内容列表
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  getContentList(params) {
    return request({
      url: '/auditor/content/public/list',
      method: 'get',
      params
    })
  }
}

export default auditorPublicContentApi