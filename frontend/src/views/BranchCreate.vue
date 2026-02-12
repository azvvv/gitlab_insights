<template>
  <div class="branch-create">
    <!-- 页面头部 - 优化设计 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon">
            <el-icon :size="32"><Grid /></el-icon>
          </div>
          <div class="header-text">
            <h1>创建分支</h1>
            <p class="page-description">在主仓库和所有子模块中创建新分支</p>
          </div>
        </div>
        <div class="header-right">
          <el-button type="primary" plain :icon="Timer" @click="handleViewHistory">
            查看历史记录
          </el-button>
        </div>
      </div>
    </div>

    <!-- 主表单 - 优化布局 -->
    <el-card class="form-card" shadow="never">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        label-position="top"
        class="modern-form"
      >
        <!-- 仓库选择 -->
        <div class="form-section">
          <div class="section-title">
            <el-icon><FolderOpened /></el-icon>
            <span>仓库配置</span>
          </div>
          <el-form-item label="选择仓库" prop="cascader_value">
            <el-cascader
              v-model="form.cascader_value"
              :options="cascaderOptions"
              :props="cascaderProps"
              placeholder="请选择分组和仓库"
              filterable
              clearable
              @change="handleCascaderChange"
              style="width: 100%"
              :show-all-levels="true"
              size="large"
            />
            <div class="form-hint">
              <el-icon><InfoFilled /></el-icon>
              先选择分组，再选择该分组下的仓库
            </div>
          </el-form-item>
        </div>

        <!-- 分支配置 -->
        <div class="form-section">
          <div class="section-title">
            <el-icon><Grid /></el-icon>
            <span>分支配置</span>
          </div>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="源分支/Tag" prop="source_ref">
                <el-input
                  v-model="form.source_ref"
                  placeholder="例如: master, develop, v1.0.0"
                  clearable
                  size="large"
                >
                  <template #prefix>
                    <el-icon><Grid /></el-icon>
                  </template>
                </el-input>
                <div class="form-hint">
                  <el-icon><InfoFilled /></el-icon>
                  从此分支或Tag创建新分支
                </div>
              </el-form-item>
            </el-col>
            
            <el-col :span="12">
              <el-form-item label="目标分支名" prop="new_branch_name">
                <el-input
                  v-model="form.new_branch_name"
                  placeholder="例如: feature/new-feature"
                  clearable
                  size="large"
                >
                  <template #prefix>
                    <el-icon><Plus /></el-icon>
                  </template>
                </el-input>
                <div class="form-hint">
                  <el-icon><InfoFilled /></el-icon>
                  在主仓库和所有子模块中创建
                </div>
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <!-- 业务信息 -->
        <div class="form-section">
          <div class="section-title">
            <el-icon><Ticket /></el-icon>
            <span>业务信息</span>
          </div>
          <el-form-item label="Jira工单号" prop="jira_ticket">
            <el-input
              v-model="form.jira_ticket"
              placeholder="请输入关联的Jira工单号，例如: PROJ-1234"
              clearable
              size="large"
            >
              <template #prefix>
                <el-icon><Ticket /></el-icon>
              </template>
            </el-input>
            <div class="form-hint required-hint">
              <el-icon><WarningFilled /></el-icon>
              必填项：记录创建此分支的业务原因或需求工单
            </div>
          </el-form-item>
        </div>

        <!-- 操作按钮 -->
        <el-form-item class="form-actions">
          <el-button
            type="primary"
            :loading="submitting"
            @click="handleSubmit"
            :icon="Check"
            size="large"
            class="submit-button"
          >
            {{ submitting ? '创建中...' : '创建分支' }}
          </el-button>
          <el-button
            @click="handleReset"
            :icon="RefreshLeft"
            size="large"
          >
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 进度对话框 -->
    <el-dialog
      v-model="progressVisible"
      title="创建分支中"
      width="500px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
      center
    >
      <div class="progress-content">
        <div class="progress-icon">
          <el-icon class="rotating" :size="60" color="#409EFF">
            <Loading />
          </el-icon>
        </div>
        
        <div class="progress-text">
          <h3>{{ progressMessage }}</h3>
          <p class="progress-hint">{{ progressHint }}</p>
        </div>
        
        <el-progress 
          :percentage="Math.floor(progressPercentage)" 
          :indeterminate="true"
          :duration="3"
          :stroke-width="8"
          :format="(percentage) => `${percentage}%`"
        />
        
        <div class="progress-stats">
          <div class="time-badge">
            <div class="time-icon">
              <el-icon :size="18"><Timer /></el-icon>
            </div>
            <div class="time-info">
              <span class="time-label">已耗时</span>
              <span class="time-value">{{ elapsedTime }}s</span>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 创建结果对话框 -->
    <el-dialog
      v-model="resultVisible"
      title="分支创建结果"
      width="900px"
      destroy-on-close
    >
      <div v-if="createResult" class="result-content">
        <!-- 父仓库结果 -->
        <div class="result-section">
          <h3>
            <el-icon :color="getParentStatusColor()"><FolderOpened /></el-icon>
            主仓库分支创建
          </h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="项目">
              {{ selectedProject?.name_with_namespace || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="分支名">
              {{ form.new_branch_name }}
            </el-descriptions-item>
            <el-descriptions-item label="源引用">
              {{ form.source_ref }}
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="getStatusTagType(createResult.parent_created)">
                {{ getStatusText(createResult.parent_created) }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 子模块结果 -->
        <div v-if="createResult.submodules && createResult.submodules.length > 0" class="result-section">
          <h3>
            <el-icon color="#409eff"><Files /></el-icon>
            子模块分支创建 ({{ createResult.submodules.length }})
          </h3>
          <el-table
            :data="createResult.submodules"
            border
            stripe
            style="width: 100%"
            max-height="400"
          >
            <el-table-column type="index" label="序号" width="60" align="center" />
            <el-table-column prop="project" label="子模块项目" min-width="200" show-overflow-tooltip />
            <el-table-column prop="url" label="URL" min-width="150" show-overflow-tooltip />
            <el-table-column prop="used_ref" label="使用的引用" min-width="120" show-overflow-tooltip>
              <template #default="{ row }">
                <span v-if="row.used_ref" class="source-ref">{{ row.used_ref }}</span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="140" align="center">
              <template #default="{ row }">
                <el-tag :type="getStatusTagType(row.status)" size="small">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>

          <!-- 统计信息 -->
          <div class="result-summary">
            <el-tag type="success" size="large">
              成功: {{ getSubmoduleStats().success }}
            </el-tag>
            <el-tag type="info" size="large">
              已存在: {{ getSubmoduleStats().exists }}
            </el-tag>
            <el-tag type="danger" size="large">
              失败: {{ getSubmoduleStats().failed }}
            </el-tag>
          </div>
        </div>

        <div v-else class="no-submodules">
          <el-empty description="该仓库没有子模块" />
        </div>
      </div>

      <template #footer>
        <el-button type="primary" @click="handleViewHistory">
          查看历史记录
        </el-button>
        <el-button @click="resultVisible = false">
          关闭
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  FolderOpened,
  Plus,
  Check,
  RefreshLeft,
  Files,
  Ticket,
  Loading,
  Timer,
  InfoFilled,
  WarningFilled,
  Grid
} from '@element-plus/icons-vue'
import { branchApi } from '@/api/branch'
import request from '@/api/request'

const router = useRouter()

// 数据
const formRef = ref(null)
const submitting = ref(false)
const projectsLoading = ref(false)
const resultVisible = ref(false)
const progressVisible = ref(false)
const progressMessage = ref('正在创建分支...')
const progressHint = ref('如果项目包含多个子模块，可能需要 1-2 分钟')
const progressPercentage = ref(0)
const elapsedTime = ref(0)
const groups = ref([])
const repositories = ref([])
const createResult = ref(null)
const selectedProject = ref(null)
const cascaderOptions = ref([])

// 级联选择器配置
const cascaderProps = {
  value: 'value',
  label: 'label',
  children: 'children',
  emitPath: false  // 只返回最后一级的值（仓库ID）
}

// 表单数据
const form = reactive({
  cascader_value: null,  // 级联选择器的值（仓库ID）
  group_name: '',
  project_id: null,
  project_name: '',
  source_ref: '',
  new_branch_name: '',
  jira_ticket: ''  // Jira工单号
})

// 表单验证规则
const rules = {
  cascader_value: [
    { required: true, message: '请选择仓库', trigger: 'change' }
  ],
  source_ref: [
    { required: true, message: '请输入源分支或Tag', trigger: 'blur' },
    { min: 1, message: '源分支名不能为空', trigger: 'blur' }
  ],
  new_branch_name: [
    { required: true, message: '请输入目标分支名', trigger: 'blur' },
    { min: 1, message: '分支名不能为空', trigger: 'blur' },
    {
      pattern: /^[a-zA-Z0-9_\-\/\.]+$/,
      message: '分支名只能包含字母、数字、下划线、中划线、斜杠和点',
      trigger: 'blur'
    }
  ],
  jira_ticket: [
    { required: true, message: '请输入Jira工单号', trigger: 'blur' },
    {
      pattern: /^[A-Z]+-\d+$/,
      message: 'Jira工单号格式不正确，应为: 项目键-数字，例如: PROJ-1234',
      trigger: 'blur'
    }
  ]
}

// 构建级联数据
const buildCascaderOptions = () => {
  // 按分组整理仓库
  const groupMap = new Map()
  
  repositories.value.forEach(repo => {
    const groupPath = repo.namespace_full_path || '未分组'
    
    if (!groupMap.has(groupPath)) {
      groupMap.set(groupPath, [])
    }
    
    groupMap.get(groupPath).push({
      value: repo.id,
      label: repo.name,
      fullPath: repo.name_with_namespace
    })
  })
  
  // 转换为级联格式
  const options = []
  groupMap.forEach((repos, groupPath) => {
    options.push({
      value: groupPath,
      label: groupPath,
      children: repos.sort((a, b) => a.label.localeCompare(b.label))
    })
  })
  
  cascaderOptions.value = options.sort((a, b) => a.label.localeCompare(b.label))
}

// 获取所有数据
const fetchAllData = async () => {
  projectsLoading.value = true
  try {
    const response = await request.get('/gitlab/repositories', {
      params: { all: 'true' }
    })
    if (response.success) {
      repositories.value = response.repositories || []
      buildCascaderOptions()
    }
  } catch (error) {
    console.error('获取仓库列表失败:', error)
    ElMessage.error('获取仓库列表失败')
  } finally {
    projectsLoading.value = false
  }
}

// 处理级联选择器变化
const handleCascaderChange = (value) => {
  console.log('Cascader changed, value:', value)
  if (value) {
    const repo = repositories.value.find(r => r.id === value)
    console.log('Found repository:', repo)
    if (repo) {
      form.project_id = repo.id
      form.project_name = repo.name
      form.group_name = repo.namespace_full_path || ''
      selectedProject.value = repo
      console.log('Updated form:', { project_id: form.project_id, project_name: form.project_name, group_name: form.group_name })
    }
  } else {
    form.project_id = null
    form.project_name = ''
    form.group_name = ''
    selectedProject.value = null
  }
}

// 提交表单
const handleSubmit = async () => {
  try {
    // 验证表单
    const valid = await formRef.value.validate()
    if (!valid) {
      return
    }

    // 预检查分支是否存在
    let branchExists = false
    try {
      const checkResponse = await branchApi.checkBranchExists(
        form.project_id,
        form.new_branch_name
      )
      if (checkResponse.success && checkResponse.data.exists) {
        branchExists = true
      }
    } catch (error) {
      console.warn('分支存在性检查失败:', error)
      // 检查失败不阻止流程，继续执行
    }

    // 确认对话框 - 根据分支是否存在显示不同的提示
    let confirmMessage = `确定要在仓库 "${selectedProject.value?.name_with_namespace}" 及其所有子模块中创建分支 "${form.new_branch_name}" 吗？`
    if (branchExists) {
      confirmMessage = `分支 "${form.new_branch_name}" 在仓库中已存在。\n\n继续创建将会记录一条新的创建记录（用于审计追踪），但不会覆盖现有分支。\n\n是否继续？`
    }
    
    const confirmed = await ElMessageBox.confirm(
      confirmMessage,
      branchExists ? '分支已存在' : '确认创建',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: branchExists ? 'warning' : 'warning',
        dangerouslyUseHTMLString: false,
      }
    ).catch(() => false)

    if (!confirmed) {
      return
    }

    submitting.value = true
    progressVisible.value = true
    progressMessage.value = '正在创建分支...'
    progressHint.value = '正在处理主仓库和子模块，请稍候'
    progressPercentage.value = 0
    elapsedTime.value = 0
    
    // 启动计时器
    const timer = setInterval(() => {
      elapsedTime.value++
      // 模拟进度增长（前60秒线性增长到80%，之后保持）
      if (elapsedTime.value <= 60) {
        progressPercentage.value = Math.min(80, (elapsedTime.value / 60) * 80)
      }
    }, 1000)

    try {
      // 获取当前用户信息
      const userInfo = JSON.parse(localStorage.getItem('user') || '{}')
      const createdBy = userInfo.username || userInfo.email || null
      
      // 调用API
      const response = await branchApi.createBranchWithSubmodules({
        group_name: form.group_name || '',
        project_name: form.project_name || '',
        project_id: form.project_id,
        source_ref: form.source_ref,
        new_branch_name: form.new_branch_name,
        jira_ticket: form.jira_ticket || null,
        created_by: createdBy
      })

      console.log('API 响应:', response)
      
      // 清除计时器
      clearInterval(timer)
      progressPercentage.value = 100
      progressMessage.value = '创建完成！'
      
      // 延迟关闭进度对话框，让用户看到完成状态
      setTimeout(() => {
        progressVisible.value = false
        
        if (response.success) {
          ElMessage.success('分支创建完成')
          createResult.value = response.data
          resultVisible.value = true
        } else {
          ElMessage.error(response.error || '创建分支失败')
        }
      }, 500)
      
    } catch (error) {
      // 清除计时器
      clearInterval(timer)
      progressVisible.value = false
      
      console.error('创建分支失败:', error)
      
      // 优化错误提示
      if (error.code === 'ECONNABORTED') {
        ElMessage.error('请求超时：创建分支耗时过长，请检查网络或联系管理员')
      } else {
        ElMessage.error(error.response?.data?.error || error.message || '创建分支失败')
      }
    } finally {
      submitting.value = false
    }
  } catch (outerError) {
    // 处理确认对话框取消等外层错误
    console.error('操作失败:', outerError)
    submitting.value = false
  }
}

// 重置表单
const handleReset = () => {
  formRef.value.resetFields()
  selectedProject.value = null
  form.cascader_value = ''
  form.project_id = ''
  form.project_name = ''
}

// 查看历史记录
const handleViewHistory = () => {
  resultVisible.value = false
  router.push('/branch-creation-history')
}

// 获取父仓库状态颜色
const getParentStatusColor = () => {
  if (!createResult.value) return '#909399'
  const status = createResult.value.parent_created
  if (status === 'created') return '#67c23a'
  if (status === 'already_exists') return '#409eff'
  return '#f56c6c'
}

// 获取状态标签类型
const getStatusTagType = (status) => {
  if (!status) return 'info'
  if (status === 'created') return 'success'
  if (status === 'already_exists') return 'info'
  if (status.startsWith('failed') || status.startsWith('create_failed') || status === 'not_found' || status === 'invalid_url' || status.includes('error')) {
    return 'danger'
  }
  return 'warning'
}

// 获取状态文本
const getStatusText = (status) => {
  if (!status) return '未知'
  if (status === 'created') return '创建成功'
  if (status === 'already_exists') return '已存在'
  if (status === 'not_found') return '未找到项目'
  if (status === 'invalid_url') return '无效URL'
  if (status.startsWith('failed:')) return '失败'
  if (status.startsWith('create_failed:')) return '创建失败'
  if (status.includes('error')) return '错误'
  return status
}

// 获取子模块统计
const getSubmoduleStats = () => {
  if (!createResult.value || !createResult.value.submodules) {
    return { success: 0, exists: 0, failed: 0 }
  }
  
  const stats = {
    success: 0,
    exists: 0,
    failed: 0
  }
  
  createResult.value.submodules.forEach(sub => {
    if (sub.status === 'created') {
      stats.success++
    } else if (sub.status === 'already_exists') {
      stats.exists++
    } else {
      stats.failed++
    }
  })
  
  return stats
}

// 初始化
onMounted(() => {
  fetchAllData()
})
</script>

<style scoped lang="scss">
.branch-create {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%);
  padding: 32px;

  .page-header {
    margin-bottom: 32px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 16px;
    padding: 32px;
    box-shadow: 0 8px 24px rgba(102, 126, 234, 0.25);

    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .header-left {
        display: flex;
        align-items: center;
        gap: 20px;

        .header-icon {
          width: 64px;
          height: 64px;
          background: rgba(255, 255, 255, 0.2);
          border-radius: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #fff;
          backdrop-filter: blur(10px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        .header-text {
          h1 {
            margin: 0;
            font-size: 32px;
            font-weight: 700;
            color: #fff;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
          }

          .page-description {
            margin: 8px 0 0;
            color: rgba(255, 255, 255, 0.9);
            font-size: 15px;
            font-weight: 400;
          }
        }
      }

      .header-right {
        .el-button {
          border-color: rgba(255, 255, 255, 0.4);
          color: #fff;
          background: rgba(255, 255, 255, 0.15);
          backdrop-filter: blur(10px);

          &:hover {
            background: rgba(255, 255, 255, 0.25);
            border-color: rgba(255, 255, 255, 0.6);
          }
        }
      }
    }
  }

  .form-card {
    max-width: 1200px;
    margin: 0 auto;
    border-radius: 16px;
    border: none;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);

    :deep(.el-card__body) {
      padding: 40px;
    }

    .modern-form {
      .form-section {
        margin-bottom: 40px;
        padding-bottom: 32px;
        border-bottom: 1px solid #e8eef5;

        &:last-of-type {
          border-bottom: none;
          margin-bottom: 0;
          padding-bottom: 0;
        }

        .section-title {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 24px;
          font-size: 18px;
          font-weight: 600;
          color: #303133;

          .el-icon {
            font-size: 22px;
            color: #667eea;
          }
        }

        .el-form-item {
          margin-bottom: 24px;

          :deep(.el-form-item__label) {
            font-weight: 500;
            color: #606266;
            font-size: 14px;
            margin-bottom: 8px;
            height: auto;
            line-height: 1.5;
          }

          .el-input {
            :deep(.el-input__wrapper) {
              border-radius: 8px;
              box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
              transition: all 0.3s ease;

              &:hover {
                box-shadow: 0 2px 12px rgba(102, 126, 234, 0.15);
              }

              &.is-focus {
                box-shadow: 0 2px 12px rgba(102, 126, 234, 0.25);
              }
            }
          }

          .el-cascader {
            :deep(.el-input__wrapper) {
              border-radius: 8px;
              box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
              transition: all 0.3s ease;

              &:hover {
                box-shadow: 0 2px 12px rgba(102, 126, 234, 0.15);
              }

              &.is-focus {
                box-shadow: 0 2px 12px rgba(102, 126, 234, 0.25);
              }
            }
          }
        }

        .form-hint {
          display: flex;
          align-items: center;
          gap: 6px;
          margin-top: 8px;
          font-size: 13px;
          color: #909399;
          line-height: 1.6;

          .el-icon {
            font-size: 14px;
            flex-shrink: 0;
          }

          &.required-hint {
            color: #f56c6c;

            .el-icon {
              color: #f56c6c;
            }
          }
        }
      }

      .form-actions {
        margin-top: 40px;
        margin-bottom: 0;
        text-align: center;

        :deep(.el-form-item__content) {
          display: flex;
          justify-content: center;
          gap: 16px;
        }

        .submit-button {
          min-width: 180px;
          height: 48px;
          font-size: 16px;
          font-weight: 500;
          border-radius: 24px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border: none;
          box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
          transition: all 0.3s ease;

          &:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
          }

          &:active {
            transform: translateY(0);
          }
        }

        .el-button:not(.submit-button) {
          min-width: 120px;
          height: 48px;
          font-size: 16px;
          border-radius: 24px;
        }
      }
    }
  }

  // 进度对话框样式
  .progress-content {
    text-align: center;
    padding: 20px;

    .progress-icon {
      margin-bottom: 24px;

      .rotating {
        animation: rotate 2s linear infinite;
      }
    }

    .progress-text {
      margin-bottom: 24px;

      h3 {
        margin: 0 0 8px 0;
        font-size: 18px;
        color: #303133;
        font-weight: 500;
      }

      .progress-hint {
        margin: 0;
        font-size: 13px;
        color: #909399;
        line-height: 1.6;
      }
    }

    .el-progress {
      margin-bottom: 20px;
    }

    .progress-stats {
      display: flex;
      justify-content: center;
      margin-top: 24px;

      .time-badge {
        display: inline-flex;
        align-items: center;
        gap: 12px;
        padding: 12px 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        transition: all 0.3s ease;

        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
        }

        .time-icon {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 36px;
          height: 36px;
          background: rgba(255, 255, 255, 0.2);
          border-radius: 50%;
          color: #fff;
          animation: pulse 2s ease-in-out infinite;
        }

        .time-info {
          display: flex;
          flex-direction: column;
          align-items: flex-start;

          .time-label {
            font-size: 11px;
            color: rgba(255, 255, 255, 0.8);
            font-weight: 400;
            line-height: 1;
            margin-bottom: 4px;
          }

          .time-value {
            font-size: 20px;
            color: #fff;
            font-weight: 600;
            line-height: 1;
            font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
          }
        }
      }
    }
  }

  @keyframes rotate {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }

  @keyframes pulse {
    0%, 100% {
      transform: scale(1);
      opacity: 1;
    }
    50% {
      transform: scale(1.1);
      opacity: 0.8;
    }
  }

  .result-content {
    .result-section {
      margin-bottom: 24px;

      h3 {
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 0 0 16px 0;
        font-size: 16px;
        color: #303133;
      }

      .source-ref {
        font-family: 'Courier New', monospace;
        font-size: 13px;
        color: #606266;
      }

      .result-summary {
        margin-top: 16px;
        display: flex;
        gap: 12px;
        justify-content: center;
      }
    }

    .no-submodules {
      padding: 20px 0;
    }
  }
}
</style>
