import request from '@/api/index'

const courseApi = {
  // ==================== 课程分类 ====================
  getCourseCategories() {
    return request.get('/admin/course/categories')
  },
  createCourseCategory(data) {
    return request.post('/admin/course/categories', data)
  },
  updateCourseCategory(id, data) {
    return request.put(`/admin/course/categories/${id}`, data)
  },
  deleteCourseCategory(id) {
    return request.delete(`/admin/course/categories/${id}`)
  },
  getCourseDetail(id) {
    return request.get(`/admin/course/${id}`)
  },

  // ==================== 课程管理 ====================
  getCourseList(params) {
    return request.get('/admin/course/list', { params })
  },
  createCourse(data) {
    return request.post('/admin/course/create', data)
  },
  updateCourse(id, data) {
    return request.put(`/admin/course/update/${id}`, data)
  },
  deleteCourse(id) {
    return request.delete(`/admin/course/delete/${id}`)  // 🔥 修复：DELETE 不需要 data 参数
  },

  // ==================== 课程资料列表（文档/视频/习题） ====================
  getCourseMaterials(courseId, resourceType) {
    return request.get(`/admin/course/${courseId}/materials`, {
      params: { resource_type: resourceType }
    })
  },
  createCourseMaterial(courseId, data) {
    return request.post(`/admin/course/${courseId}/materials`, data)
  },
  uploadCourseMaterial(formData, params) {
    return request.post('/admin/course/resource/upload', formData, {
      params,
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  updateCourseMaterial(materialId, data) {
    return request.put(`/admin/course/materials/${materialId}`, data)
  },
  deleteCourseMaterial(materialId) {
    return request.delete(`/admin/course/materials/${materialId}`)
  },
  downloadCourseMaterial(materialId) {
    return request.get(`/admin/course/materials/${materialId}/download`, {
      responseType: 'blob'
    })
  },

  // ==================== 课程知识点管理 ====================
  getKnowledgeList(courseId) {
    return request.get(`/admin/course/${courseId}/knowledge`)
  },
  createKnowledge(data) {
    return request.post('/admin/course/knowledge/create', data)
  },
  updateKnowledge(id, data) {
    return request.put(`/admin/course/knowledge/${id}`, data)
  },
  deleteKnowledge(id) {
    return request.delete(`/admin/course/knowledge/${id}`)
  },

  // ==================== 🔥 新增：独立习题管理（匹配后端接口） ====================
  // 获取课程下所有习题
  getCourseExercises(courseId) {
    return request.get(`/admin/course/${courseId}/exercises`)
  },
  // 创建课程习题
  createCourseExercise(courseId, data) {
    return request.post(`/admin/course/${courseId}/exercises`, data)
  },
  // 更新课程习题
  updateCourseExercise(exerciseId, data) {
    return request.put(`/admin/course/exercises/${exerciseId}`, data)
  },
  // 删除课程习题
  deleteCourseExercise(exerciseId) {
    return request.delete(`/admin/course/exercises/${exerciseId}`)
  }
}

export default courseApi