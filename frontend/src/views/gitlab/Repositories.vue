<template>
  <div class="repositories">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>仓库管理</span>
          <div>
            <el-button 
              v-if="activeTab === 'list'"
              type="primary" 
              icon="Refresh" 
              @click="handleSync"
            >
              同步仓库
            </el-button>
            <el-button 
              v-if="activeTab === 'analysis'"
              type="success" 
              icon="Refresh" 
              @click="loadAnalysisData"
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
          </div>
        </div>
      </template>

      <!-- Tab 切换 -->
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- 仓库分类分析 Tab -->
        <el-tab-pane label="仓库分类分析" name="analysis">
          <div class="analysis-content">
            <!-- 统计卡片 -->
            <el-row :gutter="20" class="stats-row">
              <el-col :xs="24" :sm="12" :md="8">
                <el-card class="stat-card total">
                  <div class="stat-content">
                    <el-icon class="stat-icon"><FolderOpened /></el-icon>
                    <div class="stat-info">
                      <div class="stat-value">{{ totalRepositories }}</div>
                      <div class="stat-label">仓库总数</div>
                    </div>
                  </div>
                </el-card>
              </el-col>
              
              <el-col :xs="24" :sm="12" :md="8">
                <el-card class="stat-card active">
                  <div class="stat-content">
                    <el-icon class="stat-icon"><CircleCheck /></el-icon>
                    <div class="stat-info">
                      <div class="stat-value">{{ activeCount }}</div>
                      <div class="stat-label">活跃仓库</div>
                    </div>
                  </div>
                </el-card>
              </el-col>
              
              <el-col :xs="24" :sm="12" :md="8">
                <el-card class="stat-card domains">
                  <div class="stat-content">
                    <el-icon class="stat-icon"><Grid /></el-icon>
                    <div class="stat-info">
                      <div class="stat-value">{{ businessDomainCount }}</div>
                      <div class="stat-label">业务域数量</div>
                    </div>
                  </div>
                </el-card>
              </el-col>
            </el-row>

            <!-- 筛选器 -->
            <el-card class="filter-card">
              <el-form :inline="true" class="filter-form">
                <el-form-item label="业务域">
                  <el-select 
                    v-model="analysisFilters.businessDomain" 
                    placeholder="全部" 
                    clearable
                    style="width: 150px"
                  >
                    <el-option 
                      v-for="domain in businessDomains" 
                      :key="domain" 
                      :label="domain" 
                      :value="domain" 
                    />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="活跃度">
                  <el-select 
                    v-model="analysisFilters.activityLevel" 
                    placeholder="全部" 
                    clearable
                    style="width: 150px"
                  >
                    <el-option label="活跃" value="active" />
                    <el-option label="中等" value="moderate" />
                    <el-option label="低活跃" value="low" />
                    <el-option label="归档" value="archived" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="可见性">
                  <el-select 
                    v-model="analysisFilters.visibility" 
                    placeholder="全部" 
                    clearable
                    style="width: 120px"
                  >
                    <el-option label="公开" value="public" />
                    <el-option label="私有" value="private" />
                    <el-option label="内部" value="internal" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="关键词">
                  <el-input 
                    v-model="analysisFilters.keyword" 
                    placeholder="搜索仓库名称或路径" 
                    clearable
                    style="width: 200px"
                  />
                </el-form-item>
                
                <el-form-item>
                  <el-button type="primary" icon="Search" @click="applyFilters">搜索</el-button>
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
                      <span>业务域分布（Top 10）</span>
                      <el-tag>{{ filteredRepositories.length }} 个仓库</el-tag>
                    </div>
                  </template>
                  <div ref="businessDomainChart" class="chart-container" style="width: 100%; height: 350px;"></div>
                </el-card>
              </el-col>
              
              <el-col :xs="24" :sm="24" :md="12">
                <el-card class="chart-card">
                  <template #header>
                    <div class="card-header">
                      <span>活跃度分布</span>
                      <el-tag>{{ filteredRepositories.length }} 个仓库</el-tag>
                    </div>
                  </template>
                  <div ref="activityChart" class="chart-container" style="width: 100%; height: 350px;"></div>
                </el-card>
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>

        <!-- 仓库列表 Tab -->
        <el-tab-pane label="仓库列表" name="list">
          <div class="list-content">
            <!-- 数据表格 -->
            <el-table 
              v-loading="analysisLoading"
              :data="paginatedData" 
              stripe
              border
              style="width: 100%"
              :default-sort="{ prop: 'last_activity_at', order: 'descending' }"
              @sort-change="handleSortChange"
            >
              <el-table-column prop="name" label="仓库名称" width="200" fixed sortable="custom">
                <template #default="{ row }">
                  <el-link :href="row.web_url" target="_blank" type="primary">
                    {{ row.name }}
                  </el-link>
                </template>
              </el-table-column>
              
              <el-table-column prop="path_with_namespace" label="完整路径" width="300" show-overflow-tooltip sortable="custom" />
              
              <el-table-column prop="businessDomain" label="业务域" width="120" sortable="custom">
                <template #default="{ row }">
                  <el-tag>{{ row.businessDomain }}</el-tag>
                </template>
              </el-table-column>
              
              <el-table-column prop="activityLevel" label="活跃度" width="100" sortable="custom">
                <template #default="{ row }">
                  <el-tag :type="getActivityTagType(row.activityLevel)">
                    {{ getActivityLabel(row.activityLevel) }}
                  </el-tag>
                </template>
              </el-table-column>
              
              <el-table-column prop="visibility" label="可见性" width="90" sortable="custom">
                <template #default="{ row }">
                  <el-tag :type="getVisibilityTagType(row.visibility)" size="small">
                    {{ getVisibilityLabel(row.visibility) }}
                  </el-tag>
                </template>
              </el-table-column>
              
              <el-table-column prop="last_activity_at" label="最后活动" width="110" sortable="custom">
                <template #default="{ row }">
                  {{ formatDate(row.last_activity_at) }}
                </template>
              </el-table-column>
              
              <el-table-column prop="created_at" label="创建时间" width="110" sortable="custom">
                <template #default="{ row }">
                  {{ formatDate(row.created_at) }}
                </template>
              </el-table-column>
              
              <el-table-column label="操作" width="150" fixed="right">
                <template #default="{ row }">
                  <el-button 
                    type="primary" 
                    size="small" 
                    link
                    @click="viewDetails(row)"
                  >
                    查看详情
                  </el-button>
                  <el-button 
                    type="success" 
                    size="small" 
                    link
                    @click="viewBranches(row)"
                  >
                    分支
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
                :total="filteredRepositories.length"
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
      title="仓库详情" 
      width="70%"
      :close-on-click-modal="false"
    >
      <el-descriptions v-if="currentRepo" :column="2" border>
        <el-descriptions-item label="仓库名称">{{ currentRepo.name }}</el-descriptions-item>
        <el-descriptions-item label="完整路径">{{ currentRepo.path_with_namespace }}</el-descriptions-item>
        <el-descriptions-item label="业务域">
          <el-tag>{{ currentRepo.businessDomain }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="活跃度">
          <el-tag :type="getActivityTagType(currentRepo.activityLevel)">
            {{ getActivityLabel(currentRepo.activityLevel) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="可见性">
          <el-tag :type="getVisibilityTagType(currentRepo.visibility)">
            {{ getVisibilityLabel(currentRepo.visibility) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="默认分支">{{ currentRepo.default_branch || 'N/A' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDate(currentRepo.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="最后活动">{{ formatDate(currentRepo.last_activity_at) }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">
          {{ currentRepo.description || '无描述' }}
        </el-descriptions-item>
        <el-descriptions-item label="Web URL" :span="2">
          <el-link :href="currentRepo.web_url" target="_blank" type="primary">
            {{ currentRepo.web_url }}
          </el-link>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  FolderOpened, CircleCheck, Grid, Refresh, 
  Search, Download, Link 
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { gitlabApi } from '@/api'
import { formatDate, exportToCSV } from '@/utils/common'

const router = useRouter()

// Tab 控制
const activeTab = ref('analysis')

// 仓库列表相关数据（已弃用，使用分析数据）
const listLoading = ref(false)
const tableData = ref([])

const searchForm = reactive({
  keyword: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

// 仓库分析相关数据
const analysisLoading = ref(false)
const repositories = ref([])
const analysisFilters = ref({
  businessDomain: '',
  activityLevel: '',
  visibility: '',
  keyword: ''
})

// 列表页面的分页（使用过滤后的数据）
const listPagination = ref({
  page: 1,
  pageSize: 20
})

// 排序状态
const sortConfig = ref({
  prop: 'last_activity_at',
  order: 'descending'
})

// 详情对话框
const detailDialogVisible = ref(false)
const currentRepo = ref(null)

// 图表实例
const businessDomainChart = ref(null)
const activityChart = ref(null)
let charts = {
  businessDomain: null,
  activity: null
}

// 活跃度计算
const calculateActivityLevel = (lastActivityAt) => {
  if (!lastActivityAt) return 'archived'
  
  const lastActivity = new Date(lastActivityAt)
  const now = new Date()
  const diffDays = Math.floor((now - lastActivity) / (1000 * 60 * 60 * 24))
  
  if (diffDays <= 30) return 'active'
  if (diffDays <= 90) return 'moderate'
  if (diffDays <= 180) return 'low'
  return 'archived'
}

// 业务域提取
const calculateBusinessDomain = (nameWithNamespace) => {
  if (!nameWithNamespace) return '未分类'
  const parts = nameWithNamespace.split('/')
  return parts[0] || '未分类'
}

// 增强仓库数据
const enhancedRepositories = computed(() => {
  return repositories.value.map(repo => ({
    ...repo,
    activityLevel: calculateActivityLevel(repo.last_activity_at),
    businessDomain: calculateBusinessDomain(repo.name_with_namespace),
    path_with_namespace: repo.name_with_namespace || ''
  }))
})

// 筛选后的仓库
const filteredRepositories = computed(() => {
  let result = enhancedRepositories.value
  
  if (analysisFilters.value.businessDomain) {
    result = result.filter(repo => repo.businessDomain === analysisFilters.value.businessDomain)
  }
  
  if (analysisFilters.value.activityLevel) {
    result = result.filter(repo => repo.activityLevel === analysisFilters.value.activityLevel)
  }
  
  if (analysisFilters.value.visibility) {
    result = result.filter(repo => repo.visibility === analysisFilters.value.visibility)
  }
  
  if (analysisFilters.value.keyword) {
    const keyword = analysisFilters.value.keyword.toLowerCase()
    result = result.filter(repo => 
      repo.name?.toLowerCase().includes(keyword) ||
      repo.path_with_namespace?.toLowerCase().includes(keyword) ||
      repo.description?.toLowerCase().includes(keyword)
    )
  }
  
  return result
})

// 排序后的数据
const sortedRepositories = computed(() => {
  if (!sortConfig.value.prop) {
    return filteredRepositories.value
  }
  
  const sorted = [...filteredRepositories.value]
  const { prop, order } = sortConfig.value
  
  sorted.sort((a, b) => {
    let aVal = a[prop]
    let bVal = b[prop]
    
    // 处理日期字段
    if (prop === 'created_at' || prop === 'last_activity_at') {
      aVal = new Date(aVal || 0).getTime()
      bVal = new Date(bVal || 0).getTime()
    }
    
    // 处理活跃度排序 - 按优先级排序
    if (prop === 'activityLevel') {
      const levelOrder = { active: 0, moderate: 1, low: 2, archived: 3 }
      aVal = levelOrder[aVal] ?? 999
      bVal = levelOrder[bVal] ?? 999
    }
    
    // 字符串比较
    if (typeof aVal === 'string' && typeof bVal === 'string') {
      aVal = aVal.toLowerCase()
      bVal = bVal.toLowerCase()
    }
    
    // 比较
    if (aVal < bVal) return order === 'ascending' ? -1 : 1
    if (aVal > bVal) return order === 'ascending' ? 1 : -1
    return 0
  })
  
  return sorted
})

// 分页数据（用于列表 Tab）
const paginatedData = computed(() => {
  const start = (listPagination.value.page - 1) * listPagination.value.pageSize
  const end = start + listPagination.value.pageSize
  return sortedRepositories.value.slice(start, end)
})

// 统计数据
const totalRepositories = computed(() => enhancedRepositories.value.length)

const activeCount = computed(() => 
  enhancedRepositories.value.filter(repo => repo.activityLevel === 'active').length
)

const businessDomains = computed(() => {
  const domains = new Set(enhancedRepositories.value.map(repo => repo.businessDomain))
  return Array.from(domains).sort()
})

const businessDomainCount = computed(() => businessDomains.value.length)

// 业务域统计
const businessDomainStats = computed(() => {
  const stats = {}
  filteredRepositories.value.forEach(repo => {
    stats[repo.businessDomain] = (stats[repo.businessDomain] || 0) + 1
  })
  return Object.entries(stats)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)
})

// 活跃度统计
const activityStats = computed(() => {
  const activityLabels = {
    active: '活跃',
    moderate: '中等',
    low: '低活跃',
    archived: '归档'
  }
  
  const stats = {}
  filteredRepositories.value.forEach(repo => {
    stats[repo.activityLevel] = (stats[repo.activityLevel] || 0) + 1
  })
  
  return [
    { name: activityLabels.active, value: stats.active || 0 },
    { name: activityLabels.moderate, value: stats.moderate || 0 },
    { name: activityLabels.low, value: stats.low || 0 },
    { name: activityLabels.archived, value: stats.archived || 0 }
  ]
})

// 加载分析数据（列表Tab也使用这个数据）
const loadAnalysisData = async () => {
  analysisLoading.value = true
  try {
    const response = await gitlabApi.getRepositories({ 
      page: 1, 
      page_size: 2000 
    })
    
    if (response.success && response.repositories) {
      repositories.value = response.repositories
      ElMessage.success(`成功加载 ${response.repositories.length} 个仓库`)
      
      // 等待 DOM 更新后渲染图表
      await nextTick()
      setTimeout(() => {
        renderCharts()
      }, 300)
    } else {
      ElMessage.error('加载数据失败')
    }
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败: ' + error.message)
  } finally {
    analysisLoading.value = false
  }
}

// 渲染图表
const renderCharts = () => {
  console.log('renderCharts 被调用')
  console.log('businessDomainChart.value:', businessDomainChart.value)
  console.log('activityChart.value:', activityChart.value)
  
  if (!businessDomainChart.value || !activityChart.value) {
    console.warn('图表容器还未准备好，延迟渲染...')
    setTimeout(renderCharts, 200)
    return
  }
  
  renderBusinessDomainChart()
  renderActivityChart()
}

// 业务域柱状图
const renderBusinessDomainChart = () => {
  if (!businessDomainChart.value) {
    console.error('businessDomainChart ref 不存在，无法渲染')
    return
  }
  
  try {
    console.log('开始渲染业务域图表', businessDomainStats.value)
    
    if (charts.businessDomain) {
      charts.businessDomain.dispose()
    }
    
    charts.businessDomain = echarts.init(businessDomainChart.value)
    
    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' }
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
        data: businessDomainStats.value.map(item => item.name).reverse()
      },
      series: [{
        type: 'bar',
        data: businessDomainStats.value.map(item => item.count).reverse(),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#83bff6' },
            { offset: 1, color: '#188df0' }
          ])
        },
        label: {
          show: true,
          position: 'right'
        }
      }]
    }
    
    charts.businessDomain.setOption(option)
    console.log('业务域图表渲染完成')
  } catch (error) {
    console.error('渲染业务域图表失败:', error)
  }
}

// 活跃度饼图
const renderActivityChart = () => {
  if (!activityChart.value) {
    console.error('activityChart ref 不存在，无法渲染')
    return
  }
  
  try {
    console.log('开始渲染活跃度图表', activityStats.value)
    
    if (charts.activity) {
      charts.activity.dispose()
    }
    
    charts.activity = echarts.init(activityChart.value)
    
    const option = {
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} ({d}%)'
      },
      legend: {
        bottom: '5%',
        left: 'center'
      },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}: {d}%'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        data: activityStats.value,
        color: ['#67C23A', '#409EFF', '#E6A23C', '#909399']
      }]
    }
    
    charts.activity.setOption(option)
    console.log('活跃度图表渲染完成')
  } catch (error) {
    console.error('渲染活跃度图表失败:', error)
  }
}

