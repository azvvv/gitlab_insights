<template>
  <div class="branch-rules">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>分支规则管理</span>
          <el-button type="primary" icon="Plus" @click="handleCreate">
            创建规则
          </el-button>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="tableData"
        style="width: 100%"
        stripe
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="rule_name" label="规则名称" width="150" />
        <el-table-column prop="branch_pattern" label="匹配模式" width="200" />
        <el-table-column prop="branch_type" label="分支类型" width="120" />
        <el-table-column prop="retention_days" label="保留天数" width="100" />
        <el-table-column prop="priority" label="优先级" width="100" />
        <el-table-column prop="branch_count" label="匹配分支数" width="120" />
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_active" type="success">启用</el-tag>
            <el-tag v-else type="info">禁用</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">
              删除
            </el-button>
            <el-button type="success" size="small" @click="handleApply(row)">
              应用
            </el-button>
          </template>
        </el-table-column>
      </el-table>

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

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
      >
        <el-form-item label="规则名称" prop="rule_name">
          <el-input v-model="formData.rule_name" placeholder="请输入规则名称" />
        </el-form-item>
        <el-form-item label="匹配模式" prop="branch_pattern">
          <el-input v-model="formData.branch_pattern" placeholder="例如: feature/*" />
        </el-form-item>
        <el-form-item label="分支类型" prop="branch_type">
          <el-select v-model="formData.branch_type" placeholder="请选择分支类型">
            <el-option label="功能分支" value="feature" />
            <el-option label="开发分支" value="develop" />
            <el-option label="发布分支" value="release" />
            <el-option label="热修复分支" value="hotfix" />
            <el-option label="主分支" value="main" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="保留天数" prop="retention_days">
          <el-input-number
            v-model="formData.retention_days"
            :min="1"
            :max="365"
            placeholder="不填表示永久保留"
          />
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-input-number
            v-model="formData.priority"
            :min="0"
            :max="100"
            placeholder="数值越大优先级越高"
          />
        </el-form-item>
        <el-form-item label="是否可删除" prop="is_deletable">
          <el-switch v-model="formData.is_deletable" />
        </el-form-item>
        <el-form-item label="是否启用" prop="is_active">
          <el-switch v-model="formData.is_active" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入规则描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { branchApi } from '@/api'
import { formatDate } from '@/utils/common'

const loading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('创建规则')
const submitting = ref(false)
const formRef = ref(null)

const formData = reactive({
  id: null,
  rule_name: '',
  branch_pattern: '',
  branch_type: '',
  retention_days: null,
  priority: 0,
  is_deletable: true,
  is_active: true,
  description: '',
})

const formRules = {
  rule_name: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
  branch_pattern: [{ required: true, message: '请输入匹配模式', trigger: 'blur' }],
  branch_type: [{ required: true, message: '请选择分支类型', trigger: 'change' }],
}

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const loadData = async () => {
  loading.value = true
  try {
    const res = await branchApi.getRules({
      page: pagination.page,
      page_size: pagination.pageSize,
    })
    tableData.value = res.rules || []
    pagination.total = res.count || 0
  } catch (error) {
    ElMessage.error('加载规则列表失败')
  } finally {
    loading.value = false
  }
}

const handlePageChange = () => {
  loadData()
}

const handlePageSizeChange = () => {
  pagination.page = 1
  loadData()
}

const handleCreate = () => {
  dialogTitle.value = '创建规则'
  formData.id = null
  formData.rule_name = ''
  formData.branch_pattern = ''
  formData.branch_type = ''
  formData.retention_days = null
  formData.priority = 0
  formData.is_deletable = true
  formData.is_active = true
  formData.description = ''
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑规则'
  formData.id = row.id
  formData.rule_name = row.rule_name
  formData.branch_pattern = row.branch_pattern
  formData.branch_type = row.branch_type
  formData.retention_days = row.retention_days
  formData.priority = row.priority
  formData.is_deletable = row.is_deletable
  formData.is_active = row.is_active
  formData.description = row.description || ''
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        const data = {
          rule_name: formData.rule_name,
          branch_pattern: formData.branch_pattern,
          branch_type: formData.branch_type,
          retention_days: formData.retention_days,
          priority: formData.priority,
          is_deletable: formData.is_deletable,
          is_active: formData.is_active,
          description: formData.description,
        }

        if (formData.id) {
          await branchApi.updateRule(formData.id, data)
          ElMessage.success('规则更新成功')
        } else {
          await branchApi.createRule(data)
          ElMessage.success('规则创建成功')
        }

        dialogVisible.value = false
        loadData()
      } catch (error) {
        ElMessage.error('操作失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确定要删除规则 "${row.name}" 吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(async () => {
      try {
        await branchApi.deleteRule(row.id)
        ElMessage.success('删除成功')
        loadData()
      } catch (error) {
        ElMessage.error('删除失败')
      }
    })
    .catch(() => {})
}

const handleApply = async (row) => {
  try {
    loading.value = true
    await branchApi.applyRules({ rule_id: row.id })
    ElMessage.success('规则应用任务已启动')
  } catch (error) {
    ElMessage.error('应用规则失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style lang="scss" scoped>
.branch-rules {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
