/*
 * @Author: yang_x_neu azvvv2023@outlook.com
 * @Date: 2026-01-19 13:37:39
 * @LastEditors: yang_x_neu azvvv2023@outlook.com
 * @LastEditTime: 2026-01-22 12:21:05
 * @FilePath: \gitlab_insight\frontend\src\api\branch.js
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
 */
import request from './request'

// 分支规则相关 API
export const branchApi = {
  // 获取分支规则列表
  getRules(params) {
    return request.get('/branch-rules', { params })
  },

  // 创建分支规则
  createRule(data) {
    return request.post('/branch-rules', data)
  },

  // 获取规则详情
  getRuleById(id) {
    return request.get(`/branch-rules/${id}`)
  },

  // 更新分支规则
  updateRule(id, data) {
    return request.put(`/branch-rules/${id}`, data)
  },

  // 删除分支规则
  deleteRule(id) {
    return request.delete(`/branch-rules/${id}`)
  },

  // 测试规则匹配
  testPattern(data) {
    return request.post('/branch-rules/test-pattern', data)
  },

  // 应用规则
  applyRules(data) {
    return request.post('/branch-rules/apply', data)
  },

  // 获取删除报告
  getDeletionReport(params) {
    return request.get('/branch-rules/deletion-report', { params })
  },

  // 导出删除报告（Excel）
  exportDeletionReport(params) {
    return request.get('/branch-rules/deletion-report/excel', {
      params,
      responseType: 'blob',
    })
  },

  // 创建分支（包括主仓库和子模块）
  // 注意：由于可能包含多个 submodule，设置较长的超时时间
  createBranchWithSubmodules(data) {
    return request.post('/gitlab/branches', data, {
      timeout: 240000  // 120 秒超时（适用于包含大量 submodule 的场景）
    })
  },

  // 检查分支是否存在
  checkBranchExists(projectId, branchName) {
    return request.get('/gitlab/branches/exists', {
      params: {
        project_id: projectId,
        branch_name: branchName
      }
    })
  },
}
