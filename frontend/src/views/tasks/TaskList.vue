<template>
  <div class="task-list">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>任务列表</span>
          <el-button icon="Refresh" @click="loadData">刷新</el-button>
        </div>
      </template>

      <!-- 筛选栏 -->
      <div class="filter-bar">
        <el-select
          v-model="filterForm.status"
          placeholder="任务状态"
          clearable
          style="width: 150px"
          @change="handleFilter"
        >
          <el-option label="等待中" value="pending" />
          <el-option label="运行中" value="running" />
          <el-option label="已完成" value="completed" />
          <el-option label="失败" value="failed" />
          <el-option label="已取消" value="cancelled" />
        </el-select>
      </div>

      <!-- 数据表格 -->
      <el-table
        v-loading="loading"
        :data="tableData"
        style="width: 100%; margin-top: 20px"
        stripe
      >
        <el-table-column prop="task_id" label="任务ID" width="280" show-overflow-tooltip />
        <el-table-column prop="task_type" label="任务类型" width="150" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getTaskStatusType(row.status)">
              {{ getTaskStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度" width="100">
          <template #default="{ row }">
            <el-progress
              v-if="row.status === 'running'"
              :percentage="row.progress || 0"
              :status="row.status === 'failed' ? 'exception' : undefined"
            />
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="completed_at" label="完成时间" width="180">
          <template #default="{ row }">
            {{ row.completed_at ? formatDate(row.completed_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'running'"
              type="danger"
              size="small"
              @click="handleCancel(row)"
            >
              取消
            </el-button>
            <el-button type="primary" size="small" @click="viewDetail(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handlePageSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 任务详情对话框 -->
    <el-dialog
      v-model="detailVisible"
      title="任务详情"
      width="600px"
    >
      <el-descriptions :column="1" border>
        <el-descriptions-item label="任务ID">
          {{ currentTask?.task_id }}
        </el-descriptions-item>
        <el-descriptions-item label="任务类型">
          {{ currentTask?.task_type }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getTaskStatusType(currentTask?.status)">
            {{ getTaskStatusText(currentTask?.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDate(currentTask?.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="完成时间">
          {{ currentTask?.completed_at ? formatDate(currentTask.completed_at) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="结果">
          <pre v-if="currentTask?.result">{{ JSON.stringify(currentTask.result, null, 2) }}</pre>
          <span v-else>-</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { taskApi } from '@/api'
import { formatDate, getTaskStatusType, getTaskStatusText } from '@/utils/common'

const loading = ref(false)
const tableData = ref([])
const detailVisible = ref(false)
const currentTask = ref(null)

const filterForm = reactive({
  status: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }

    if (filterForm.status) {
      params.status = filterForm.status
    }

    const res = await taskApi.getTasks(params)
    tableData.value = res.tasks || []
    pagination.total = res.total || 0
  } catch (error) {
    ElMessage.error('加载任务列表失败')
  } finally {
    loading.value = false
  }
}

const handleFilter = () => {
  pagination.page = 1
  loadData()
}

const handlePageChange = () => {
  loadData()
}

const handlePageSizeChange = () => {
  pagination.page = 1
  loadData()
}

const viewDetail = async (row) => {
  try {
    const res = await taskApi.getTaskById(row.task_id)
    currentTask.value = res.task || row
    detailVisible.value = true
  } catch (error) {
    ElMessage.error('加载任务详情失败')
  }
}

const handleCancel = (row) => {
  ElMessageBox.confirm('确定要取消此任务吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(async () => {
      try {
        await taskApi.cancelTask(row.task_id)
        ElMessage.success('任务已取消')
        loadData()
      } catch (error) {
        ElMessage.error('取消任务失败')
      }
    })
    .catch(() => {})
}

onMounted(() => {
  loadData()
})
</script>

<style lang="scss" scoped>
.task-list {
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

  pre {
    background: #f5f7fa;
    padding: 10px;
    border-radius: 4px;
    max-height: 300px;
    overflow: auto;
  }
}
</style>
