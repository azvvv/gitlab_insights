<template>
  <div class="todos-container">
    <el-card class="page-header" shadow="never">
      <div class="header-content">
        <div>
          <h2>待办列表</h2>
          <p class="description">管理GitLab待办事项，快速查看需要处理的MR和Issue</p>
        </div>
        <div class="header-actions">
          <el-button
            type="primary"
            :icon="Refresh"
            @click="loadTodos"
            :loading="loading"
          >
            刷新
          </el-button>
          <el-button
            type="success"
            :icon="Select"
            @click="handleMarkAllDone"
            :disabled="!todos.length"
          >
            全部标记完成
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 过滤条件 -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="状态">
          <el-select v-model="filters.state" placeholder="请选择" @change="handleFilterChange">
            <el-option label="待处理" value="pending" />
            <el-option label="已完成" value="done" />
            <el-option label="全部" value="all" />
          </el-select>
        </el-form-item>

        <el-form-item label="类型">
          <el-select v-model="filters.type" placeholder="全部类型" clearable @change="handleFilterChange">
            <el-option label="MR" value="MergeRequest" />
            <el-option label="Issue" value="Issue" />
            <el-option label="Epic" value="Epic" />
          </el-select>
        </el-form-item>

        <el-form-item label="操作">
          <el-select v-model="filters.action" placeholder="全部操作" clearable @change="handleFilterChange">
            <el-option label="分配给你" value="assigned" />
            <el-option label="请求审查" value="review_requested" />
            <el-option label="提到了你" value="mentioned" />
            <el-option label="直接提到" value="directly_addressed" />
            <el-option label="无法合并" value="unmergeable" />
            <el-option label="构建失败" value="build_failed" />
            <el-option label="需要审批" value="approval_required" />
          </el-select>
        </el-form-item>

        <el-form-item label="项目">
          <el-input
            v-model="filters.project_name"
            placeholder="输入项目名称"
            clearable
            @change="handleFilterChange"
            style="width: 200px"
          />
        </el-form-item>

        <el-form-item label="目标分支">
          <el-input
            v-model="filters.branch"
            placeholder="输入分支名称"
            clearable
            @change="handleFilterChange"
            style="width: 180px"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 待办事项列表 -->
    <el-card class="todos-list" shadow="never" v-loading="loading">
      <div v-if="!todos.length && !loading" class="empty-state">
        <el-empty description="没有待办事项" />
      </div>

      <div v-else class="todos-content">
        <div class="todos-header">
          <span class="total-count">共 {{ total }} 个待办事项</span>
        </div>

        <!-- 按项目分组 -->
        <div
          v-for="(projectTodos, projectName) in groupedTodos"
          :key="projectName"
          class="project-group"
        >
          <div class="project-header">
            <el-icon><FolderOpened /></el-icon>
            <span class="project-name">{{ projectName }}</span>
            <el-tag size="small" type="info">{{ projectTodos.length }}</el-tag>
          </div>

          <div class="todos-items">
            <div
              v-for="todo in projectTodos"
              :key="todo.id"
              class="todo-item"
              :class="{ 'todo-done': todo.state === 'done' }"
            >
              <div class="todo-main">
                <div class="todo-header-row">
                  <div class="todo-left">
                    <el-icon class="todo-status-icon" :class="todo.state === 'done' ? 'done' : 'pending'">
                      <component :is="todo.state === 'done' ? CircleCheck : CircleClose" />
                    </el-icon>
                    <el-tag size="small" :type="getTypeColor(todo.target_type)">
                      {{ getTypeLabel(todo.target_type) }}
                    </el-tag>
                    <el-tag size="small" type="warning">{{ todo.action_name }}</el-tag>
                  </div>
                  <div class="todo-actions">
                    <el-button
                      v-if="todo.state === 'pending'"
                      type="success"
                      size="small"
                      :icon="Select"
                      @click="handleMarkDone(todo.id)"
                    >
                      标记完成
                    </el-button>
                  </div>
                </div>

                <div class="todo-title">
                  <a :href="todo.target_url" target="_blank" class="title-link">
                    {{ todo.title }}
                  </a>
                </div>

                <div class="todo-meta">
                  <span class="meta-item">
                    <el-icon><User /></el-icon>
                    作者: {{ todo.author.name }}
                  </span>
                  <span class="meta-item">
                    <el-icon><Clock /></el-icon>
                    时间: {{ formatDate(todo.created_at) }}
                  </span>
                  <span v-if="todo.source_branch && todo.target_branch" class="meta-item branch-info">
                    <el-icon><Operation /></el-icon>
                    分支: {{ todo.source_branch }} → {{ todo.target_branch }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh,
  Select,
  FolderOpened,
  CircleCheck,
  CircleClose,
  User,
  Clock,
  Operation,
} from '@element-plus/icons-vue'
import { gitlabApi } from '@/api'

