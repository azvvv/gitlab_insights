import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  const token = ref(null)

  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.is_admin === true)
  const username = computed(() => user.value?.username || '')
  const userId = computed(() => user.value?.user_id || null)

  // 从本地存储初始化
  function initFromStorage() {
    const savedToken = localStorage.getItem('token')
    const savedUser = localStorage.getItem('user')

    if (savedToken && savedUser) {
      token.value = savedToken
      try {
        user.value = JSON.parse(savedUser)
      } catch (e) {
        console.error('解析用户信息失败:', e)
        logout()
      }
    }
  }

  // 登录
  async function login(username, password) {
    try {
      const res = await authApi.autoLogin({ username, password })
      
      if (res.success && res.token) {
        token.value = res.token
        user.value = res.user

        // 保存到本地存储
        localStorage.setItem('token', res.token)
        localStorage.setItem('user', JSON.stringify(res.user))

        return { success: true }
      } else {
        return { success: false, error: res.error || '登录失败' }
      }
    } catch (error) {
      return { success: false, error: error.message || '登录失败' }
    }
  }

  // 登出
  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  // 更新用户信息
  function updateUser(userData) {
    user.value = { ...user.value, ...userData }
    localStorage.setItem('user', JSON.stringify(user.value))
  }

  // 修改密码
  async function changePassword(oldPassword, newPassword) {
    try {
      const res = await authApi.changePassword({
        old_password: oldPassword,
        new_password: newPassword,
      })
      return { success: true, message: res.message }
    } catch (error) {
      return { success: false, error: error.message || '修改密码失败' }
    }
  }

  return {
    user,
    token,
    isLoggedIn,
    isAdmin,
    username,
    userId,
    initFromStorage,
    login,
    logout,
    updateUser,
    changePassword,
  }
})
