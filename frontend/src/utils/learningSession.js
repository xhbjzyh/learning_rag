/**
 * 学习会话记录工具
 * 用于在学习过程中自动记录用户的学习行为
 */

import userProfileApi from '@/api/user/userProfile'
import { ElMessage } from 'element-plus'

class LearningSessionTracker {
  constructor() {
    this.sessionStartTime = null
    this.currentPointId = null
    this.isTracking = false
  }

  /**
   * 开始跟踪学习会话
   * @param {Number} pointId - 知识点ID
   */
  startSession(pointId) {
    console.log('🔥🔥🔥 startSession 被调用，pointId:', pointId)
    
    if (!pointId) {
      console.warn('⚠️ 知识点ID不能为空')
      return
    }

    this.sessionStartTime = Date.now()
    this.currentPointId = pointId
    this.isTracking = true

    console.log('✅ 学习会话已启动:', {
      pointId,
      startTime: new Date().toISOString(),
      isTracking: this.isTracking
    })
  }

  /**
   * 结束学习会话并保存
   * @param {Object} options - 可选参数
   * @param {Boolean} options.isMastered - 是否掌握
   * @param {String} options.sessionType - 会话类型: study/review/practice
   * @param {String} options.notes - 学习笔记
   */
  async endSession(options = {}) {
    console.log('🔥 endSession 被调用', {
      isTracking: this.isTracking,
      currentPointId: this.currentPointId,
      sessionStartTime: this.sessionStartTime
    })

    if (!this.isTracking || !this.currentPointId) {
      console.warn('⚠️ 没有正在进行的会话')
      return
    }

    const duration = Math.floor((Date.now() - this.sessionStartTime) / 1000) // 转换为秒
    
    console.log('🔥 计算学习时长:', duration, '秒')

    // 如果学习时长少于5秒，不记录（避免误操作）
    if (duration < 5) {
      console.log('⚠️ 学习时长过短，不记录会话', duration, '秒')
      this.resetSession()
      return
    }

    const sessionData = {
      point_id: this.currentPointId,
      duration: duration,
      is_mastered: options.isMastered || false,
      session_type: options.sessionType || 'study',
      notes: options.notes || null
    }

    console.log('🔥 准备提交学习会话数据:', sessionData)

    try {
      const result = await userProfileApi.recordLearningSession(sessionData)
      console.log('✅ 学习会话记录成功:', sessionData)
      console.log('🔥 API 返回结果:', result)

      // 可选：显示提示消息
      // ElMessage.success(`学习记录已保存 (${this.formatDuration(duration)})`)
    } catch (error) {
      console.error('❌ 记录学习会话失败:', error)
      console.error('❌ 错误详情:', {
        message: error.message,
        response: error.response,
        status: error.response?.status,
        data: error.response?.data
      })
      // 不显示错误消息，避免打扰用户
    } finally {
      this.resetSession()
    }
  }

  /**
   * 重置会话状态
   */
  resetSession() {
    this.sessionStartTime = null
    this.currentPointId = null
    this.isTracking = false
  }

  /**
   * 格式化时长
   */
  formatDuration(seconds) {
    if (seconds < 60) {
      return `${seconds}秒`
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60)
      return `${minutes}分钟`
    } else {
      const hours = Math.floor(seconds / 3600)
      const minutes = Math.floor((seconds % 3600) / 60)
      return `${hours}小时${minutes}分钟`
    }
  }

  /**
   * 获取当前会话时长（秒）
   */
  getCurrentSessionDuration() {
    if (!this.isTracking || !this.sessionStartTime) {
      return 0
    }
    return Math.floor((Date.now() - this.sessionStartTime) / 1000)
  }
}

// 导出单例
export default new LearningSessionTracker()
