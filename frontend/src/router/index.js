import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import MainLayout from '@/layouts/MainLayout.vue'
import LandingLayout from '@/layouts/LandingLayout.vue'

const routes = [
  {
    path: '/',
    component: LandingLayout,
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('@/views/Home.vue'),
        meta: { requiresAuth: false },
      },
    ],
  },
  {
    path: '/dashboard',
    component: MainLayout,
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { requiresAuth: true, title: '仪表盘', icon: 'DataAnalysis' },
      },
    ],
  },
  {
    path: '/repositories',
    component: MainLayout,
    children: [
      {
        path: '',
        name: 'Repositories',
        component: () => import('@/views/gitlab/Repositories.vue'),
        meta: { requiresAuth: true, title: '仓库管理', icon: 'FolderOpened' },
      },
    ],
  },
  {
    path: '/groups',
    component: MainLayout,
    children: [
      {
        path: '',
        name: 'Groups',
        component: () => import('@/views/gitlab/Groups.vue'),
        meta: { requiresAuth: true, title: '分组管理', icon: 'Grid' },
      },
    ],
  },
  {
    path: '/branches',
    component: MainLayout,
    children: [
      {
        path: '',
        name: 'Branches',
        component: () => import('@/views/gitlab/Branches.vue'),
        meta: { requiresAuth: true, title: '分支管理', icon: 'Operation' },
      },
    ],
  },
  {
    path: '/branch-rules',
    component: MainLayout,
    children: [
      {
        path: '',
        name: 'BranchRules',
        component: () => import('@/views/gitlab/BranchRules.vue'),
        meta: { requiresAuth: true, title: '分支规则', icon: 'Setting' },
      },
    ],
  },
  {
    path: '/branch-creation-history',
    component: MainLayout,
    children: [
      {
        path: '',
        name: 'BranchCreationHistory',
        component: () => import('@/views/BranchCreationHistory.vue'),
        meta: { requiresAuth: true, title: '分支创建历史', icon: 'Clock' },
      },
    ],
  },
  {
    path: '/branch-create',
    component: MainLayout,
    children: [
      {
        path: '',
        name: 'BranchCreate',
        component: () => import('@/views/BranchCreate.vue'),
        meta: { requiresAuth: true, title: '创建分支', icon: 'Plus' },
      },
    ],
  },
  {
    path: '/logs',
    component: MainLayout,
    children: [
      {
        path: '',
        name: 'Logs',
        component: () => import('@/views/logs/LogList.vue'),
        meta: { requiresAuth: true, title: '日志管理', icon: 'Document' },
      },
    ],
  },
  {
    path: '/todos',
    component: MainLayout,
    children: [
      {
        path: '',
        name: 'Todos',
        component: () => import('@/views/gitlab/Todos.vue'),
        meta: { requiresAuth: true, title: '待办列表', icon: 'List', requiresAdmin: true },
      },
    ],
  },
  {
    path: '/tasks',
    component: MainLayout,
    children: [
      {
        path: '',
        name: 'Tasks',
        component: () => import('@/views/tasks/TaskList.vue'),
        meta: { requiresAuth: true, title: '任务管理', icon: 'List' },
      },
    ],
  },
  {
    path: '/settings',
    component: MainLayout,
    children: [
      {
        path: '',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
        meta: { requiresAuth: true, title: '系统设置', icon: 'Tools' },
      },
    ],
  },
  {
    path: '/home-content',
    component: MainLayout,
    children: [
      {
        path: '',
        name: 'HomeContent',
        component: () => import('@/views/HomeContentManagement.vue'),
        meta: { requiresAuth: true, title: '首页内容维护', icon: 'EditPen', requiresAdmin: true },
      },
    ],
  },
  // 404 页面 - 必须放在最后
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { requiresAuth: false },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  // 检查路由是否需要认证
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth === true)
  const requiresAdmin = to.matched.some((record) => record.meta.requiresAdmin === true)
  
  if (requiresAuth && !userStore.isLoggedIn) {
    // 需要登录但未登录，重定向到首页
    if (to.path !== '/') {
      next('/')
    } else {
      next()
    }
  } else if (requiresAdmin && !userStore.user?.is_admin) {
    // 需要管理员权限但用户不是管理员
    ElMessage.warning('此功能仅限管理员使用')
    next('/dashboard')
  } else {
    // 不需要登录或已登录，放行
    next()
  }
})

export default router
