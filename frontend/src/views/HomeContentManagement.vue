<template>
  <div class="home-content-management">
    <el-card class="page-header">
      <h2>首页内容维护</h2>
      <p>管理首页显示的文档链接和平台监控配置</p>
    </el-card>

    <el-tabs v-model="activeTab" class="content-tabs">
      <!-- 文档链接管理 Tab -->
      <el-tab-pane label="文档链接管理" name="doc_links">
        <div class="tab-content">
          <div class="toolbar">
            <el-button type="primary" @click="openAddDialog('doc_links')">
              <el-icon><Plus /></el-icon>
              添加文档链接
            </el-button>
          </div>

          <el-collapse v-model="activeGroups" accordion>
            <el-collapse-item 
              v-for="group in docLinkGroups" 
              :key="group.group_name"
              :name="group.group_name"
            >
              <template #title>
                <div class="group-header">
                  <span class="group-title">{{ group.group_title }}</span>
                  <span class="group-count">{{ group.links.length }} 个链接</span>
                </div>
              </template>

              <el-table :data="group.links" stripe>
                <el-table-column label="排序" width="80" align="center">
                  <template #default="{ row }">
                    <span>{{ row.sort_order }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="title" label="标题" min-width="150" />
                <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
                <el-table-column prop="url" label="链接地址" min-width="250" show-overflow-tooltip>
                  <template #default="{ row }">
                    <el-link :href="row.url" target="_blank" type="primary">
                      {{ row.url }}
                    </el-link>
                  </template>
                </el-table-column>
                <el-table-column label="状态" width="100" align="center">
                  <template #default="{ row }">
                    <el-tag :type="row.is_active ? 'success' : 'info'">
                      {{ row.is_active ? '启用' : '禁用' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="220" align="center" fixed="right">
                  <template #default="{ row }">
                    <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
                    <el-button 
                      size="small" 
                      :type="row.is_active ? 'warning' : 'success'"
                      @click="toggleActive(row)"
                    >
                      {{ row.is_active ? '禁用' : '启用' }}
                    </el-button>
                    <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-collapse-item>
          </el-collapse>

          <el-empty v-if="docLinkGroups.length === 0" description="暂无文档链接" />
        </div>
      </el-tab-pane>

      <!-- 平台监控管理 Tab -->
      <el-tab-pane label="平台监控管理" name="platform_links">
        <div class="tab-content">
          <div class="toolbar">
            <el-button type="primary" @click="openAddDialog('platform_links')">
              <el-icon><Plus /></el-icon>
              添加平台监控
            </el-button>
          </div>

          <el-table :data="platformLinks" stripe>
            <el-table-column label="排序" width="80" align="center">
              <template #default="{ row }">
                <span>{{ row.sort_order }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="title" label="平台名称" min-width="120" />
            <el-table-column prop="description" label="描述" min-width="150" show-overflow-tooltip />
            <el-table-column label="IP:端口" min-width="150">
              <template #default="{ row }">
                <span>{{ row.ip }}:{{ row.port }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="url" label="访问地址" min-width="200" show-overflow-tooltip>
              <template #default="{ row }">
                <el-link :href="row.url" target="_blank" type="primary">
                  {{ row.url }}
                </el-link>
              </template>
            </el-table-column>
            <el-table-column prop="icon" label="图标" width="100" align="center" />
            <el-table-column label="颜色" width="120" align="center">
              <template #default="{ row }">
                <div 
                  class="color-preview" 
                  :style="{ background: row.color }"
                  :title="row.color"
                ></div>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'">
                  {{ row.is_active ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="220" align="center" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
                <el-button 
                  size="small" 
                  :type="row.is_active ? 'warning' : 'success'"
                  @click="toggleActive(row)"
                >
                  {{ row.is_active ? '禁用' : '启用' }}
                </el-button>
                <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-empty v-if="platformLinks.length === 0" description="暂无平台监控配置" />
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 添加/编辑对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="dialogTitle"
      width="600px"
      @close="resetForm"
    >
      <el-form 
        ref="formRef" 
        :model="formData" 
        :rules="formRules" 
        label-width="100px"
      >
        <el-form-item label="分类" prop="category">
          <el-radio-group v-model="formData.category" :disabled="isEdit">
            <el-radio label="doc_links">文档链接</el-radio>
            <el-radio label="platform_links">平台监控</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="分组" prop="group_name" v-if="formData.category === 'doc_links'">
          <el-select 
            v-model="formData.group_name" 
            placeholder="请选择或输入分组"
            filterable
            allow-create
            default-first-option
          >
            <el-option 
              v-for="group in availableGroups" 
              :key="group.group_name"
              :label="group.group_title" 
              :value="group.group_name" 
            />
          </el-select>
          <span class="form-tip">可选择已有分组或输入新分组名称（英文，如：devops、jira、ai）</span>
        </el-form-item>

        <el-form-item label="标题" prop="title">
          <el-input v-model="formData.title" placeholder="请输入标题" />
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input 
            v-model="formData.description" 
            type="textarea" 
            :rows="2"
            placeholder="请输入描述（可选）" 
          />
        </el-form-item>

        <el-form-item label="链接地址" prop="url">
          <el-input v-model="formData.url" placeholder="https://example.com" />
        </el-form-item>

        <!-- 平台监控专属字段 -->
        <template v-if="formData.category === 'platform_links'">
          <el-form-item label="IP地址" prop="ip">
            <el-input v-model="formData.ip" placeholder="10.10.89.209" />
          </el-form-item>

          <el-form-item label="端口" prop="port">
            <el-input v-model="formData.port" placeholder="80" />
          </el-form-item>

          <el-form-item label="图标" prop="icon">
            <el-input v-model="formData.icon" placeholder="Connection" />
            <span class="form-tip">Element Plus 图标名称</span>
          </el-form-item>

          <el-form-item label="渐变色" prop="color">
            <el-input 
              v-model="formData.color" 
              type="textarea"
              :rows="2"
              placeholder="linear-gradient(135deg, #667eea 0%, #764ba2 100%)" 
            />
            <span class="form-tip">CSS 渐变色代码</span>
          </el-form-item>
        </template>

        <el-form-item label="排序" prop="sort_order">
          <el-input-number v-model="formData.sort_order" :min="0" :max="999" />
          <span class="form-tip">数字越小越靠前</span>
        </el-form-item>

        <el-form-item label="启用状态">
          <el-switch v-model="formData.is_active" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getHomeLinks,
  createHomeLink,
  updateHomeLink,
  deleteHomeLink,
  toggleHomeLinkActive
} from '@/api/homeLink'

// 数据状态
const activeTab = ref('doc_links')
const activeGroups = ref([])
const docLinkGroups = ref([])
const platformLinks = ref([])
const availableGroups = ref([])  // 可用的分组列表

// 对话框状态
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref(null)

const formData = reactive({
  category: 'doc_links',
  group_name: '',
  title: '',
  description: '',
  url: '',
  icon: '',
  color: '',
  ip: '',
  port: '',
  sort_order: 0,
  is_active: true
})

// 监听分类变化，重新加载分组
watch(() => formData.category, (newCategory) => {
  if (newCategory === 'doc_links') {
    // 文档链接类别：从已加载的数据中提取分组
    extractGroups()
    formData.group_name = ''
  } else if (newCategory === 'platform_links') {
    // 平台监控：固定为 monitoring 分组
    formData.group_name = 'monitoring'
  }
})

const dialogTitle = computed(() => {
  return isEdit.value ? '编辑链接' : '添加链接'
})

// 表单验证规则
const formRules = {
  category: [
    { required: true, message: '请选择分类', trigger: 'change' }
  ],
  group_name: [
    { 
      required: true, 
      message: '请选择分组', 
      trigger: 'change',
      validator: (rule, value, callback) => {
        if (formData.category === 'doc_links' && !value) {
          callback(new Error('文档链接必须选择分组'))
        } else {
          callback()
        }
      }
    }
  ],
  title: [
    { required: true, message: '请输入标题', trigger: 'blur' }
  ],
  url: [
    { required: true, message: '请输入链接地址', trigger: 'blur' },
    { type: 'url', message: '请输入有效的URL', trigger: 'blur' }
  ]
}

// 加载数据
const loadData = async () => {
  try {
    // 管理页面需要加载所有记录，包括未激活的
    const res = await getHomeLinks(true)
    if (res.data) {
      docLinkGroups.value = res.data.doc_links || []
      platformLinks.value = res.data.platform_links || []
      
      // 从加载的数据中提取分组列表
      extractGroups()
    }
  } catch (error) {
    ElMessage.error('加载数据失败: ' + error.message)
  }
}

// 从已加载的数据中提取分组列表（去重）
const extractGroups = () => {
  // 从 docLinkGroups 中提取所有分组
  const groups = docLinkGroups.value.map(group => ({
    group_name: group.group_name,
    group_title: group.group_title
  }))
  
  // 去重（虽然 docLinkGroups 本身已经是按分组的，但为了确保唯一性）
  const uniqueGroups = groups.filter((group, index, self) =>
    index === self.findIndex(g => g.group_name === group.group_name)
  )
  
  availableGroups.value = uniqueGroups
}

// 打开添加对话框
const openAddDialog = (category) => {
  isEdit.value = false
  resetForm()
  formData.category = category
  if (category === 'platform_links') {
    formData.group_name = 'monitoring'
  }
  dialogVisible.value = true
}

// 打开编辑对话框
const openEditDialog = (row) => {
  isEdit.value = true
  Object.assign(formData, { ...row })
  dialogVisible.value = true
}

// 重置表单
const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  Object.assign(formData, {
    category: 'doc_links',
    group_name: '',
    title: '',
    description: '',
    url: '',
    icon: '',
    color: '',
    ip: '',
    port: '',
    sort_order: 0,
    is_active: true
  })
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    
    try {
      const data = { ...formData }
      
      // 平台监控自动设置分组
      if (data.category === 'platform_links') {
        data.group_name = 'monitoring'
      }
      
      if (isEdit.value) {
        await updateHomeLink(data.id, data)
        ElMessage.success('更新成功')
      } else {
        await createHomeLink(data)
        ElMessage.success('创建成功')
      }
      
      dialogVisible.value = false
      loadData()  // 重新加载数据，会自动更新分组列表
    } catch (error) {
      ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
    } finally {
      submitting.value = false
    }
  })
}

// 切换启用状态
const toggleActive = async (row) => {
  try {
    await toggleHomeLinkActive(row.id)
    ElMessage.success('状态已更新')
    loadData()
  } catch (error) {
    ElMessage.error('操作失败: ' + error.message)
  }
}

// 删除
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除链接"${row.title}"吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await deleteHomeLink(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + error.message)
    }
  }
}

