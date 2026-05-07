import request from '@/api/index'

/**
 * 内容公开申请接口
 */
const contentApplyApi = {
  /**
   * 申请公开文档
   * @param {number} docId - 文档ID
   * @param {string} applyRemark - 申请理由
   * @returns {Promise}
   */
  applyPublic(docId, applyRemark) {
    return request({
      url: `/user/content/apply/document/${docId}`,
      method: 'post',
      params: { apply_remark: applyRemark }
    })
  },

  /**
   * 获取我的公开申请列表
   * @returns {Promise}
   */
  getMyApplyList() {
    return request({
      url: '/user/content/apply/my',
      method: 'get'
    })
  },

  /**
   * 取消待审核的申请
   * @param {number} applyId - 申请ID
   * @returns {Promise}
   */
  cancelApply(applyId) {
    return request({
      url: `/user/content/apply/${applyId}`,
      method: 'delete'
    })
  }
}

export default contentApplyApi