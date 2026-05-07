import request from '@/api/index'

/**
 * 个性化推荐模块API（与后端接口1:1匹配）
 */
const personalRecommendApi = {
  /**
   * 获取个性化推荐知识点
   * @param {Object} params - { top_k: 推荐数量(1-20) }
   */
  getPersonalRecommend(params) {
    return request({
      url: '/user/recommend/personal',
      method: 'get',
      params
    })
  },

  /**
   * 生成个性化学习路径
   * @param {Object} params - { max_length: 路径长度(1-20) }
   */
  getLearningPath(params) {
    return request({
      url: '/user/recommend/learning-path',
      method: 'get',
      params
    })
  }
}

export default personalRecommendApi