onMounted(() => {
  loadData()  // 加载数据时会自动调用 extractGroups()
})
</script>

<style scoped lang="scss">
.home-content-management {
  padding: 20px;

  .page-header {
    margin-bottom: 20px;

    h2 {
      margin: 0 0 8px 0;
      font-size: 24px;
      font-weight: 600;
      color: #303133;
    }

    p {
      margin: 0;
      font-size: 14px;
      color: #909399;
    }
  }

  .content-tabs {
    background: white;
    border-radius: 8px;
    padding: 20px;

    .tab-content {
      .toolbar {
        margin-bottom: 16px;
      }

      .group-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        width: 100%;
        padding-right: 20px;

        .group-title {
          font-size: 16px;
          font-weight: 600;
          color: #303133;
        }

        .group-count {
          font-size: 14px;
          color: #909399;
        }
      }

      .color-preview {
        width: 80px;
        height: 32px;
        border-radius: 4px;
        border: 1px solid #dcdfe6;
        margin: 0 auto;
      }
    }
  }

  .form-tip {
    display: block;
    font-size: 12px;
    color: #909399;
    margin-top: 4px;
  }
}

:deep(.el-collapse-item__header) {
  font-size: 16px;
  font-weight: 500;
}

:deep(.el-table) {
  margin-top: 12px;
}
</style>
