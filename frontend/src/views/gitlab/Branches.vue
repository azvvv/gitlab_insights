<template>
  <div class="branches">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>分支管理</span>
          <div>
            <el-button 
              v-if="activeTab === 'analysis'"
              type="success" 
              icon="Refresh" 
              @click="handleRefreshSummaryData"
              :loading="refreshingSummary"
            >
              刷新数据
            </el-button>
            <el-button 
              v-if="activeTab === 'analysis'"
              type="primary" 
              icon="Download" 
              @click="exportData"
            >
              导出数据
            </el-button>
            <el-button 
              v-if="activeTab === 'list'"
              type="warning" 
              icon="Download" 
              @click="exportDeletionReport"
              :loading="deletionReportLoading"
            >
              导出删除分析报告
            </el-button>
            <el-button 
              v-if="activeTab === 'list'"
              type="primary" 
              icon="Refresh" 
              @click="handleSync"
            >
              同步分支
            </el-button>
          </div>
        </div>
      </template>

      <!-- Tab 切换 -->
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- 分支分类分析 Tab -->
        <el-tab-pane label="分支分类分析" name="analysis">
          <div class="analysis-content">
            <!-- 统计卡片 -->
            <el-row :gutter="20" class="stats-row">
              <el-col :xs="24" :sm="12" :md="6">
                <el-card class="stat-card total">
                  <div class="stat-content">
                    <el-icon class="stat-icon"><FolderOpened /></el-icon>
                    <div class="stat-info">
                      <div class="stat-value">{{ totalBranches }}</div>
                      <div class="stat-label">分支总数</div>
                    </div>
                  </div>
                </el-card>
              </el-col>
              
              <el-col :xs="24" :sm="12" :md="6">
                <el-card class="stat-card active">
                  <div class="stat-content">
                    <el-icon class="stat-icon"><CircleCheck /></el-icon>
                    <div class="stat-info">
                      <div class="stat-value">{{ activeBranchCount }}</div>
                      <div class="stat-label">活跃分支</div>
                    </div>
                  </div>
                </el-card>
              </el-col>
              
              <el-col :xs="24" :sm="12" :md="6">
                <el-card class="stat-card protected">
                  <div class="stat-content">
                    <el-icon class="stat-icon"><Lock /></el-icon>
                    <div class="stat-info">
                      <div class="stat-value">{{ protectedBranchCount }}</div>
                      <div class="stat-label">受保护分支</div>
                    </div>
                  </div>
                </el-card>
              </el-col>
              
              <el-col :xs="24" :sm="12" :md="6">
                <el-card class="stat-card repos">
                  <div class="stat-content">
                    <el-icon class="stat-icon"><Grid /></el-icon>
                    <div class="stat-info">
                      <div class="stat-value">{{ repositoryCount }}</div>
                      <div class="stat-label">仓库数量</div>
                    </div>
                  </div>
                </el-card>
              </el-col>
            </el-row>

            <!-- 筛选器 -->
            <el-card class="filter-card">
              <el-form :inline="true" class="filter-form">
                <el-form-item label="关键词">
                  <el-input 
                    v-model="analysisFilters.keyword" 
                    placeholder="搜索仓库名称" 
                    clearable
                    style="width: 300px"
                  />
                </el-form-item>
                
                <el-form-item>
                  <el-button type="primary" icon="Search" @click="handleSearch">搜索</el-button>
                  <el-button icon="Refresh" @click="resetAnalysisFilters">重置</el-button>
                </el-form-item>
              </el-form>
            </el-card>

            <!-- 图表区域 -->
            <el-row :gutter="20" class="charts-row">
              <el-col :xs="24" :sm="24" :md="12">
                <el-card class="chart-card">
                  <template #header>
                    <div class="card-header">
                      <span>分支类型分布</span>
                      <el-tag>{{ filteredBranches.length }} 个仓库</el-tag>
                    </div>
                  </template>
                  <div ref="branchTypeChart" class="chart-container" style="width: 100%; height: 350px;"></div>
                </el-card>
              </el-col>
              
              <el-col :xs="24" :sm="24" :md="12">
                <el-card class="chart-card">
                  <template #header>
                    <div class="card-header">
                      <span>活跃度分布</span>
                      <el-tag>{{ filteredBranches.length }} 个仓库</el-tag>
                    </div>
                  </template>
                  <div ref="activityChart" class="chart-container" style="width: 100%; height: 350px;"></div>
                </el-card>
              </el-col>
            </el-row>

            <!-- Top 仓库分布 -->
            <el-row :gutter="20">
              <el-col :span="24">
                <el-card class="chart-card">
                  <template #header>
                    <div class="card-header">
                      <span>仓库分支数量 TOP 10</span>
                    </div>
                  </template>
                  <div ref="repositoryChart" class="chart-container" style="width: 100%; height: 400px;"></div>
                </el-card>
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>

        <!-- 分支列表 Tab -->
        <el-tab-pane label="分支列表" name="list">
          <div class="list-content">
            <!-- 筛选栏 -->
            <div class="filter-bar">
              <el-select
                v-model="filterForm.repoId"
                placeholder="选择仓库"
                clearable
                filterable
                style="width: 300px"
                @change="handleRepoChange"
              >
                <el-option
                  v-for="repo in repositories"
                  :key="repo.id"
                  :label="repo.name"
                  :value="repo.id"
                />
              </el-select>
            </div>

            <!-- 数据表格 -->
            <el-table 
              v-loading="listLoading"
              :data="paginatedData" 
              stripe
              border
              style="width: 100%; margin-top: 20px"
              :default-sort="{ prop: 'last_commit_date', order: 'descending' }"
              @sort-change="handleSortChange"
            >
              <el-table-column prop="branch_name" label="分支名称" width="250" fixed sortable="custom" show-overflow-tooltip />
              
              <el-table-column prop="branchType" label="分支类型" width="120" sortable="custom">
                <template #default="{ row }">
                  <el-tag v-if="row.branchType" :type="getBranchTypeTagType(row.branchType)">
                    {{ getBranchTypeLabel(row.branchType) }}
                  </el-tag>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              
              <el-table-column prop="activityLevel" label="活跃度" width="100" sortable="custom">
                <template #default="{ row }">
                  <el-tag :type="getActivityTagType(row.activityLevel)">
                    {{ getActivityLabel(row.activityLevel) }}
                  </el-tag>
                </template>
              </el-table-column>
              
              <el-table-column prop="protected" label="保护状态" width="100" sortable="custom">
                <template #default="{ row }">
                  <el-tag v-if="row.protected" type="success">已保护</el-tag>
                  <el-tag v-else type="info">未保护</el-tag>
                </template>
              </el-table-column>
              
              <el-table-column prop="commit_author_name" label="提交者" width="120" sortable="custom" />
              
              <el-table-column prop="last_commit_date" label="最后提交" width="110" sortable="custom">
                <template #default="{ row }">
                  {{ formatDate(row.last_commit_date) }}
                </template>
              </el-table-column>
              
              <el-table-column prop="commit_message" label="提交信息" min-width="200" show-overflow-tooltip />
              
              <el-table-column label="操作" width="120" fixed="right">
                <template #default="{ row }">
                  <el-button 
                    type="primary" 
                    size="small" 
                    link
                    @click="viewBranchDetails(row)"
                  >
                    查看详情
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <!-- 分页 -->
            <div class="pagination">
              <el-pagination
                v-model:current-page="listPagination.page"
                v-model:page-size="listPagination.pageSize"
                :page-sizes="[20, 50, 100, 200]"
                :total="filteredBranchList.length"
                layout="total, sizes, prev, pager, next, jumper"
                @size-change="handleListSizeChange"
                @current-change="handleListPageChange"
              />
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog 
      v-model="detailDialogVisible" 
      title="分支详情" 
      width="70%"
      :close-on-click-modal="false"
    >
      <el-descriptions v-if="currentBranch" :column="2" border>
        <el-descriptions-item label="分支名称">{{ currentBranch.branch_name }}</el-descriptions-item>
        <el-descriptions-item label="仓库名称">{{ currentBranch.repositoryName || getRepositoryName(currentBranch.repository_id) }}</el-descriptions-item>
        
        <el-descriptions-item label="分支类型">
          <el-tag v-if="currentBranch.branchType" :type="getBranchTypeTagType(currentBranch.branchType)">
            {{ getBranchTypeLabel(currentBranch.branchType) }}
          </el-tag>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item label="活跃度">
          <el-tag :type="getActivityTagType(currentBranch.activityLevel)">
            {{ getActivityLabel(currentBranch.activityLevel) }}
          </el-tag>
        </el-descriptions-item>
        
        <el-descriptions-item label="保护状态">
          <el-tag v-if="currentBranch.protected" type="success">已保护</el-tag>
          <el-tag v-else type="info">未保护</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="可删除">
          <el-tag v-if="currentBranch.is_deletable" type="warning">是</el-tag>
          <el-tag v-else type="info">否</el-tag>
        </el-descriptions-item>
        
        <el-descriptions-item label="提交ID" :span="2">
          <code>{{ currentBranch.commit_id }}</code>
        </el-descriptions-item>
        <el-descriptions-item label="提交者">{{ currentBranch.commit_author_name }}</el-descriptions-item>
        <el-descriptions-item label="提交邮箱">{{ currentBranch.commit_author_email }}</el-descriptions-item>
        <el-descriptions-item label="最后提交时间">{{ formatDate(currentBranch.last_commit_date) }}</el-descriptions-item>
        <el-descriptions-item label="同步时间">{{ formatDate(currentBranch.sync_time) }}</el-descriptions-item>
        <el-descriptions-item label="提交信息" :span="2">
          <pre style="white-space: pre-wrap; word-wrap: break-word;">{{ currentBranch.commit_message }}</pre>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { FolderOpened, CircleCheck, Lock, Grid } from '@element-plus/icons-vue'
