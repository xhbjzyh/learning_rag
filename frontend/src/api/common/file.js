import request from '@/api/index'

/**
 * 文件接口模块
 */
const fileApi = {
  /**
   * 上传文件
   * @param {FormData} formData - 表单数据
   * @param {Function} onUploadProgress - 上传进度回调
   * @returns {Promise}
   */
  upload(formData, onUploadProgress) {
    return request({
      url: '/common/file/upload',
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress
    })
  },

  /**
   * 下载文件
   * @param {number} fileId - 文件ID
   * @returns {Promise}
   */
  download(fileId) {
    return request({
      url: `/common/file/download/${fileId}`,
      method: 'get',
      responseType: 'blob'
    })
  }
}

export default fileApi