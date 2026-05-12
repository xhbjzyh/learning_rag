import request from '@/api/index'

/**
 * 学习中心-习题模块API（与后端接口1:1匹配 | 已修复裸数据兼容）
 */
const learningCenterApi = {
  // -------------- 习题练习 --------------
  /**
   * 获取习题列表（分页）
   * @param {Object} params - { page, size, keyword }
   */
  getExerciseList(params) {
    // 强制限制size最大50，适配后端校验规则
    const paramsData = { ...params, size: Math.min(params.size || 10, 50) }
    return request({
      url: '/user/exercise/list',
      method: 'get',
      params: paramsData
    }).then(res => {
      // 直接返回后端裸数据 {list,total}
      return res || { list: [], total: 0 }
    })
  },

  /**
   * 获取单个习题详情（隐藏答案，仅题目+选项）
   * @param {number} exerciseId - 习题ID
   */
  getExerciseDetail(exerciseId) {
    return request({
      url: `/user/exercise/${exerciseId}`,
      method: 'get'
    }).then(res => res || {})
  },

  // -------------- 答题提交 --------------
  /**
   * 提交答题
   * @param {Object} data - { exercise_id, user_answer }
   */
  submitAnswer(data) {
    return request({
      url: '/user/exercise-record/submit',
      method: 'post',
      data
    }).then(res => res || {})
  },

  // -------------- 答题记录 --------------
  /**
   * 获取我的答题记录
   * @param {Object} params - { page, size }
   */
  getAnswerRecords(params) {
    // 强制限制size最大50，解决后端参数校验报错
    const paramsData = { ...params, size: Math.min(params.size || 10, 50) }
    return request({
      url: '/user/exercise-record/records',
      method: 'get',
      params: paramsData
    }).then(res => {
      return res || { list: [], total: 0 }
    })
  },

  // -------------- 错题本 --------------
  /**
   * 获取我的错题本
   * @param {Object} params - { page, size }
   */
  getWrongQuestions(params) {
    // 强制限制size最大50，解决后端参数校验报错
    const paramsData = { ...params, size: Math.min(params.size || 10, 50) }
    return request({
      url: '/user/exercise-record/wrong',
      method: 'get',
      params: paramsData
    }).then(res => {
      return res || { list: [], total: 0 }
    })
  },

  /**
   * 标记错题已掌握
   * @param {number} wrongId - 错题记录ID
   */
  markMastered(wrongId) {
    return request({
      url: `/user/exercise-record/wrong/${wrongId}/master`,
      method: 'post'
    }).then(res => res || {})
  },

  /**
   * 移除错题本中的题目
   * @param {number} wrongId - 错题记录ID
   */
  removeWrongQuestion(wrongId) {
    return request({
      url: `/user/exercise-record/wrong/${wrongId}`,
      method: 'delete'
    }).then(res => res || {})
  },

  // -------------- 学习统计 --------------
  /**
   * 获取学习统计数据（Dashboard用）
   */
  getStats() {
    return request({
      url: '/user/learning-center/stats',
      method: 'get'
    }).then(res => res || {})
  }
}

export default learningCenterApi