// 工具函数
const applyFilters = () => {
  // 筛选会自动通过 computed 属性应用
}

const resetAnalysisFilters = () => {
  analysisFilters.value = {
    businessDomain: '',
    activityLevel: '',
    visibility: '',
    keyword: ''
  }
}

const exportData = () => {
  if (filteredRepositories.value.length === 0) {
    ElMessage.warning('没有可导出的数据')
    return
  }

  // 定义导出列
  const columns = [
    { key: 'name', label: '仓库名称' },
    { key: 'path_with_namespace', label: '完整路径' },
    { key: 'businessDomain', label: '业务域' },
    { 
      key: 'activityLevel', 
      label: '活跃度',
      formatter: (value) => getActivityLabel(value)
    },
    { 
      key: 'visibility', 
      label: '可见性',
      formatter: (value) => getVisibilityLabel(value)
    },
    { 
      key: 'created_at', 
      label: '创建时间',
      formatter: (value) => formatDate(value)
    },
    { 
      key: 'last_activity_at', 
      label: '最后活动',
      formatter: (value) => formatDate(value)
    }
  ]

  // 使用通用导出函数
  const success = exportToCSV(filteredRepositories.value, '仓库分析', { 
    columns,
    addTimestamp: false  // 使用日期格式而不是时间戳
  })
  
  if (success) {
    ElMessage.success(`已导出 ${filteredRepositories.value.length} 条数据`)
  } else {
    ElMessage.error('导出数据失败')
  }
}

