<template>
  <div class="log-list">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>日志管理</span>
          <el-button type="primary" icon="Refresh" @click="handleParse">
            解析日志
          </el-button>
        </div>
      </template>

      <div class="log-content">
        <el-alert
          title="日志管理功能正在开发中"
          description="此功能将提供日志查看、解析和管理功能"
          type="info"
          show-icon
          :closable="false"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'

const handleParse = () => {
  ElMessage.info('日志解析功能正在开发中')
}
</script>

<style scoped>
.log-list {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.log-content {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>