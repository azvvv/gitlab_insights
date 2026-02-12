<template>
  <div class="settings">
    <el-card shadow="hover">
      <template #header>
        <span>系统设置</span>
      </template>

      <el-tabs v-model="activeTab">
        <!-- 系统信息 -->
        <el-tab-pane label="系统信息" name="system">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="系统名称">
              GitLab Insight
            </el-descriptions-item>
            <el-descriptions-item label="版本">
              v1.0.0
            </el-descriptions-item>
            <el-descriptions-item label="后端地址">
              {{ backendUrl }}
            </el-descriptions-item>
            <el-descriptions-item label="健康状态">
              <el-tag v-if="healthStatus" type="success">正常</el-tag>
              <el-tag v-else type="danger">异常</el-tag>
            </el-descriptions-item>
          </el-descriptions>

          <div class="mt-20">
            <el-button type="primary" @click="checkHealth">
              检查健康状态
            </el-button>
            <el-button type="danger" @click="initDatabase">
              初始化数据库
            </el-button>
          </div>
        </el-tab-pane>

        <!-- LDAP 配置（仅管理员可见） -->
        <el-tab-pane v-if="userStore.isAdmin" label="LDAP 配置" name="ldap">
          <el-descriptions v-if="ldapConfig" :column="1" border>
            <el-descriptions-item label="LDAP 启用">
              <el-tag v-if="ldapConfig.enabled" type="success">已启用</el-tag>
              <el-tag v-else type="info">未启用</el-tag>
            </el-descriptions-item>
            <el-descriptions-item v-if="ldapConfig.enabled" label="服务器地址">
              {{ ldapConfig.server }}
            </el-descriptions-item>
            <el-descriptions-item v-if="ldapConfig.enabled" label="Base DN">
              {{ ldapConfig.base_dn }}
            </el-descriptions-item>
          </el-descriptions>

          <div v-if="ldapConfig?.enabled" class="mt-20">
            <el-button type="primary" @click="testLdap">
              测试 LDAP 连接
            </el-button>
          </div>
        </el-tab-pane>

        <!-- 用户信息 -->
        <el-tab-pane label="用户信息" name="user">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="用户名">
              {{ userStore.username }}
            </el-descriptions-item>
            <el-descriptions-item label="用户ID">
              {{ userStore.userId }}
            </el-descriptions-item>
            <el-descriptions-item label="角色">
              <el-tag v-if="userStore.isAdmin" type="danger">管理员</el-tag>
              <el-tag v-else type="primary">普通用户</el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { systemApi, authApi } from '@/api'

const userStore = useUserStore()
const activeTab = ref('system')
const healthStatus = ref(false)
const ldapConfig = ref(null)
const backendUrl = ref('/api')

const checkHealth = async () => {
  try {
    await systemApi.healthCheck()
    healthStatus.value = true
    ElMessage.success('系统健康检查通过')
  } catch (error) {
    healthStatus.value = false
    ElMessage.error('系统健康检查失败')
  }
}

const initDatabase = () => {
  ElMessageBox.confirm(
    '此操作将初始化数据库，可能会创建必要的表结构。确定继续吗？',
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )
    .then(async () => {
      try {
        await systemApi.initDatabase()
        ElMessage.success('数据库初始化成功')
      } catch (error) {
        ElMessage.error('数据库初始化失败')
      }
    })
    .catch(() => {})
}

const testLdap = async () => {
  try {
    const res = await authApi.testLdap()
    if (res.success) {
      ElMessage.success('LDAP 连接测试成功')
    } else {
      ElMessage.error(res.error || 'LDAP 连接测试失败')
    }
  } catch (error) {
    ElMessage.error('LDAP 连接测试失败')
  }
}

const loadLdapConfig = async () => {
  if (!userStore.isAdmin) return

  try {
    const res = await authApi.getLdapConfig()
    ldapConfig.value = res.config
  } catch (error) {
    console.error('加载 LDAP 配置失败:', error)
  }
}

onMounted(() => {
  checkHealth()
  loadLdapConfig()
})
</script>

<style lang="scss" scoped>
.settings {
  .mt-20 {
    margin-top: 20px;
  }
}
</style>
