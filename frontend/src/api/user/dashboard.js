
import request from '@/api/index'

/**
 * 用户个人仪表盘API
 */
const dashboardApi = {
  /**
   * 获取仪表盘数据
   */
  getDashboardData() {
    return request({
      url: '/user/personal/dashboard',
      method: 'get'
    })
  }
}

export default dashboardApi
