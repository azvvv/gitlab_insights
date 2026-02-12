import request from './request'

// 日志和系统相关 API
export const systemApi = {
  // 获取日志列表
  getLogs(params) {
    return request.get('/logs', { params })
  },

  // 解析日志
  parseLog(data) {
    return request.post('/parse-log', data)
  },

  // 获取导入状态
  getStatus() {
    return request.get('/status')
  },

  // 获取导入历史
  getImportHistory() {
    return request.get('/import-history')
  },

  // 健康检查
  healthCheck() {
    return request.get('/health')
  },

  // 获取系统统计数据
  getStatistics() {
    return request.get('/statistics')
  },

  // 初始化数据库
  initDatabase() {
    return request.post('/init-db')
  },
}
