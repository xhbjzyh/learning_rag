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
      url: '/user/profile',
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
  },

  // ==================== 第一阶段优化：新增API ====================

  /**
   * 记录学习会话
   * @param {Object} data - { point_id, duration, is_mastered, session_type, notes }
   */
  recordLearningSession(data) {
    return request({
      url: '/user/profile/learning-session',
      method: 'post',
      data
    })
  },

  /**
   * 提交用户反馈
   * @param {Object} data - { point_id, course_id, feedback_type, content, rating }
   */
  submitFeedback(data) {
    return request({
      url: '/user/profile/feedback',
      method: 'post',
      data
    })
  },

  /**
   * 提交推荐反馈
   * @param {Object} data - { recommendation_id, is_clicked, is_helpful, feedback_score }
   */
  submitRecommendationFeedback(data) {
    return request({
      url: '/user/profile/recommendation-feedback',
      method: 'post',
      data
    })
  },

  /**
   * 获取用户行为统计
   */
  getBehaviorStats() {
    return request({
      url: '/user/profile/behavior-stats',
      method: 'get'
    })
  },

  /**
   * 获取学习历史
   * @param {Object} params - { page, limit }
   */
  getLearningHistory(params) {
    return request({
      url: '/user/profile/learning-history',
      method: 'get',
      params
    })
  },

  /**
   * 强制更新所有画像
   */
  forceUpdateAllProfiles() {
    return request({
      url: '/user/profile/update',
      method: 'post'
    })
  },

  /**
   * 获取用户薄弱标签
   * @param {Object} params - { limit }
   */
  getWeakTags(params) {
    return request({
      url: '/user/profile/weak-tags',
      method: 'get',
      params
    })
  },

  /**
   * 获取用户优势标签
   * @param {Object} params - { limit }
   */
  getStrongTags(params) {
    return request({
      url: '/user/profile/strong-tags',
      method: 'get',
      params
    })
  },

  /**
   * 获取用户兴趣标签
   * @param {Object} params - { limit }
   */
  getInterestTags(params) {
    return request({
      url: '/user/profile/interest-tags',
      method: 'get',
      params
    })
  },

  /**
   * 记录课程行为
   * @param {Number} courseId - 课程ID
   * @param {String} behaviorType - 行为类型
   * @param {Number} behaviorValue - 行为值
   */
  recordCourseBehavior(courseId, behaviorType, behaviorValue) {
    return request({
      url: `/user/profile/behavior/course/${courseId}/${behaviorType}`,
      method: 'post',
      params: { behavior_value: behaviorValue }
    })
  },

  /**
   * 记录知识点行为
   * @param {Number} pointId - 知识点ID
   * @param {String} behaviorType - 行为类型
   * @param {Number} behaviorValue - 行为值
   */
  recordKnowledgeBehavior(pointId, behaviorType, behaviorValue) {
    return request({
      url: `/user/profile/behavior/knowledge/${pointId}/${behaviorType}`,
      method: 'post',
      params: { behavior_value: behaviorValue }
    })
  },

  /**
   * 记录资源行为
   * @param {Number} resourceId - 资源ID
   * @param {String} behaviorType - 行为类型
   * @param {Number} behaviorValue - 行为值
   */
  recordResourceBehavior(resourceId, behaviorType, behaviorValue) {
    return request({
      url: `/user/profile/behavior/resource/${resourceId}/${behaviorType}`,
      method: 'post',
      params: { behavior_value: behaviorValue }
    })
  },

  // 🔥 新增：第五步智能推荐相关API
  
  /**
   * 获取智能推荐（混合策略）
   * @param {Number} limit - 推荐数量，默认5
   */
  getSmartRecommendations(limit = 5) {
    return request({
      url: '/user/profile/smart-recommendations',
      method: 'get',
      params: { limit }
    })
  },

  /**
   * 获取用户行为分析（含时段偏好、资源偏好、薄弱标签等）
   */
  getUserBehaviorAnalysis() {
    return request({
      url: '/user/profile/behavior-analysis',
      method: 'get'
    })
  },

  /**
   * 获取学习效果预测
   */
  getLearningPrediction() {
    return request({
      url: '/user/profile/learning-prediction',
      method: 'get'
    })
  }
}

// 🔥 导出独立函数（方便直接导入）
export const getSmartRecommendations = (limit = 5) => userProfileApi.getSmartRecommendations(limit)
export const getUserBehaviorAnalysis = () => userProfileApi.getUserBehaviorAnalysis()
export const getLearningPrediction = () => userProfileApi.getLearningPrediction()

export default userProfileApi