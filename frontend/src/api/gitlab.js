import request from './request'

// GitLab 相关 API
export const gitlabApi = {
  // 同步仓库
  syncRepositories(data) {
    return request.post('/gitlab/sync-repositories', data)
  },

  // 同步分组
  syncGroups(data) {
    return request.post('/gitlab/sync-groups', data)
  },

  // 同步分支
  syncBranches(data) {
    return request.post('/gitlab/sync-branches', data)
  },

  // 同步权限
  syncPermissions(data) {
    return request.post('/gitlab/sync-permissions', data)
  },

  // 同步所有数据
  syncAll(data) {
    return request.post('/gitlab/sync-all', data)
  },

  // 获取仓库列表
  getRepositories(params) {
    return request.get('/gitlab/repositories', { params })
  },

  // 获取分组列表
  getGroups(params) {
    return request.get('/gitlab/groups', { params })
  },

  // 获取仓库的分支列表
  getBranches(repoId, params) {
    return request.get(`/gitlab/repository/${repoId}/branches`, { params })
  },

  // 获取仓库的权限列表
  getPermissions(repoId, params) {
    return request.get(`/gitlab/repository/${repoId}/permissions`, { params })
  },

  // 创建标签
  createTag(data) {
    return request.post('/gitlab/create-tag', data)
  },

  // 获取待办事项列表
  getTodos(params) {
    return request.get('/gitlab/todos', { params })
  },

  // 标记单个待办事项为完成
  markTodoDone(todoId) {
    return request.post(`/gitlab/todos/${todoId}/mark-done`)
  },

  // 标记所有待办事项为完成
  markAllTodosDone() {
    return request.post('/gitlab/todos/mark-all-done')
  },

  // ========== 分支汇总 API ==========
  
  // 获取分支汇总列表
  getBranchSummaries(params) {
    return request.get('/gitlab/branches/summary', { params })
  },

  // 获取全局分支统计
  getGlobalBranchStatistics() {
    return request.get('/gitlab/branches/summary/global')
  },

  // 获取单个仓库的分支汇总
  getRepositoryBranchSummary(repositoryId) {
    return request.get(`/gitlab/branches/summary/repository/${repositoryId}`)
  },

  // 生成所有仓库的分支汇总（异步任务）
  generateBranchSummaries(params = {}) {
    return request.post('/gitlab/branches/summary/generate', params)
  },

  // 生成单个仓库的分支汇总
  generateRepositoryBranchSummary(repositoryId) {
    return request.post(`/gitlab/branches/summary/repository/${repositoryId}/generate`)
  },
}