// 数据
const loading = ref(false)
const todos = ref([])
const total = ref(0)

// 过滤条件
const filters = ref({
  state: 'pending',
  type: '',
  action: '',
  project_name: '',
  branch: '',
})

// 按项目分组
const groupedTodos = computed(() => {
  const groups = {}
  todos.value.forEach((todo) => {
    const projectName = todo.project.name_with_namespace
    if (!groups[projectName]) {
      groups[projectName] = []
    }
    groups[projectName].push(todo)
  })
  return groups
})

// 加载待办事项
const loadTodos = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.value.state) params.state = filters.value.state
    if (filters.value.type) params.type = filters.value.type
    if (filters.value.action) params.action = filters.value.action
    if (filters.value.project_name) params.project_name = filters.value.project_name
    if (filters.value.branch) params.branch = filters.value.branch

    const response = await gitlabApi.getTodos(params)
    if (response && response.success) {
      todos.value = response.todos || []
      total.value = response.total || 0
    } else {
      ElMessage.error(response?.error || '获取待办事项失败')
      todos.value = []
      total.value = 0
    }
  } catch (error) {
    console.error('加载待办事项失败:', error)
    ElMessage.error(error.response?.data?.error || error.message || '加载待办事项失败')
    todos.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 标记单个待办事项为完成
const handleMarkDone = async (todoId) => {
  try {
    await ElMessageBox.confirm('确定要标记此待办事项为完成吗？', '确认', {
      type: 'warning',
    })

    const response = await gitlabApi.markTodoDone(todoId)
    if (response && response.success) {
      ElMessage.success(response.message || '标记成功')
      loadTodos()
    } else {
      ElMessage.error(response?.error || '标记失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('标记待办事项失败:', error)
      ElMessage.error(error.response?.data?.error || error.message || '标记待办事项失败')
    }
  }
}

// 标记所有待办事项为完成
const handleMarkAllDone = async () => {
  try {
    await ElMessageBox.confirm('确定要标记所有待办事项为完成吗？', '确认', {
      type: 'warning',
    })

    const response = await gitlabApi.markAllTodosDone()
    if (response && response.success) {
      ElMessage.success(response.message || '全部标记成功')
      loadTodos()
    } else {
      ElMessage.error(response?.error || '标记失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('标记所有待办事项失败:', error)
      ElMessage.error(error.response?.data?.error || error.message || '标记所有待办事项失败')
    }
  }
}

// 搜索
const handleSearch = () => {
  loadTodos()
}

// 重置过滤条件
const handleReset = () => {
  filters.value = {
    state: 'pending',
    type: '',
    action: '',
    project_name: '',
    branch: '',
  }
  loadTodos()
}

// 过滤条件改变
const handleFilterChange = () => {
  loadTodos()
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// 获取类型标签
const getTypeLabel = (type) => {
  const map = {
    MergeRequest: 'MR',
    Issue: 'Issue',
    Epic: 'Epic',
    'DesignManagement::Design': 'Design',
    'AlertManagement::Alert': 'Alert',
  }
  return map[type] || type
}

// 获取类型颜色
const getTypeColor = (type) => {
  const map = {
    MergeRequest: 'primary',
    Issue: 'warning',
    Epic: 'success',
  }
  return map[type] || 'info'
}

// 初始化
onMounted(() => {
  loadTodos()
})
</script>

<style scoped>
.todos-container {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #303133;
}

.description {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-form {
  margin: 0;
}

.todos-list {
  min-height: 400px;
}

.empty-state {
  padding: 60px 0;
  text-align: center;
}

.todos-content {
  padding: 10px 0;
}

.todos-header {
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}

.total-count {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.project-group {
  margin-bottom: 30px;
}

.project-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 12px;
}

.project-name {
  font-size: 15px;
  font-weight: 500;
  color: #303133;
  flex: 1;
}

.todos-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.todo-item {
  padding: 16px;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  transition: all 0.3s;
}

.todo-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 12px 0 rgba(64, 158, 255, 0.1);
}

.todo-item.todo-done {
  opacity: 0.6;
}

.todo-main {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.todo-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.todo-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.todo-status-icon {
  font-size: 20px;
}

.todo-status-icon.pending {
  color: #e6a23c;
}

.todo-status-icon.done {
  color: #67c23a;
}

.todo-title {
  font-size: 15px;
  line-height: 1.5;
}

.title-link {
  color: #303133;
  text-decoration: none;
  font-weight: 500;
}

.title-link:hover {
  color: #409eff;
  text-decoration: underline;
}

.todo-meta {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  font-size: 13px;
  color: #909399;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.branch-info {
  color: #67c23a;
  font-family: monospace;
}
</style>