const getActivityLabel = (level) => {
  const labels = { active: '活跃', moderate: '中等', low: '低活跃', archived: '归档' }
  return labels[level] || level
}

const getVisibilityLabel = (visibility) => {
  const labels = { public: '公开', private: '私有', internal: '内部' }
  return labels[visibility] || visibility
}

const getActivityTagType = (level) => {
  const types = { active: 'success', moderate: '', low: 'warning', archived: 'info' }
  return types[level] || ''
}

const getVisibilityTagType = (visibility) => {
  const types = { public: 'success', internal: 'warning', private: 'danger' }
  return types[visibility] || ''
}

// 列表页面函数
const handleListSizeChange = (size) => {
  listPagination.value.pageSize = size
  listPagination.value.page = 1
}

const handleListPageChange = (page) => {
  listPagination.value.page = page
}

const handleSortChange = ({ prop, order }) => {
  console.log('排序变化:', prop, order)
  sortConfig.value = {
    prop: prop || 'last_activity_at',
    order: order || 'descending'
  }
  // 排序后重置到第一页
  listPagination.value.page = 1
}

const viewDetails = (repo) => {
  currentRepo.value = repo
  detailDialogVisible.value = true
}

// 原有列表页面函数（已弃用）
// 原有列表函数（已弃用，保留以避免错误）
const handleSearch = () => {
  // 不再使用
}

