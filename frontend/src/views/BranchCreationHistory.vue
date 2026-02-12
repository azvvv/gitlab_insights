<template>
  <div class="branch-creation-history">
    <div class="page-header">
      <h1>分支创建历史</h1>
      <p class="page-description">查看和管理所有分支创建记录（按 Jira 工单分组）</p>
    </div>

    <!-- 统计卡片和筛选条件 -->
    <el-row :gutter="20" class="top-section">
      <!-- 搜索和筛选 -->
      <el-col :span="24">
        <el-card class="filter-card" shadow="never">
          <div class="filter-header">
            <span class="filter-title">
              <el-icon><Filter /></el-icon>
              筛选条件
            </span>
          </div>
      
      <el-form :inline="true" :model="queryParams" class="filter-form" label-position="top">
        <el-row :gutter="12">
          <el-col :span="6">
            <el-form-item label="Jira工单号">
              <el-input
                v-model="jiraTicketSearch"
                placeholder="如: PROJ-123"
                clearable
                @clear="handleQuery"
                @input="handleJiraTicketSearch"
                size="small"
              >
                <template #prefix>
                  <el-icon><Ticket /></el-icon>
                </template>
              </el-input>
            </el-form-item>
          </el-col>

          <el-col :span="7">
            <el-form-item label="项目/分支">
              <el-input
                v-model="queryParams.search"
                placeholder="搜索项目名、分支名..."
                clearable
                @clear="handleQuery"
                size="small"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </el-form-item>
          </el-col>

          <el-col :span="5">
            <el-form-item label="状态">
              <el-select
                v-model="queryParams.status"
                placeholder="全部状态"
                clearable
                @change="handleQuery"
                size="small"
                style="width: 100%"
              >
                <el-option label="创建成功" value="created">
                  <span style="display: flex; align-items: center; gap: 8px;">
                    <el-tag type="success" size="small" effect="plain">成功</el-tag>
                    创建成功
                  </span>
                </el-option>
                <el-option label="已存在" value="already_exists">
                  <span style="display: flex; align-items: center; gap: 8px;">
                    <el-tag type="info" size="small" effect="plain">已存在</el-tag>
                    已存在
                  </span>
                </el-option>
                <el-option label="失败" value="failed">
                  <span style="display: flex; align-items: center; gap: 8px;">
                    <el-tag type="danger" size="small" effect="plain">失败</el-tag>
                    失败
                  </span>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :span="6">
            <el-form-item label="日期范围">
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
                @change="handleDateChange"
                size="small"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row>
          <el-col :span="24" class="filter-actions">
            <el-button type="primary" @click="handleQuery" :icon="Search" size="small">
              搜索
            </el-button>
            <el-button @click="handleReset" :icon="Refresh" size="small">
              重置
            </el-button>
          </el-col>
        </el-row>
      </el-form>
        </el-card>
      </el-col>
    </el-row>

    <!-- 按 Jira Ticket 分组的折叠面板 -->
    <el-card class="collapse-card" v-loading="loading">
      <div v-if="groupedData.length === 0" class="empty-state">
        <el-empty description="暂无数据" />
      </div>
      
      <el-collapse v-else v-model="activeCollapses">
        <el-collapse-item
          v-for="group in groupedData"
          :key="group.jiraTicket"
          :name="group.jiraTicket"
        >
          <!-- 折叠面板标题 -->
          <template #title>
            <div class="collapse-title">
              <el-tag type="primary" size="large" effect="dark">
                <el-icon style="margin-right: 6px"><Ticket /></el-icon>
                {{ group.jiraTicket || '未关联工单' }}
              </el-tag>
              <el-divider direction="vertical" />
              <span class="record-count">
                <el-icon><Document /></el-icon>
                {{ group.records.length }} 条记录
              </span>
              <el-divider direction="vertical" />
              <span class="time-range">
                <el-icon><Clock /></el-icon>
                {{ formatDate(group.latestTime) }}
              </span>
              <el-divider direction="vertical" />
              <span class="creator" v-if="group.createdBy">
                <el-icon><User /></el-icon>
                {{ group.createdBy }}
              </span>
            </div>
          </template>

          <!-- 折叠面板内容 - 数据表格 -->
          <el-table
            :data="group.records"
            stripe
            border
            style="width: 100%"
            size="small"
          >
            <el-table-column type="index" label="序号" width="60" align="center" />
            
            <el-table-column
              prop="project_path"
              label="项目路径"
              min-width="200"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                <div class="project-cell">
                  <el-icon class="project-icon"><FolderOpened /></el-icon>
                  <span>{{ row.project_path || row.project_name }}</span>
                </div>
              </template>
            </el-table-column>

            <el-table-column
              prop="branch_name"
              label="分支名称"
              min-width="180"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                <el-tag type="info" effect="plain">
                  <el-icon style="margin-right: 4px"><BranchesOutlined /></el-icon>
                  {{ row.branch_name }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column
              prop="source_ref"
              label="源引用"
              min-width="150"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                <span class="source-ref">{{ row.source_ref || '-' }}</span>
              </template>
            </el-table-column>

            <el-table-column
              prop="source_commit"
              label="源提交"
              min-width="120"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                <span v-if="row.source_commit" class="commit-sha">
                  {{ row.source_commit.substring(0, 8) }}
                </span>
                <span v-else class="text-muted">-</span>
              </template>
            </el-table-column>

            <el-table-column
              prop="status"
              label="状态"
              width="120"
              align="center"
            >
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column
              prop="message"
              label="消息"
              min-width="200"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                <span v-if="row.message" class="message-text">{{ row.message }}</span>
                <span v-else class="text-muted">-</span>
              </template>
            </el-table-column>

            <el-table-column
              prop="created_at"
              label="创建时间"
              width="180"
              sortable
            >
              <template #default="{ row }">
                <div class="time-cell">
                  <el-icon><Clock /></el-icon>
                  <span>{{ formatDateTime(row.created_at) }}</span>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-collapse-item>
      </el-collapse>
      
      <!-- 数据统计信息 -->
      <div class="data-summary" v-if="tableData.length > 0">
        <el-divider />
        <div class="summary-text">
          <el-icon><Document /></el-icon>
          <span>共 {{ total }} 条记录，分为 {{ groupedData.length }} 个工单</span>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Search,
  Refresh,
  Clock,
  Calendar,
  CircleCheck,
  FolderOpened,
  Ticket,
  Document,
  User,
  Filter
} from '@element-plus/icons-vue'
import { getBranchCreationRecords } from '@/api/branchCreation'

