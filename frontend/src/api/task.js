import request from './request'

// 任务相关 API
export const taskApi = {
  // 获取任务列表
  getTasks(params) {
    return request.get('/tasks', { params })
  },

  // 获取任务详情
  getTaskById(taskId) {
    return request.get(`/tasks/${taskId}`)
  },

  // 取消任务
  cancelTask(taskId) {
    return request.post(`/tasks/${taskId}/cancel`)
  },
}
