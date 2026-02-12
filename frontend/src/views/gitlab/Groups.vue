<template>
  <div class="groups">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>分组列表</span>
          <el-button type="primary" icon="Refresh" @click="handleSync">
            同步分组
          </el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-input
          v-model="searchForm.keyword"
          placeholder="搜索分组名称或路径"
          clearable
          style="width: 300px"
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        >
          <template #append>
            <el-button icon="Search" @click="handleSearch" />
          </template>
        </el-input>
      </div>

      <el-table
        v-loading="loading"
        :data="tableData"
        style="width: 100%; margin-top: 20px"
        stripe
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="分组名称" width="200" />
        <el-table-column prop="path" label="路径" width="200" />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="visibility" label="可见性" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.visibility === 'public'" type="success">公开</el-tag>
            <el-tag v-else-if="row.visibility === 'private'" type="danger">私有</el-tag>
            <el-tag v-else type="warning">{{ row.visibility }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handlePageSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { gitlabApi } from '@/api'
import { formatDate } from '@/utils/common'

const loading = ref(false)
const tableData = ref([])

const searchForm = reactive({
  keyword: '',
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
    
    if (searchForm.keyword) {
      params.search = searchForm.keyword
    }

    const res = await gitlabApi.getGroups(params)
    tableData.value = res.groups || []
    pagination.total = res.total || 0
  } catch (error) {
    ElMessage.error('加载分组列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
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

const handleSync = async () => {
  try {
    loading.value = true
    await gitlabApi.syncGroups({})
    ElMessage.success('分组同步任务已启动')
    setTimeout(loadData, 2000)
  } catch (error) {
    ElMessage.error('启动同步任务失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style lang="scss" scoped>
.groups {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .search-bar {
    margin-bottom: 20px;
  }

  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