// 注意：BranchesOutlined 组件需要在项目中创建或使用 element-plus 的分支图标
// 暂时使用一个简单的替代方案
const BranchesOutlined = { template: '<i class="el-icon-branch"></i>' }

// 数据
const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const dateRange = ref([])
const activeCollapses = ref([])

// 查询参数
const queryParams = reactive({
  page: 1,
  pageSize: 20,
  search: '',
  status: '',
  startDate: '',
  endDate: ''
})

// 单独的 jiraTicket 搜索框值（用于 UI 显示）
const jiraTicketSearch = ref('')

// 按 Jira Ticket 分组数据
const groupedData = computed(() => {
  const groups = new Map()
  
  tableData.value.forEach(record => {
    const jiraTicket = record.jira_ticket || '未关联工单'
    
    if (!groups.has(jiraTicket)) {
      groups.set(jiraTicket, {
        jiraTicket: jiraTicket,
        records: [],
        latestTime: record.created_at,
        createdBy: record.created_by
      })
    }
    
    const group = groups.get(jiraTicket)
    group.records.push(record)
    
    // 更新最新时间
    if (record.created_at > group.latestTime) {
      group.latestTime = record.created_at
    }
  })
  
  // 转换为数组并按最新时间排序
  return Array.from(groups.values()).sort((a, b) => {
    return new Date(b.latestTime) - new Date(a.latestTime)
  })
})

