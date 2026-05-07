import request from '@/api/index'

/**
 * 审核工作台接口
 */
const auditWorkbenchApi = {
  /**
   * 获取待审核内容列表
   * @returns {Promise}
   */
  getPendingList() {
    return request({
      url: '/auditor/audit/pending',
      method: 'get'
    })
  },

  /**
   * 获取审核历史
   * @returns {Promise}
   */
  getAuditHistory() {
    return request({
      url: '/auditor/audit/history',
      method: 'get'
    })
  },

  /**
   * 获取审核统计
   * @returns {Promise}
   */
  getAuditStats() {
    return request({
      url: '/auditor/audit/stats',
      method: 'get'
    })
  },

  /**
   * 审核文档公开申请
   * @param {number} applyId - 申请ID
   * @param {number} auditStatus - 审核状态（1=通过，2=驳回）
   * @param {string} auditRemark - 审核备注
   * @returns {Promise}
   */
  auditDocument(applyId, auditStatus, auditRemark) {
    return request({
      url: `/auditor/audit/apply/${applyId}`,
      method: 'put',
      params: {
        audit_status: auditStatus,
        audit_remark: auditRemark
      }
    })
  }
}

export default auditWorkbenchApi