import { gitlabApi, branchApi } from '@/api'
import * as echarts from 'echarts'
import { exportToCSV } from '@/utils/common'

// 状态管理
const activeTab = ref('analysis')
const analysisLoading = ref(false)
const refreshingSummary = ref(false)  // 刷新汇总数据的 loading 状态
const listLoading = ref(false)
const deletionReportLoading = ref(false)  // 删除报告加载状态
const branches = ref([]) // 汇总数据（用于分析Tab）
const branchList = ref([]) // 具体分支列表（用于列表Tab）
const repositories = ref([])
const detailDialogVisible = ref(false)
const currentBranch = ref(null)

// 分析筛选器（简化版）
const analysisFilters = reactive({
  keyword: ''
})

// 列表筛选器
const filterForm = reactive({
  repoId: null
})

// 列表分页
const listPagination = reactive({
  page: 1,
  pageSize: 20
})

// 排序配置
const sortConfig = ref({
  prop: 'last_commit_date',
  order: 'descending'
})

// ECharts 实例引用
const branchTypeChart = ref(null)
const activityChart = ref(null)
const repositoryChart = ref(null)

// 增强分支数据（使用汇总数据）
const enhancedBranches = computed(() => {
  // branches 现在包含的是仓库汇总数据，不再是单个分支
  // 为了向后兼容，我们保持相同的数据结构
  return branches.value
})

