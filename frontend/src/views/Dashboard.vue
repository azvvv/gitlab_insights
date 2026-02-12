<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#409eff"><FolderOpened /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ stats.repositories }}</div>
              <div class="stat-label">仓库总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#67c23a"><Grid /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ stats.groups }}</div>
              <div class="stat-label">分组总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#e6a23c"><Operation /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ stats.branches }}</div>
              <div class="stat-label">分支总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#f56c6c"><Document /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ stats.logs }}</div>
              <div class="stat-label">日志记录</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mt-20">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>最近同步任务</span>
              <el-button text @click="refreshTasks">刷新</el-button>
            </div>
          </template>
          <el-table :data="recentTasks" style="width: 100%">
            <el-table-column prop="task_type" label="任务类型" width="150" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getTaskStatusType(row.status)">
                  {{ getTaskStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>快速操作</span>
          </template>
          <div class="quick-actions">
            <el-button 
              type="primary" 
              size="large"
              class="action-btn"
              @click="handleSyncAll"
            >
              <el-icon class="btn-icon"><Refresh /></el-icon>
              <span>同步所有数据</span>
            </el-button>
            <el-button 
              type="success" 
              size="large"
              class="action-btn"
              @click="handleParseLog"
            >
              <el-icon class="btn-icon"><Document /></el-icon>
              <span>解析日志</span>
            </el-button>
            <el-button 
              type="warning" 
              size="large"
              class="action-btn"
              @click="handleExport"
            >
              <el-icon class="btn-icon"><Download /></el-icon>
              <span>导出数据</span>
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Document, Download, FolderOpened, Grid, Operation } from '@element-plus/icons-vue'
import { gitlabApi, taskApi, systemApi } from '@/api'
import { formatDate, getTaskStatusType, getTaskStatusText } from '@/utils/common'

const stats = ref({
  repositories: 0,
  groups: 0,
  branches: 0,
  logs: 0,
})

const recentTasks = ref([])

const loadStats = async () => {
  try {
    // 使用新的统计接口
    const statsRes = await systemApi.getStatistics()
    
    console.log('Statistics Response:', statsRes)

    stats.value.repositories = statsRes.repositories || 0
    stats.value.groups = statsRes.groups || 0
    stats.value.branches = statsRes.branches || 0
    stats.value.logs = statsRes.logs || 0
  } catch (error) {
    console.error('加载统计数据失败:', error)
    ElMessage.error('加载统计数据失败')
  }
}

const loadRecentTasks = async () => {
  try {
    const res = await taskApi.getTasks({ page: 1, page_size: 5 })
    recentTasks.value = res.tasks || []
  } catch (error) {
    console.error('加载任务列表失败:', error)
  }
}

const refreshTasks = () => {
  loadRecentTasks()
}

const handleSyncAll = async () => {
  try {
    await gitlabApi.syncAll({})
    ElMessage.success('同步任务已启动')
    setTimeout(loadRecentTasks, 1000)
  } catch (error) {
    ElMessage.error('启动同步任务失败')
  }
}

const handleParseLog = async () => {
  try {
    await systemApi.parseLog({})
    ElMessage.success('日志解析任务已启动')
  } catch (error) {
    ElMessage.error('启动日志解析失败')
  }
}

const handleExport = () => {
  ElMessage.info('导出功能开发中')
}

onMounted(() => {
  loadStats()
  loadRecentTasks()
})
</script>

<style lang="scss" scoped>
.dashboard {
  .stat-card {
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
          color: #303133;
        }

        .stat-label {
          font-size: 14px;
          color: #909399;
          margin-top: 8px;
        }
      }
    }
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .quick-actions {
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding: 10px 0;

    .action-btn {
      width: 100%;
      height: 56px;
      font-size: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 8px;
      transition: all 0.3s ease;

      .btn-icon {
        font-size: 20px;
        margin-right: 8px;
      }

      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      }

      &:active {
        transform: translateY(0);
      }
    }
  }

  .mt-20 {
    margin-top: 20px;
  }
}
</style>