// 获取列表数据
const fetchData = async () => {
  loading.value = true
  try {
    // 获取所有数据（不分页），以便正确按 ticket 分组
    const allDataParams = {
      ...queryParams,
      page: 1,
      pageSize: 10000  // 获取所有数据
    }
    
    const response = await getBranchCreationRecords(allDataParams)
    if (response.success) {
      const data = response.data
      tableData.value = data.records
      total.value = data.total
      
      // 默认不展开任何 ticket（合并状态）
      activeCollapses.value = []
    } else {
      ElMessage.error(response.error || '获取数据失败')
    }
  } catch (error) {
    console.error('获取数据失败:', error)
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

// 处理搜索
const handleQuery = () => {
  queryParams.page = 1
  fetchData()
}

// 处理 Jira Ticket 搜索
const handleJiraTicketSearch = () => {
  // 将 jiraTicket 的值同步到 search 参数中
  queryParams.search = jiraTicketSearch.value
  handleQuery()
}

// 处理重置
const handleReset = () => {
  Object.assign(queryParams, {
    page: 1,
    pageSize: 20,
    search: '',
    status: '',
    startDate: '',
    endDate: ''
  })
  jiraTicketSearch.value = ''
  dateRange.value = []
  fetchData()
}

// 处理日期变化
const handleDateChange = (dates) => {
  if (dates && dates.length === 2) {
    queryParams.startDate = dates[0]
    queryParams.endDate = dates[1]
  } else {
    queryParams.startDate = ''
    queryParams.endDate = ''
  }
  handleQuery()
}

// 格式化日期时间
const formatDateTime = (dateTimeStr) => {
  if (!dateTimeStr) return '-'
  const date = new Date(dateTimeStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 格式化日期
const formatDate = (dateTimeStr) => {
  if (!dateTimeStr) return '-'
  const date = new Date(dateTimeStr)
  return date.toLocaleDateString('zh-CN')
}

// 获取状态类型
const getStatusType = (status) => {
  const typeMap = {
    'created': 'success',
    'already_exists': 'info',
    'failed': 'danger',
    'pending': 'warning'
  }
  return typeMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const textMap = {
    'created': '创建成功',
    'already_exists': '已存在',
    'failed': '失败',
    'pending': '处理中'
  }
  return textMap[status] || status
}

// 初始化
onMounted(() => {
  fetchData()
})
</script>

<style scoped lang="scss">
.branch-creation-history {
  padding: 20px;
  
  .page-header {
    margin-bottom: 24px;
    
    h1 {
      font-size: 24px;
      font-weight: 600;
      color: #303133;
      margin: 0 0 8px 0;
    }
    
    .page-description {
      font-size: 14px;
      color: #909399;
      margin: 0;
    }
  }
  
  .top-section {
    margin-bottom: 20px;
  }
  
  .stats-cards-compact {
    display: flex;
    flex-direction: column;
    gap: 8px;
    
    .stat-card-compact {
      cursor: default;
      
      :deep(.el-card__body) {
        padding: 12px 16px;
      }
      
      .stat-content-compact {
        display: flex;
        align-items: center;
        gap: 12px;
        
        .stat-icon-compact {
          width: 36px;
          height: 36px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 18px;
          flex-shrink: 0;
          
          &.success {
            background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
            color: white;
          }
          
          &.primary {
            background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
            color: white;
          }
          
          &.info {
            background: linear-gradient(135deg, #909399 0%, #b1b3b8 100%);
            color: white;
          }
          
          &.warning {
            background: linear-gradient(135deg, #e6a23c 0%, #ebb563 100%);
            color: white;
          }
        }
        
        .stat-info-compact {
          flex: 1;
          
          .stat-value-compact {
            font-size: 20px;
            font-weight: 600;
            color: #303133;
            line-height: 1;
            margin-bottom: 4px;
          }
          
          .stat-label-compact {
            font-size: 12px;
            color: #909399;
          }
        }
      }
    }
  }
  
  .stats-cards-vertical {
    display: flex;
    flex-direction: column;
    gap: 12px;
    height: 100%;
    
    .stat-card {
      cursor: default;
      flex: 1;
      
      :deep(.el-card__body) {
        padding: 16px;
        height: 100%;
      }
      
      .stat-content {
        display: flex;
        align-items: center;
        gap: 12px;
        height: 100%;
        
        .stat-icon {
          width: 48px;
          height: 48px;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 24px;
          flex-shrink: 0;
          
          &.success {
            background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
            color: white;
          }
          
          &.info {
            background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
            color: white;
          }
          
          &.warning {
            background: linear-gradient(135deg, #e6a23c 0%, #ebb563 100%);
            color: white;
          }
        }
        
        .stat-info {
          flex: 1;
          
          .stat-value {
            font-size: 24px;
            font-weight: 600;
            color: #303133;
            line-height: 1;
            margin-bottom: 6px;
          }
          
          .stat-label {
            font-size: 13px;
            color: #909399;
          }
        }
      }
    }
  }
  
  .stats-cards {
    margin-bottom: 20px;
    
    .stat-card {
      cursor: default;
      
      :deep(.el-card__body) {
        padding: 20px;
      }
      
      .stat-content {
        display: flex;
        align-items: center;
        gap: 16px;
        
        .stat-icon {
          width: 56px;
          height: 56px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 28px;
          
          &.success {
            background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
            color: white;
          }
          
          &.info {
            background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
            color: white;
          }
          
          &.warning {
            background: linear-gradient(135deg, #e6a23c 0%, #ebb563 100%);
            color: white;
          }
        }
        
        .stat-info {
          flex: 1;
          
          .stat-value {
            font-size: 28px;
            font-weight: 600;
            color: #303133;
            line-height: 1;
            margin-bottom: 8px;
          }
          
          .stat-label {
            font-size: 14px;
            color: #909399;
          }
        }
      }
    }
  }
  
  .filter-card {
    background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
    border: 1px solid #e4e7ed;
    
    :deep(.el-card__body) {
      padding: 16px;
    }
    
    .filter-header {
      margin-bottom: 12px;
      padding-bottom: 10px;
      border-bottom: 2px solid #e4e7ed;
      
      .filter-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        font-weight: 600;
        color: #303133;
        
        .el-icon {
          color: #409eff;
          font-size: 16px;
        }
      }
    }
    
    .filter-form {
      
      :deep(.el-form-item__label) {
        font-weight: 500;
        color: #606266;
        padding-bottom: 4px;
        font-size: 12px;
      }
      
      :deep(.el-form-item) {
        margin-bottom: 10px;
      }
      
      :deep(.el-input__wrapper) {
        box-shadow: 0 0 0 1px #dcdfe6 inset;
        transition: all 0.3s;
        
        &:hover {
          box-shadow: 0 0 0 1px #c0c4cc inset;
        }
      }
      
      :deep(.el-input__wrapper.is-focus) {
        box-shadow: 0 0 0 1px #409eff inset;
      }
      
      .filter-actions {
        display: flex;
        justify-content: flex-end;
        gap: 10px;
        padding-top: 10px;
        border-top: 1px dashed #e4e7ed;
      }
    }
  }
  
  .collapse-card {
    .empty-state {
      padding: 40px 0;
    }
    
    .collapse-title {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 14px;
      color: #606266;
      flex: 1;
      padding-right: 20px;
      
      .record-count,
      .time-range,
      .creator {
        display: flex;
        align-items: center;
        gap: 4px;
      }
    }
    
    :deep(.el-collapse-item__header) {
      height: auto;
      padding: 16px 20px;
      font-size: 16px;
      font-weight: 500;
      border: none;
    }
    
    :deep(.el-collapse-item__wrap) {
      border: none;
    }
    
    :deep(.el-collapse-item) {
      border: none;
      margin-bottom: 16px;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    }
    
    :deep(.el-collapse-item__content) {
      padding-bottom: 20px;
      border: none;
    }
    
    .project-cell {
      display: flex;
      align-items: center;
      gap: 8px;
      
      .project-icon {
        color: #409eff;
        font-size: 16px;
      }
    }
    
    .commit-sha {
      font-family: 'Courier New', monospace;
      font-size: 12px;
      color: #606266;
      background: #f5f7fa;
      padding: 2px 6px;
      border-radius: 3px;
    }
    
    .time-cell {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
      color: #606266;
    }
    
    .message-text {
      font-size: 13px;
      color: #606266;
      line-height: 1.5;
    }
    
    .text-muted {
      color: #c0c4cc;
    }
    
    .data-summary {
      margin-top: 20px;
      
      .summary-text {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        color: #606266;
        font-size: 14px;
        
        .el-icon {
          color: #409eff;
        }
      }
    }
  }
}
</style>
