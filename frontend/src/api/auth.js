import request from './request'

// 认证相关 API
export const authApi = {
  // 自动登录（推荐使用）
  autoLogin(data) {
    return request.post('/auth/auto-login', data)
  },

  // 本地登录
  login(data) {
    return request.post('/auth/login', data)
  },

  // LDAP 登录
  ldapLogin(data) {
    return request.post('/auth/ldap-login', data)
  },

  // 验证 Token
  verifyToken() {
    return request.get('/auth/verify')
  },

  // 获取当前用户信息
  getCurrentUser() {
    return request.get('/auth/me')
  },

  // 修改密码
  changePassword(data) {
    return request.post('/auth/change-password', data)
  },

  // 测试 LDAP 连接（管理员）
  testLdap() {
    return request.get('/auth/ldap/test')
  },

  // 获取 LDAP 配置（管理员）
  getLdapConfig() {
    return request.get('/auth/ldap/config')
  },
}
