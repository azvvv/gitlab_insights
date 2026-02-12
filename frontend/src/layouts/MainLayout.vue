<template>
  <div class="main-layout">
    <!-- 使用公共 Header -->
    <AppHeader />

    <!-- 主容器：侧边栏 + 内容区 -->
    <div class="layout-container">
      <!-- 左侧边栏 -->
      <aside class="sidebar">
        <el-menu
          :default-active="currentPath"
          class="sidebar-menu"
          @select="handleMenuSelect"
        >
          <!-- 仪表盘 -->
          <el-menu-item index="/dashboard">
            <el-icon><DataAnalysis /></el-icon>
            <template #title>仪表盘</template>
          </el-menu-item>

          <!-- GitLab 管理 -->
          <el-sub-menu index="gitlab">
            <template #title>
              <el-icon><FolderOpened /></el-icon>
              <span>GitLab 管理</span>
            </template>
            <el-menu-item index="/repositories">
              <el-icon><FolderOpened /></el-icon>
              <template #title>仓库管理</template>
            </el-menu-item>
            <el-menu-item index="/groups">
              <el-icon><Grid /></el-icon>
              <template #title>分组管理</template>
            </el-menu-item>
            <el-menu-item index="/branches">
              <el-icon><Operation /></el-icon>
              <template #title>分支管理</template>
            </el-menu-item>
            <el-menu-item index="/branch-rules">
              <el-icon><Setting /></el-icon>
              <template #title>分支规则</template>
            </el-menu-item>
            <el-menu-item index="/branch-creation-history">
              <el-icon><Clock /></el-icon>
              <template #title>分支创建历史</template>
            </el-menu-item>
            <el-menu-item index="/branch-create">
              <el-icon><Plus /></el-icon>
              <template #title>创建分支</template>
            </el-menu-item>
            <el-menu-item index="/logs">
              <el-icon><Document /></el-icon>
              <template #title>日志管理</template>
            </el-menu-item>
            <el-menu-item v-if="userStore.user?.is_admin" index="/todos">
              <el-icon><List /></el-icon>
              <template #title>待办列表</template>
            </el-menu-item>
          </el-sub-menu>

          <!-- 任务管理 -->
          <el-menu-item index="/tasks">
            <el-icon><List /></el-icon>
            <template #title>任务管理</template>
          </el-menu-item>

          <!-- 系统设置 -->
          <el-menu-item index="/settings">
            <el-icon><Tools /></el-icon>
            <template #title>系统设置</template>
          </el-menu-item>

          <!-- 首页内容维护（仅管理员） -->
          <el-menu-item v-if="userStore.user?.is_admin" index="/home-content">
            <el-icon><EditPen /></el-icon>
            <template #title>首页内容维护</template>
          </el-menu-item>
        </el-menu>
      </aside>

      <!-- 右侧内容区域 -->
      <main class="main-content">
        <div class="content-container">
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </div>
      </main>
    </div>

    <!-- 使用公共 Footer -->
    <AppFooter />

    <!-- 修改密码对话框 -->
    <el-dialog
      v-model="changePasswordVisible"
      title="修改密码"
      width="400px"
    >
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="80px"
      >
        <el-form-item label="旧密码" prop="oldPassword">
          <el-input
            v-model="passwordForm.oldPassword"
            type="password"
            show-password
          />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="passwordForm.newPassword"
            type="password"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="passwordForm.confirmPassword"
            type="password"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="changePasswordVisible = false">取消</el-button>
        <el-button type="primary" :loading="passwordLoading" @click="handleChangePassword">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  DataAnalysis,
  FolderOpened,
  Grid,
  Operation,
  Setting,
  Document,
  List,
  Tools,
  EditPen,
  Clock,
  Plus,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import AppHeader from '@/components/common/AppHeader.vue'
import AppFooter from '@/components/common/AppFooter.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const changePasswordVisible = ref(false)
const passwordLoading = ref(false)
const passwordFormRef = ref(null)

const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const passwordRules = {
  oldPassword: [
    { required: true, message: '请输入旧密码', trigger: 'blur' },
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.value.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

// 当前路径
const currentPath = computed(() => route.path)

// 处理菜单选择
const handleMenuSelect = (path) => {
  router.push(path)
}

// 修改密码
const handleChangePassword = async () => {
  if (!passwordFormRef.value) return

  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      passwordLoading.value = true
      try {
        const result = await userStore.changePassword(
          passwordForm.value.oldPassword,
          passwordForm.value.newPassword
        )

        if (result.success) {
          ElMessage.success('密码修改成功，请重新登录')
          changePasswordVisible.value = false
          passwordForm.value.oldPassword = ''
          passwordForm.value.newPassword = ''
          passwordForm.value.confirmPassword = ''
          
          // 退出登录
          setTimeout(() => {
            userStore.logout()
            router.push('/')
          }, 1000)
        } else {
          ElMessage.error(result.error || '修改密码失败')
        }
      } catch (error) {
        ElMessage.error('修改密码失败，请稍后重试')
      } finally {
        passwordLoading.value = false
      }
    }
  })
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.main-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: $bg-primary;
}

// 布局容器
.layout-container {
  display: flex;
  flex: 1;
  max-width: 1600px;
  width: 100%;
  margin: 0 auto;
  background: white;
  box-shadow: $shadow-lg;
}

// 左侧边栏
.sidebar {
  width: 240px;
  background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 50%, #2563eb 100%);
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
  
  :deep(.sidebar-menu) {
    border: none;
    background: transparent;
    
    .el-menu-item {
      color: rgba(255, 255, 255, 0.85);
      font-size: $font-md;
      font-weight: 500;
      padding: 16px 20px;
      margin: 8px 12px;
      border-radius: $radius-md;
      transition: $transition-normal;
      
      &:hover {
        background: rgba(255, 255, 255, 0.15);
        color: white;
      }
      
      &.is-active {
        background: rgba(255, 255, 255, 0.25);
        color: white;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
      }
      
      .el-icon {
        color: inherit;
        font-size: 18px;
        margin-right: 8px;
      }
    }

    // 子菜单样式
    .el-sub-menu {
      .el-sub-menu__title {
        color: rgba(255, 255, 255, 0.85);
        font-size: $font-md;
        font-weight: 500;
        padding: 16px 20px;
        margin: 8px 12px;
        border-radius: $radius-md;
        transition: $transition-normal;

        &:hover {
          background: rgba(255, 255, 255, 0.15);
          color: white;
        }

        .el-icon {
          color: inherit;
          font-size: 18px;
          margin-right: 8px;
        }
      }

      .el-menu {
        background: rgba(0, 0, 0, 0.1);
      }

      .el-menu-item {
        padding-left: 50px !important;
        margin: 4px 12px;
        font-size: 14px;

        &:hover {
          background: rgba(255, 255, 255, 0.2);
        }

        &.is-active {
          background: rgba(255, 255, 255, 0.3);
        }
      }
    }
  }
}

// 右侧内容区域
.main-content {
  flex: 1;
  overflow-y: auto;
  background: $bg-secondary;
  
  .content-container {
    padding: 24px;
    min-height: 100%;
  }
}

// 过渡动画
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

// 响应式设计
@media (max-width: 1024px) {
  .layout-container {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
    
    :deep(.sidebar-menu) {
      display: flex;
      overflow-x: auto;
      
      .el-menu-item {
        white-space: nowrap;
      }
    }
  }
}

@media (max-width: 768px) {
  .main-content {
    .content-container {
      padding: 16px;
    }
  }
}
</style>