// 筛选后的分支（分析Tab使用汇总数据）
const filteredBranches = computed(() => {
  let result = enhancedBranches.value

  // 关键词筛选（搜索仓库名称）
  if (analysisFilters.keyword) {
    const keyword = analysisFilters.keyword.toLowerCase()
    result = result.filter(summary => 
      summary.repository_name.toLowerCase().includes(keyword)
    )
  }

  return result
})

// 筛选后的分支列表（列表Tab使用具体分支数据）
const filteredBranchList = computed(() => {
  let result = branchList.value.map(branch => {
    return {
      ...branch,
      branchType: calculateBranchType(branch.branch_name),
      activityLevel: calculateActivityLevel(branch.last_commit_date),
      repositoryName: getRepositoryName(branch.repository_id)
    }
  })

  // 注意：不需要额外的仓库筛选，因为 loadBranchList() 已经只加载了选中仓库的分支
  // 如果需要支持"显示所有仓库"的功能，可以在这里添加筛选逻辑

  return result
})

// 排序后的分支（列表Tab使用）
const sortedBranchList = computed(() => {
  if (!sortConfig.value.prop || !sortConfig.value.order) {
    return filteredBranchList.value
  }

  const { prop, order } = sortConfig.value
  const multiplier = order === 'ascending' ? 1 : -1

  return [...filteredBranchList.value].sort((a, b) => {
    // 活跃度特殊排序
    if (prop === 'activityLevel') {
      const levelOrder = { active: 0, moderate: 1, low: 2, archived: 3 }
      const aLevel = levelOrder[a.activityLevel] ?? 4
      const bLevel = levelOrder[b.activityLevel] ?? 4
      return (aLevel - bLevel) * multiplier
    }

    let aVal = a[prop]
    let bVal = b[prop]

    // 处理null/undefined
    if (aVal == null && bVal == null) return 0
    if (aVal == null) return multiplier
    if (bVal == null) return -multiplier

    // 字符串比较
    if (typeof aVal === 'string' && typeof bVal === 'string') {
      return aVal.localeCompare(bVal) * multiplier
    }

    // 数值比较
    return (aVal > bVal ? 1 : -1) * multiplier
  })
})

