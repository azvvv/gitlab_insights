/**
 * 分支创建历史记录 API
 */
import request from './request'

/**
 * 获取分支创建记录列表（带分页和过滤）
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.pageSize - 每页数量
 * @param {number} params.projectId - 项目ID（可选）
 * @param {string} params.branchName - 分支名称（可选）
 * @param {string} params.status - 状态（可选）
 * @param {string} params.search - 综合搜索（可选）
 * @param {string} params.jiraTicket - Jira工单号（可选）
 * @param {string} params.startDate - 开始日期（可选）
 * @param {string} params.endDate - 结束日期（可选）
 * @returns {Promise}
 */
export function getBranchCreationRecords(params) {
  return request({
    url: '/gitlab/branches/history',
    method: 'get',
    params
  })
}

/**
 * 获取分支创建统计信息
 * @returns {Promise}
 */
export function getBranchCreationStats() {
  return request({
    url: '/gitlab/branches/history/stats',
    method: 'get'
  })
}

/**
 * 获取单个分支创建记录详情
 * @param {number} recordId - 记录ID
 * @returns {Promise}
 */
export function getBranchCreationRecord(recordId) {
  return request({
    url: `/gitlab/branches/history/${recordId}`,
    method: 'get'
  })
}
