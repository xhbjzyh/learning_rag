// @/api/user/course.js
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
      url: `/user/course/course/${courseId}`,
      method: 'get'
    })
  },

  // 获取课程资料
  getCourseMaterials(courseId, resourceType) {
    return request({
      url: `/user/course/${courseId}/materials`,
      method: 'get',
      params: { resource_type: resourceType }
    })
  },

  // 更新课程进度
  updateCourseProgress(data) {
    return request({
      url: `/user/course/course/${data.course_id}/progress`,
      method: 'post',
      params: {
        progress: data.progress,
        study_duration: data.study_duration
      }
    })
  },

  // ✅ 修复：传递所有必要参数（progress, watch_position, study_duration, is_finished）
  updateResourceProgress(data) {
    return request({
      url: `/user/course/resource/${data.resource_id}/progress`,
      method: "post",
      data: {
        progress: data.progress,
        watch_position: data.watch_position,
        study_duration: data.study_duration,
        is_finished: data.is_finished
      }
    });
  },

  // ✅ 对齐后端：获取习题列表（支持 course_id/page/size 参数）
  getExerciseList(params) {
    return request({
      url: '/user/course/exercise/list',
      method: 'get',
      params // 包含 course_id/page/size
    })
  },

  // ✅ 对齐后端：获取习题详情（路径传参 exercise_id）
  getExerciseDetail(exerciseId) {
    return request({
      url: `/user/course/exercise/${exerciseId}`,
      method: 'get'
    })
  },

  // ✅ 对齐后端：提交习题答案（包含 user_id + exercise_id + answer）
  submitExerciseAnswer(data) {
    return request({
      url: '/user/course/exercise/submit',
      method: 'post',
      data: {
        user_id: data.user_id || 1, // 补充用户ID（后端必填）
        exercise_id: data.exercise_id,
        user_answer: data.user_answer
      }
    })
  },

  // 🆕 错题本相关接口
  // 获取错题本列表
  getWrongQuestionList(params) {
    return request({
      url: '/user/course/wrong-question/list',
      method: 'get',
      params
    })
  },

  // 标记错题已掌握
  markWrongMastered(wrongId) {
    return request({
      url: `/user/course/wrong-question/${wrongId}/mastered`,
      method: 'post'
    })
  },

  // 删除错题
  removeWrongQuestion(wrongId) {
    return request({
      url: `/user/course/wrong-question/${wrongId}`,
      method: 'delete'
    })
  },

  // 基于错题生成专项练习
  generatePracticeFromWrong(wrongId) {
    return request({
      url: '/user/course/practice/generate',
      method: 'post',
      params: { wrong_id: wrongId }
    })
  },

  // 🆕 个性化推荐相关接口
  // 获取课程个性化推荐（学习路径）
  getCourseRecommendations(courseId) {
    return request({
      url: `/user/course/${courseId}/recommendations`,
      method: 'get'
    })
  },

  // 获取课程知识点掌握情况
  getCourseMastery(courseId) {
    return request({
      url: `/user/course/${courseId}/mastery`,
      method: 'get'
    })
  }
}

export default courseApi