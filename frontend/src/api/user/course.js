// 🔥 修改：使用你项目里正确的请求工具路径
import request from '@/api/index'

const courseApi = {
  // 获取三级分类
  getCategories() {
    return request({
      url: '/user/course/categories',
      method: 'get'
    })
  },

  // 获取课程列表
  getCourseList(params) {
    return request({
      url: '/user/course/list',
      method: 'get',
      params
    })
  },

  // 获取课程详情
  getCourseDetail(courseId) {
    return request({
      url: `/user/course/${courseId}`,
      method: 'get'
    })
  },

  // 更新课程进度
  updateCourseProgress(data) {
    return request({
      url: `/user/course/${data.course_id}/progress`,
      method: 'post',
      params: {
        progress: data.progress,
        study_duration: data.study_duration
      }
    })
  },

  // 更新资源进度
  updateResourceProgress(data) {
    return request({
      url: `/user/course/resource/${data.resource_id}/progress`,
      method: 'post',
      params: {
        progress: data.progress,
        watch_duration: data.watch_duration
      }
    })
  }
}

export default courseApi