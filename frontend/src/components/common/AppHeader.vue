<template>
  <header class="app-header">
    <div class="header-content">
      <div class="logo" @click="goHome">
        <div class="logo-icon">
          <el-icon><Platform /></el-icon>
        </div>
        <div class="logo-info">
          <span class="logo-text">GitLab Insights</span>
          <span class="logo-subtitle">Welcome to GitLab Insights</span>
        </div>
      </div>
      <div class="header-actions">
        <template v-if="!userStore.isLoggedIn">
          <el-button type="primary" @click="showLoginDialog = true" size="large" class="login-btn">
            <el-icon><User /></el-icon>
            <span>登录</span>
          </el-button>
        </template>
        <template v-else>
          <el-dropdown @command="handleUserCommand">
            <span class="user-info">
              <div class="user-avatar">
                <el-icon><User /></el-icon>
              </div>
              <span class="user-name">{{ userStore.username }}</span>
              <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="dashboard">
                  <el-icon><DataAnalysis /></el-icon>
                  <span>进入系统</span>
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided>
                  <el-icon><SwitchButton /></el-icon>
                  <span>退出登录</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </div>
    </div>
  </header>

  <!-- 登录对话框 -->
  <el-dialog
    v-model="showLoginDialog"
    title="用户登录"
    width="400px"
    :close-on-click-modal="false"
  >
    <el-form :model="loginForm" :rules="loginRules" ref="loginFormRef" label-width="80px">
      <el-form-item label="用户名" prop="username">
        <el-input
          v-model="loginForm.username"
          placeholder="请输入用户名"
          @keyup.enter="handleLogin"
        >
          <template #prefix>
            <el-icon><User /></el-icon>
          </template>
        </el-input>
      </el-form-item>
      <el-form-item label="密码" prop="password">
        <el-input
          v-model="loginForm.password"
          type="password"
          placeholder="请输入密码"
          show-password
          @keyup.enter="handleLogin"
        >
          <template #prefix>
            <el-icon><Lock /></el-icon>
          </template>
        </el-input>
      </el-form-item>
      <el-form-item>
        <el-button
          type="primary"
          :loading="loginLoading"
          @click="handleLogin"
          style="width: 100%"
        >
          登录
        </el-button>
      </el-form-item>
    </el-form>
  </el-dialog>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  User,
  Platform,
  ArrowDown,
  DataAnalysis,
  SwitchButton,
  Lock,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const showLoginDialog = ref(false)
const loginLoading = ref(false)
const loginFormRef = ref(null)

const loginForm = reactive({
  username: '',
  password: '',
})

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const goHome = () => {
  router.push('/')
}

const handleLogin = async () => {
  if (!loginFormRef.value) return

  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loginLoading.value = true
      try {
        const result = await userStore.login(loginForm.username, loginForm.password)
        if (result.success) {
          ElMessage.success('登录成功')
          showLoginDialog.value = false
          loginForm.username = ''
          loginForm.password = ''
          router.push('/dashboard')
        } else {
          ElMessage.error(result.error || '用户名或密码错误')
        }
      } catch (error) {
        ElMessage.error(error.message || '登录失败')
      } finally {
        loginLoading.value = false
      }
    }
  })
}

const handleUserCommand = (command) => {
  if (command === 'dashboard') {
    router.push('/dashboard')
  } else if (command === 'logout') {
    userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/')
  }
}
</script>

<style lang="scss" scoped>
.app-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(59, 130, 246, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 1px 3px rgba(59, 130, 246, 0.08);
  
  .header-content {
    max-width: 1400px;
    margin: 0 auto;
    padding: 16px 40px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .logo {
      display: flex;
      align-items: center;
      gap: 16px;
      cursor: pointer;
      
      .logo-icon {
        width: 50px;
        height: 50px;
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        transition: all 0.3s;
        
        .el-icon {
          font-size: 28px;
          color: white;
        }
        
        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
        }
      }
      
      .logo-info {
        display: flex;
        flex-direction: column;
        gap: 2px;
        
        .logo-text {
          font-size: 22px;
          font-weight: 700;
          background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          letter-spacing: -0.5px;
        }
        
        .logo-subtitle {
          font-size: 12px;
          color: #64748b;
          font-weight: 500;
          letter-spacing: 0.5px;
        }
      }
    }
    
    .header-actions {
      .login-btn {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        border: none;
        padding: 12px 28px;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        transition: all 0.3s;
        
        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
        }
      }
      
      .user-info {
        display: flex;
        align-items: center;
        gap: 12px;
        cursor: pointer;
        padding: 8px 16px;
        border-radius: 12px;
        transition: all 0.3s;
        
        .user-avatar {
          width: 36px;
          height: 36px;
          background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          
          .el-icon {
            color: white;
            font-size: 18px;
          }
        }
        
        .user-name {
          color: #1e293b;
          font-weight: 600;
          font-size: 15px;
        }
        
        .dropdown-icon {
          color: #64748b;
          font-size: 14px;
        }
        
        &:hover {
          background: rgba(59, 130, 246, 0.08);
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .app-header {
    .header-content {
      padding: 12px 20px;
      
      .logo {
        .logo-icon {
          width: 42px;
          height: 42px;
          
          .el-icon {
            font-size: 24px;
          }
        }
        
        .logo-info {
          .logo-text {
            font-size: 18px;
          }
          
          .logo-subtitle {
            font-size: 10px;
          }
        }
      }
    }
  }
}
</style>
