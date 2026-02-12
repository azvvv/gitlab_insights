<template>
  <div class="not-found-page">
    <AppHeader />

    <main class="not-found-main">
      <div class="not-found-container">
        <el-result
          icon="error"
          title="404"
          sub-title="抱歉，您访问的页面不存在"
        >
          <template #extra>
            <el-button type="primary" @click="goHome">
              返回首页
            </el-button>
            <el-button @click="goBack">
              返回上一页
            </el-button>
          </template>
        </el-result>
      </div>
    </main>

    <AppFooter />
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import AppHeader from '@/components/common/AppHeader.vue'
import AppFooter from '@/components/common/AppFooter.vue'

const router = useRouter()

const goHome = () => {
  router.push('/')
}

const goBack = () => {
  router.go(-1)
}
</script>

<style lang="scss" scoped>
.not-found-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #f0f7ff 0%, #ffffff 100%);

  .not-found-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
  }

  .not-found-container {
    width: 100%;
    max-width: 600px;
  }
}

:deep(.el-result__title) {
  color: #303133;
}

:deep(.el-result__subtitle) {
  color: #606266;
}
</style>