const handlePageChange = () => {
  // 不再使用
}

const handlePageSizeChange = () => {
  // 不再使用
}

const handleSync = async () => {
  try {
    analysisLoading.value = true
    await gitlabApi.syncRepositories({})
    ElMessage.success('仓库同步任务已启动')
    setTimeout(loadAnalysisData, 2000)
  } catch (error) {
    ElMessage.error('启动同步任务失败')
  } finally {
    analysisLoading.value = false
  }
}

const viewBranches = (row) => {
  router.push({
    name: 'Branches',
    query: { repo_id: row.id, repo_name: row.name },
  })
}

const viewPermissions = (row) => {
  ElMessage.info(`查看仓库 ${row.name} 的权限`)
  // TODO: 实现权限查看功能
}

// Tab 切换处理
const handleTabChange = (tabName) => {
  if (tabName === 'list') {
    // 列表页使用同样的分析数据，无需额外加载
    if (repositories.value.length === 0) {
      loadAnalysisData()
    }
  } else if (tabName === 'analysis') {
    if (repositories.value.length === 0) {
      loadAnalysisData()
    }
  }
}

// 监听筛选变化，重新渲染图表
watch(filteredRepositories, () => {
  setTimeout(() => {
    renderCharts()
  }, 100)
}, { deep: true })

