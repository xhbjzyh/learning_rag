import request from '@/api/index'

/**
 * 管理员-课程管理API
 */
const courseApi = {
  // ==================== 课程分类接口 ====================
  // 获取课程分类树形结构
  getCourseCategories() {
    return request.get('/admin/course/course/categories')
  },
  // 新增课程分类
  createCourseCategory(data) {
    return request.post('/admin/course/course/categories', data)
  },
  // 修改课程分类
  updateCourseCategory(id, data) {
    return request.put(`/admin/course/course/categories/${id}`, data)
  },
  // 删除课程分类
  deleteCourseCategory(id) {
    return request.delete(`/admin/course/course/categories/${id}`)
  },
  // 获取课程详情
  getCourseDetail(id) {
    return request.get(`/admin/course/course/${id}`)
  },

  // ==================== 课程管理接口 ====================
  /**
   * 获取课程列表（分页+搜索）
   * @param {Object} params - { page, size, title }
   */
  getCourseList(params) {
    return request({
      url: '/admin/course/course/list',
      method: 'get',
      params
    })
  },

  /**
   * 创建课程
   * @param {Object} data - 课程信息
   */
  createCourse(data) {
    return request({
      url: '/admin/course/course/create',
      method: 'post',
      data
    })
  },

  /**
   * 修改课程
   * @param {number} id - 课程ID
   * @param {Object} data - 更新数据
   */
  updateCourse(id, data) {
    return request({
      url: `/admin/course/course/update/${id}`,
      method: 'put',
      data
    })
  },

  /**
   * 删除课程
   * @param {number} id - 课程ID
   */
  deleteCourse(id) {
    return request({
      url: `/admin/course/course/delete/${id}`,
      method: 'delete',
    })
  },

  // ==================== 🔥 课程资料管理接口（视频/文档/习题） ====================
  /**
   * 获取课程资料列表（按类型筛选）
   * @param {number} courseId - 课程ID
   * @param {string} resourceType - 资源类型 video/document/exercise
   */
  getCourseMaterials(courseId, resourceType) {
    return request({
      url: `/admin/course/course/${courseId}/materials`,
      method: 'get',
      params: { resource_type: resourceType }
    })
  },

  /**
   * 创建课程资料（普通JSON创建）
   * @param {number} courseId - 课程ID
   * @param {Object} data - 资料参数
   */
  createCourseMaterial(courseId, data) {
    return request({
      url: `/admin/course/course/${courseId}/materials`,
      method: 'post',
      data
    })
  },

  /**
   * ✅ 新增：上传课程资料文件（核心：文件上传，FormData格式）
   * @param {number} courseId - 课程ID
   * @param {FormData} formData - 文件+表单数据
   */
  uploadCourseMaterial(formData, params) {
    return request({
      url: `/admin/course/course/resource/upload`, // 正确路径
      method: 'post',
      params: params, // 🔥 新增：查询参数(course_id/title/type)
      data: formData,
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  /**
   * 更新课程资料
   * @param {number} materialId - 资料ID
   * @param {Object} data - 更新参数
   */
  updateCourseMaterial(materialId, data) {
    return request({
      url: `/admin/course/course/materials/${materialId}`,
      method: 'put',
      data
    })
  },

  /**
   * 删除课程资料
   * @param {number} materialId - 资料ID
   */
  deleteCourseMaterial(materialId) {
    return request({
      url: `/admin/course/course/materials/${materialId}`,
      method: 'delete'
    })
  },

  /**
   * ✅ 新增：下载课程资料文件
   * @param {number} materialId - 资料ID
   */
  downloadCourseMaterial(materialId) {
    return request({
      url: `/admin/course/course/materials/${materialId}/download`,
      method: 'get',
      // 下载文件设置响应类型
      responseType: 'blob'
    })
  },

  // ==================== ✅ 新增：知识点管理接口（内嵌课程API，无需新建文件） ====================
  /**
   * 获取知识点列表
   */
  getKnowledgeList(params) {
    return request.get('/admin/knowledge/list', { params })
  },
  /**
   * 新增知识点
   */
  createKnowledge(data) {
    return request.post('/admin/knowledge/create', data)
  },
  /**
   * 修改知识点
   */
  updateKnowledge(id, data) {
    return request.put(`/admin/knowledge/update/${id}`, data)
  },
  /**
   * 删除知识点
   */
  deleteKnowledge(id) {
    return request.delete(`/admin/knowledge/delete/${id}`)
  }
}

export default courseApi