// 分页后的数据（列表Tab使用）
const paginatedData = computed(() => {
  const start = (listPagination.page - 1) * listPagination.pageSize
  const end = start + listPagination.pageSize
  return sortedBranchList.value.slice(start, end)
})

// 统计数据（基于汇总数据计算）
const totalBranches = computed(() => {
  return filteredBranches.value.reduce((sum, summary) => sum + (summary.total_branches || 0), 0)
})

const activeBranchCount = computed(() => {
  return filteredBranches.value.reduce((sum, summary) => sum + (summary.active_30days || 0), 0)
})

const protectedBranchCount = computed(() => {
  return filteredBranches.value.reduce((sum, summary) => sum + (summary.protected_branches || 0), 0)
})

const repositoryCount = computed(() => {
  return filteredBranches.value.length
})

// 监听筛选条件变化，重新渲染图表
watch(() => analysisFilters.keyword, () => {
  if (activeTab.value === 'analysis') {
    nextTick(() => {
      renderCharts()
    })
  }
})

// 分支类型标签（简化版，仅用于图表）
function getBranchTypeLabel(type) {
  const labels = {
    feature: '功能',
    develop: '开发',
    release: '发布',
    hotfix: '热修复',
    bugfix: '修复',
    main: '主分支',
    stabilization: '稳定',
    archive: '归档',
    other: '其他'
  }
  return labels[type] || type
}

// 计算分支类型（从分支名提取）
function calculateBranchType(branchName) {
  if (!branchName) return 'other'
  
  const prefixes = ['dev/', 'feature/', 'bugfix/', 'hotfix/', 'release/', 'stabilization/', 'archive/', 'engineering/', 'customer/']
  
  for (const prefix of prefixes) {
    if (branchName.startsWith(prefix)) {
      return prefix.replace('/', '')
    }
  }
  
  // 特殊分支
  if (branchName === 'main' || branchName === 'master') return 'main'
  if (branchName === 'develop' || branchName === 'development') return 'develop'
  
  return 'other'
}

// 计算活跃度
function calculateActivityLevel(lastCommitDate) {
  if (!lastCommitDate) return 'archived'
  
  const now = new Date()
  const commitDate = new Date(lastCommitDate)
  const daysDiff = Math.floor((now - commitDate) / (1000 * 60 * 60 * 24))
  
  if (daysDiff <= 30) return 'active'
  if (daysDiff <= 90) return 'moderate'
  if (daysDiff <= 180) return 'low'
  return 'archived'
}

// 获取仓库名称
function getRepositoryName(repositoryId) {
  const repo = repositories.value.find(r => r.id === repositoryId)
  return repo ? repo.name : `仓库 ${repositoryId}`
}

// 分支类型标签颜色
function getBranchTypeTagType(type) {
  const types = {
    main: 'danger',
    develop: 'warning',
    dev: 'primary',
    feature: 'success',
    bugfix: 'warning',
    hotfix: 'danger',
    release: 'success',
    stabilization: 'info',
    archive: 'info',
    engineering: 'primary',
    customer: 'warning',
    other: 'info'  // 修改：将空字符串改为 'info'
  }
  return types[type] || 'info'  // 修改：将空字符串改为 'info'
}

// 活跃度标签
function getActivityLabel(level) {
  const labels = {
    active: '活跃',
    moderate: '中等',
    low: '低活跃',
    archived: '归档'
  }
  return labels[level] || level
}