onMounted(() => {
  // 默认加载分析数据
  loadAnalysisData()
  
  // 窗口大小变化时重新调整图表
  window.addEventListener('resize', () => {
    Object.values(charts).forEach(chart => {
      if (chart) chart.resize()
    })
  })
})
</script>

<style lang="scss" scoped>
.repositories {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  // 分析页面样式
  .analysis-content {
    .stats-row {
      margin-bottom: 20px;
      
      .stat-card {
        cursor: default;
        transition: all 0.3s;
        
        &:hover {
          transform: translateY(-5px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        
        :deep(.el-card__body) {
          padding: 20px;
        }
        
        .stat-content {
          display: flex;
          align-items: center;
          gap: 20px;
          
          .stat-icon {
            font-size: 48px;
          }
          
          .stat-info {
            flex: 1;
            
            .stat-value {
              font-size: 32px;
              font-weight: bold;
              line-height: 1;
              margin-bottom: 8px;
            }
            
            .stat-label {
              font-size: 14px;
              color: #909399;
            }
          }
        }
        
        &.total {
          .stat-icon { color: #409EFF; }
          .stat-value { color: #409EFF; }
        }
        
        &.active {
          .stat-icon { color: #67C23A; }
          .stat-value { color: #67C23A; }
        }
        
        &.domains {
          .stat-icon { color: #E6A23C; }
          .stat-value { color: #E6A23C; }
        }
      }
    }
    
    .filter-card {
      margin-bottom: 20px;
      
      .filter-form {
        :deep(.el-form-item) {
          margin-bottom: 0;
        }
      }
    }
    
    .charts-row {
      margin-bottom: 20px;
      
      .chart-card {
        margin-bottom: 20px;
        
        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .chart-container {
          height: 350px;
        }
      }
    }
  }

  // 列表页面样式
  .list-content {
    .search-bar {
      margin-bottom: 20px;
    }

    .pagination {
      margin-top: 20px;
      display: flex;
      justify-content: flex-end;
    }
  }
}
</style>