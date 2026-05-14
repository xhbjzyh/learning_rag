NEW_FILE_CODE
import request from '@/api/index'

/**
 * 个性化推荐系统 API（第二阶段）
 */
const recommendationApi = {
  /**
   * 获取个性化推荐
   * @param {Object} params - { query, limit }
   */
  getPersonalizedRecommendations(params = {}) {
    return request({
      url: '/user/recommendation/personalized',
      method: 'get',
      params
    })
  },

  /**
   * 提交推荐反馈
   * @param {Object} data - { recommendation_id, is_clicked, is_helpful, feedback_score }
   */
  submitRecommendationFeedback(data) {
    return request({
      url: '/user/recommendation/feedback',
      method: 'post',
      data
    })
  },

  /**
   * 获取相似课程
   * @param {Number} courseId - 课程ID
   * @param {Object} params - { limit }
   */
  getSimilarCourses(courseId, params = {}) {
    return request({
      url: `/user/recommendation/similar-courses/${courseId}`,
      method: 'get',
      params
    })
  },

  /**
   * 获取推荐统计信息
   */
  getRecommendationStats() {
    return request({
      url: '/user/recommendation/stats',
      method: 'get'
    })
  },

  /**
   * 刷新相似度矩阵（管理员功能，前端暂不暴露）
   * @param {String} type - user/course/both
   */
  refreshSimilarities(type = 'both') {
    return request({
      url: '/user/recommendation/refresh-similarities',
      method: 'post',
      params: { similarity_type: type }
    })
  }
}

export default recommendationApi