// 活跃度标签颜色
function getActivityTagType(level) {
  const types = {
    active: 'success',
    moderate: 'primary',
    low: 'warning',
    archived: 'info'
  }
  return types[level] || ''
}

// 日期格式化
function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 刷新汇总数据（调用生成所有汇总的API）
async function handleRefreshSummaryData() {
  try {
    await ElMessageBox.confirm(
      '将重新生成所有仓库的分支汇总数据（异步任务），可能需要几分钟时间，是否继续？',
      '确认刷新',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    refreshingSummary.value = true
    
    // 调用生成汇总API（异步任务）
    const result = await gitlabApi.generateBranchSummaries({
      async: true,
      force_refresh: false
    })
    
    if (result.success) {
      ElMessage.success({
        message: result.message || '汇总任务已创建，正在后台生成中...',
        duration: 3000
      })
      
      // 等待几秒后刷新页面数据
      setTimeout(async () => {
        await loadAnalysisData()
        ElMessage.info('数据已更新，如未看到最新数据请稍后再试')
      }, 5000)
    } else {
      ElMessage.error(result.message || '创建汇总任务失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('刷新汇总数据失败:', error)
      ElMessage.error('刷新汇总数据失败')
    }
  } finally {
    refreshingSummary.value = false
  }
}

// 原分析分支规则函数（已废弃，保留以防需要）
async function handleAnalyzeBranches() {
  try {
    await ElMessageBox.confirm(
      '将分析数据库中所有仓库的分支规则（不会连接 GitLab），是否继续？',
      '确认分析',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    refreshingSummary.value = true
    const result = await gitlabApi.analyzeBranches()
    
    if (result.success) {
      ElMessage.success(result.message || '分支规则分析完成')
      // 分析完成后刷新数据
      await loadAnalysisData()
    } else {
      ElMessage.error(result.message || '分支规则分析失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('分析分支规则失败:', error)
      ElMessage.error('分析分支规则失败')
    }
  } finally {
    refreshingSummary.value = false
  }
}

// 加载分析数据（使用新的分支汇总 API）
async function loadAnalysisData() {
  analysisLoading.value = true
  try {
    // 加载所有仓库
    const repoRes = await gitlabApi.getRepositories({ page: 1, page_size: 2000 })
    repositories.value = repoRes.repositories || []
    
    // 使用新的分支汇总 API（性能优化：直接获取汇总数据，而不是查询所有分支）
    const summaryRes = await gitlabApi.getBranchSummaries({})
    console.log('Branch summaries response:', summaryRes)
    
    // 后端返回格式：{ success: true, data: [...] }
    const summaries = summaryRes.data || summaryRes.summaries || []
    
    // 将汇总数据展开为分支列表格式（用于兼容现有图表逻辑）
    branches.value = summaries.map(summary => ({
      repository_id: summary.repository_id,
      repository_name: summary.repository_name,
      total_branches: summary.total_branches,
      protected_branches: summary.protected_branches,
      deletable_branches: summary.deletable_branches,
      // 常用分支类型统计（独立字段）
      feature_branches: summary.feature_branches,
      develop_branches: summary.develop_branches,
      release_branches: summary.release_branches,
      hotfix_branches: summary.hotfix_branches,
      main_branches: summary.main_branches,
      stabilization_branches: summary.stabilization_branches,
      other_branches: summary.other_branches,
      // 活跃度统计
      active_30days: summary.active_30days,
      active_90days: summary.active_90days,
      inactive_180days: summary.inactive_180days,
      inactive_365days: summary.inactive_365days,
      // 最新最旧分支
      latest_branch_name: summary.latest_branch_name,
      latest_branch_date: summary.latest_branch_date,
      oldest_branch_name: summary.oldest_branch_name,
      oldest_branch_date: summary.oldest_branch_date,
      // 默认分支信息
      default_branch: summary.default_branch,
      default_branch_commit: summary.default_branch_commit,
      default_branch_last_commit_date: summary.default_branch_last_commit_date,
      // 元数据
      last_sync_time: summary.last_sync_time
    }))
    
    ElMessage.success(`已加载 ${summaries.length} 个仓库的分支汇总数据`)
    
    // 渲染图表
    if (activeTab.value === 'analysis') {
      await nextTick()
      setTimeout(renderCharts, 300)
    }
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    analysisLoading.value = false
  }
}

// 渲染图表
function renderCharts() {
  renderBranchTypeChart()
  renderActivityChart()
  renderRepositoryChart()
}

// 渲染分支类型图表（使用汇总数据的固定分支类型字段）
function renderBranchTypeChart() {
  if (!branchTypeChart.value) {
    console.log('branchTypeChart ref not ready')
    return
  }

  // 获取或创建图表实例（避免重复初始化）
  const chartInstance = echarts.getInstanceByDom(branchTypeChart.value) || echarts.init(branchTypeChart.value)
  
  // 聚合所有仓库的分支类型统计（使用固定字段）
  const typeStats = {
    feature: 0,
    develop: 0,
    release: 0,
    hotfix: 0,
    main: 0,
    stabilization: 0,
    other: 0
  }
  
  filteredBranches.value.forEach(branch => {
    typeStats.feature += branch.feature_branches || 0
    typeStats.develop += branch.develop_branches || 0
    typeStats.release += branch.release_branches || 0
    typeStats.hotfix += branch.hotfix_branches || 0
    typeStats.main += branch.main_branches || 0
    typeStats.stabilization += branch.stabilization_branches || 0
    typeStats.other += branch.other_branches || 0
  })
  
  // 过滤掉数量为0的类型，并排序
  const sortedTypes = Object.entries(typeStats)
    .filter(([, count]) => count > 0)
    .sort((a, b) => b[1] - a[1])
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: sortedTypes.map(([type]) => getBranchTypeLabel(type)),
      axisLabel: {
        rotate: 30
      }
    },
    yAxis: {
      type: 'value'
    },
    series: [{
      name: '分支数量',
      type: 'bar',
      data: sortedTypes.map(([, count]) => count),
      itemStyle: {
        color: '#409eff'
      }
    }]
  }
  
  chartInstance.setOption(option)
}

// 渲染活跃度图表（使用汇总数据）
function renderActivityChart() {
  if (!activityChart.value) {
    console.log('activityChart ref not ready')
    return
  }

  // 获取或创建图表实例（避免重复初始化）
  const chartInstance = echarts.getInstanceByDom(activityChart.value) || echarts.init(activityChart.value)
  
  // 聚合所有仓库的活跃度统计
  const activityStats = {
    active_30days: 0,
    active_90days: 0,
    inactive_180days: 0,
    inactive_365days: 0
  }
  
  filteredBranches.value.forEach(summary => {
    activityStats.active_30days += summary.active_30days || 0
    activityStats.active_90days += summary.active_90days || 0
    activityStats.inactive_180days += summary.inactive_180days || 0
    activityStats.inactive_365days += summary.inactive_365days || 0
  })
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [{
      name: '活跃度',
      type: 'pie',
      radius: '60%',
      data: [
        { value: activityStats.active_30days, name: '30天内活跃' },
        { value: activityStats.active_90days - activityStats.active_30days, name: '90天内活跃' },
        { value: activityStats.inactive_180days, name: '180天未活跃' },
        { value: activityStats.inactive_365days, name: '365天未活跃' }
      ].filter(item => item.value > 0),
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }
  
  chartInstance.setOption(option)
}

// 渲染仓库分支图表（使用汇总数据）
function renderRepositoryChart() {
  if (!repositoryChart.value) {
    console.log('repositoryChart ref not ready')
    return
  }

  // 获取或创建图表实例（避免重复初始化）
  const chartInstance = echarts.getInstanceByDom(repositoryChart.value) || echarts.init(repositoryChart.value)
  
  // 按分支总数排序，取前10
  const top10Repos = filteredBranches.value
    .map(summary => ({
      name: summary.repository_name,
      count: summary.total_branches || 0
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value'
    },
    yAxis: {
      type: 'category',
      data: top10Repos.map(repo => repo.name),
      axisLabel: {
        width: 200,
        overflow: 'truncate'
      }
    },
    series: [{
      name: '分支数量',
      type: 'bar',
      data: top10Repos.map(repo => repo.count),
      itemStyle: {
        color: '#67c23a'
      }
    }]
  }
  
  chartInstance.setOption(option)
}

// 重置筛选器
function resetAnalysisFilters() {
  analysisFilters.keyword = ''
}

// 搜索
function handleSearch() {
  // 筛选逻辑在 computed 中自动处理
  listPagination.page = 1
}

// Tab切换
async function handleTabChange(tabName) {
  if (tabName === 'analysis' && branches.value.length > 0) {
    await nextTick()
    setTimeout(renderCharts, 300)
  } else if (tabName === 'list' && branchList.value.length === 0) {
    // 第一次切换到列表Tab时加载分支数据
    await loadBranchList()
  }
}

// 仓库切换
async function handleRepoChange() {
  listPagination.page = 1
  // 切换仓库时重新加载该仓库的分支数据
  if (filterForm.repoId) {
    await loadBranchList()
  } else {
    // 清空选择时，清空分支列表
    branchList.value = []
  }
}

// 排序变化
function handleSortChange({ prop, order }) {
  sortConfig.value = { prop, order }
  listPagination.page = 1
}

// 分页变化
function handleListSizeChange(pageSize) {
  listPagination.pageSize = pageSize
  listPagination.page = 1
}

function handleListPageChange(page) {
  listPagination.page = page
}

// 加载分支列表数据（用于列表Tab）
async function loadBranchList() {
  if (!filterForm.repoId) {
    ElMessage.warning('请先选择仓库')
    return
  }
  
  listLoading.value = true
  try {
    const branchRes = await gitlabApi.getBranches(filterForm.repoId, {})
    branchList.value = branchRes.branches || []
    ElMessage.success(`已加载 ${branchList.value.length} 个分支`)
  } catch (error) {
    console.error('加载分支列表失败:', error)
    ElMessage.error('加载分支列表失败')
  } finally {
    listLoading.value = false
  }
}

// 查看分支详情
function viewBranchDetails(branch) {
  currentBranch.value = branch
  detailDialogVisible.value = true
}

// 查看详情（已更新为查看分支详情）
function viewDetails(branch) {
  currentBranch.value = branch
  detailDialogVisible.value = true
}

// 查看仓库详情（废弃，保留以防万一）
function viewRepositoryDetails(summary) {
  currentBranch.value = summary
  detailDialogVisible.value = true
}

// 刷新单个仓库的分支汇总（废弃，保留以防万一）
async function refreshRepositorySummary(repositoryId) {
  try {
    ElMessage.info('正在刷新仓库分支汇总...')
    await gitlabApi.generateRepositoryBranchSummary(repositoryId)
    ElMessage.success('刷新成功')
    // 重新加载数据
    await loadAnalysisData()
  } catch (error) {
    console.error('刷新失败:', error)
    ElMessage.error('刷新失败')
  }
}

// 同步分支（更新为同步原始分支数据）
async function handleSync() {
  try {
    ElMessage.info('正在同步分支数据，此操作可能需要几分钟...')
    await gitlabApi.syncBranches({})
    ElMessage.success('分支同步完成')
    // 如果当前有选中的仓库，重新加载该仓库的分支
    if (filterForm.repoId) {
      await loadBranchList()
    }
  } catch (error) {
    console.error('同步分支失败:', error)
    ElMessage.error('同步分支失败')
  }
}

// 导出数据
function exportData() {
  if (filteredBranches.value.length === 0) {
    ElMessage.warning('没有可导出的数据')
    return
  }

  // 定义导出列
  const columns = [
    { key: 'repository_name', label: '仓库名称' },
    { key: 'total_branches', label: '总分支数' },
    { key: 'protected_branches', label: '受保护分支' },
    { key: 'deletable_branches', label: '可删除分支' },
    { key: 'feature_branches', label: 'Feature分支' },
    { key: 'develop_branches', label: 'Develop分支' },
    { key: 'release_branches', label: 'Release分支' },
    { key: 'hotfix_branches', label: 'Hotfix分支' },
    { key: 'main_branches', label: 'Main分支' },
    { key: 'stabilization_branches', label: 'Stabilization分支' },
    { key: 'other_branches', label: '其他分支' },
    { key: 'active_30days', label: '30天内活跃' },
    { key: 'active_90days', label: '90天内活跃' },
    { key: 'inactive_180days', label: '180天未活跃' },
    { key: 'inactive_365days', label: '365天未活跃' },
    { key: 'latest_branch_name', label: '最新分支名称' },
    { 
      key: 'latest_branch_date', 
      label: '最新分支日期',
      formatter: (value) => value ? new Date(value).toLocaleDateString() : ''
    },
    { key: 'oldest_branch_name', label: '最旧分支名称' },
    { 
      key: 'oldest_branch_date', 
      label: '最旧分支日期',
      formatter: (value) => value ? new Date(value).toLocaleDateString() : ''
    },
    { key: 'default_branch', label: '默认分支' },
    { 
      key: 'last_sync_time', 
      label: '最后同步时间',
      formatter: (value) => value ? new Date(value).toLocaleString() : ''
    }
  ]

  // 生成文件名（如果有筛选关键词，添加到文件名中）
  const keyword = analysisFilters.keyword ? `_${analysisFilters.keyword}` : ''
  const filename = `分支汇总数据${keyword}`

  // 使用通用导出函数
  const success = exportToCSV(filteredBranches.value, filename, { columns })
  
  if (success) {
    ElMessage.success(`已导出 ${filteredBranches.value.length} 条数据`)
  } else {
    ElMessage.error('导出数据失败')
  }
}

// ==================== 分支删除分析相关 ====================

// 导出删除报告
async function exportDeletionReport() {
  deletionReportLoading.value = true
  try {
    const response = await branchApi.exportDeletionReport()
    
    // 从响应中获取blob数据
    // 注意：request拦截器对blob类型返回的是整个response对象
    const blobData = response.data
    
    // 检查是否真的是blob数据
    if (!blobData || blobData.size === 0) {
      throw new Error('接收到的文件数据为空')
    }
    
    console.log('接收到文件大小:', blobData.size, 'bytes')
    
    // 创建Blob对象，指定正确的MIME类型
    const blob = new Blob([blobData], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    // 生成文件名
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
    link.setAttribute('download', `分支删除报告_${timestamp}.xlsx`)
    
    // 触发下载
    document.body.appendChild(link)
    link.click()
    
    // 清理
    setTimeout(() => {
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    }, 100)
    
    ElMessage.success('报告导出成功')
  } catch (error) {
    console.error('导出报告失败:', error)
    ElMessage.error('导出报告失败: ' + (error.message || '未知错误'))
  } finally {
    deletionReportLoading.value = false
  }
}

// 组件挂载
onMounted(() => {
  loadAnalysisData()
})
</script>


<style lang="scss" scoped>
.branches {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .filter-bar {
    margin-bottom: 20px;
  }

  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }

  .analysis-content {
    .stats-row {
      margin-bottom: 20px;
    }

    .stat-card {
      cursor: default;
      transition: all 0.3s ease;

      &:hover {
        transform: translateY(-3px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      }

      .stat-content {
        display: flex;
        align-items: center;
        padding: 10px 0;

        .stat-icon {
          font-size: 48px;
          margin-right: 20px;
        }

        .stat-info {
          flex: 1;

          .stat-value {
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 5px;
          }

          .stat-label {
            font-size: 14px;
            color: #909399;
          }
        }
      }

      &.total {
        .stat-icon {
          color: #409eff;
        }
        .stat-value {
          color: #409eff;
        }
      }

      &.active {
        .stat-icon {
          color: #67c23a;
        }
        .stat-value {
          color: #67c23a;
        }
      }

      &.protected {
        .stat-icon {
          color: #e6a23c;
        }
        .stat-value {
          color: #e6a23c;
        }
      }

      &.repos {
        .stat-icon {
          color: #909399;
        }
        .stat-value {
          color: #909399;
        }
      }
    }

    .filter-card {
      margin-bottom: 20px;

      .filter-form {
        margin-bottom: 0;
      }
    }

    .charts-row {
      margin-bottom: 20px;
    }

    .chart-card {
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .chart-container {
        min-height: 350px;
      }
    }
  }

  .list-content {
    .filter-bar {
      margin-bottom: 20px;
    }
  }
}

:deep(.el-table) {
  font-size: 14px;

  .el-table__header th {
    background-color: #f5f7fa;
  }
}

:deep(.el-descriptions__label) {
  font-weight: bold;
}

pre {
  margin: 0;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

code {
  padding: 2px 6px;
  background-color: #f5f7fa;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
}
</style>

<!-- 分支总数应该是27071，但是只读到7396个分支，所以对于分支来说，要在后台计算写到表里直接读，在前端处理不是个好办法，那么先 -->