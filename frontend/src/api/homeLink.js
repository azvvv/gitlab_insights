import request from './request'

/**
 * 获取所有首页链接
 * @param {boolean} includeInactive - 是否包含未激活的记录
 */
export function getHomeLinks(includeInactive = false) {
  return request({
    url: '/home-links',
    method: 'get',
    params: includeInactive ? { include_inactive: 'true' } : {}
  })
}

/**
 * 按分类获取链接
 */
export function getHomeLinksByCategory(category) {
  return request({
    url: `/home-links/category/${category}`,
    method: 'get'
  })
}

/**
 * 按分类和分组获取链接
 */
export function getHomeLinksByGroup(category, groupName) {
  return request({
    url: `/home-links/category/${category}/group/${groupName}`,
    method: 'get'
  })
}

/**
 * 根据ID获取链接
 */
export function getHomeLinkById(id) {
  return request({
    url: `/home-links/${id}`,
    method: 'get'
  })
}

/**
 * 创建新链接
 */
export function createHomeLink(data) {
  return request({
    url: '/home-links',
    method: 'post',
    data
  })
}

/**
 * 更新链接
 */
export function updateHomeLink(id, data) {
  return request({
    url: `/home-links/${id}`,
    method: 'put',
    data
  })
}

/**
 * 删除链接
 */
export function deleteHomeLink(id) {
  return request({
    url: `/home-links/${id}`,
    method: 'delete'
  })
}

/**
 * 切换链接启用状态
 */
export function toggleHomeLinkActive(id) {
  return request({
    url: `/home-links/${id}/toggle`,
    method: 'post'
  })
}

/**
 * 批量更新排序
 */
export function updateHomeLinkSort(orders) {
  return request({
    url: '/home-links/sort',
    method: 'put',
    data: { orders }
  })
}
