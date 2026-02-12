<template>
  <div class="home">
    <!-- 主内容区 -->
    <main class="main-content">
      <div class="content-wrapper">
        <!-- 主内容区布局 -->
        <div class="main-content-grid">
          <!-- 左侧 Tab 内容区 -->
          <div class="tab-section">
          <!-- Tab 导航栏 -->
          <div class="tab-nav">
            <div
              v-for="tab in systemTabs"
              :key="tab.id"
              :class="['tab-item', { active: activeTab === tab.id }]"
              @click="activeTab = tab.id"
            >
              <el-icon>
                <component :is="tab.icon" />
              </el-icon>
              <span class="tab-label">{{ tab.label }}</span>
              <div v-if="tab.badge" class="tab-badge">{{ tab.badge }}</div>
            </div>
          </div>

          <!-- Tab 内容区 -->
          <div class="tab-content">
            <transition name="fade-slide" mode="out-in">
              <!-- 动态渲染当前激活的分组内容 -->
              <div 
                v-if="currentGroup"
                :key="currentGroup.group_name"
                class="tab-pane"
              >
                <div class="pane-header">
                  <!-- <div class="pane-icon-wrapper" :class="`${currentGroup.group_name.toLowerCase()}-icon`"> -->
                  <div class="pane-icon-wrapper devops-icon">
                    <el-icon><DataLine /></el-icon>
                    <!-- <el-icon>
                      <component :is="devops-icon" />
                    </el-icon> -->
                  </div>
                  <div class="pane-info">
                    <h3 class="pane-title">{{ currentGroup.group_title }}</h3>
                  </div>
                </div>
                <div class="links-grid">
                  <a 
                    v-for="link in currentGroup.links"
                    :key="link.id"
                    :href="link.url" 
                    target="_blank"
                    class="link-card"
                  >
                    <div class="link-icon">
                      <el-icon><Reading /></el-icon>
                    </div>
                    <div class="link-content">
                      <span class="link-title">{{ link.title }}</span>
                      <span class="link-desc">{{ link.description }}</span>
                    </div>
                    <el-icon class="arrow"><ArrowRight /></el-icon>
                  </a>
                </div>
                <el-empty v-if="currentGroup.links.length === 0" description="暂无文档链接" />
              </div>
            </transition>
          </div>
        </div>

        <!-- 右侧 AI 智能助手区域 -->
        <div class="ai-sidebar">
          <div class="ai-header">
            <div class="ai-icon-wrapper">
              <el-icon class="pulse-icon"><ChatDotRound /></el-icon>
            </div>
            <div class="ai-badge">开发中</div>
          </div>
          
          <h3 class="ai-title">AI 智能助手</h3>
          <p class="ai-desc">基于 AI 的智能代码分析与协作工具</p>
          
          <div class="ai-status">
            <div class="status-icon">
              <el-icon><ChatDotRound /></el-icon>
            </div>
            <div class="status-info">
              <p class="status-title">即将上线</p>
              <p class="status-desc">敬请期待强大的 AI 功能</p>
            </div>
          </div>

          <div class="ai-features">
            <div class="feature-item">
              <el-icon><Check /></el-icon>
              <span>智能代码审查</span>
            </div>
            <div class="feature-item">
              <el-icon><Check /></el-icon>
              <span>问题智能问答</span>
            </div>
            <div class="feature-item">
              <el-icon><Check /></el-icon>
              <span>工作流程优化</span>
            </div>
          </div>
        </div>
        </div>
        <!-- End of main-content-grid -->

        <!-- 底部新增板块 -->
        <div class="bottom-sections">
          <!-- 系统监控大屏 -->
          <div class="monitoring-dashboard">
            <div class="dashboard-header">
              <div class="header-content">
                <div class="title-wrapper">
                  <div class="icon-badge">
                    <el-icon><Monitor /></el-icon>
                  </div>
                  <div>
                    <h3 class="section-title">平台服务监控</h3>
                    <p class="section-subtitle">实时监控 DevOps 平台服务状态与响应时间</p>
                  </div>
                </div>
                <el-button 
                  type="primary" 
                  :icon="Refresh" 
                  @click="refreshMonitoring"
                  :loading="monitoringLoading"
                  size="default"
                  round
                >
                  {{ monitoringLoading ? '检测中...' : '刷新状态' }}
                </el-button>
              </div>
            </div>

            <div class="services-container">
              <a 
                v-for="service in platformServices" 
                :key="service.key"
                :href="service.url"
                target="_blank"
                class="service-card"
              >
                <div class="service-header">
                  <div class="service-icon-wrapper" :style="{ background: service.color }">
                    <el-icon>
                      <component :is="service.icon" />
                    </el-icon>
                  </div>
                  <div class="service-status" :class="service.status">
                    <el-icon v-if="service.status === 'online'">
                      <SuccessFilled />
                    </el-icon>
                    <el-icon v-else-if="service.status === 'offline'">
                      <CircleClose />
                    </el-icon>
                    <el-icon v-else class="rotating">
                      <Loading />
                    </el-icon>
                    <span>
                      {{ service.status === 'online' ? '在线' : service.status === 'offline' ? '离线' : '检测中' }}
                    </span>
                  </div>
                </div>
                
                <div class="service-content">
                  <h4 class="service-name">{{ service.name }}</h4>
                  <p class="service-desc">{{ service.desc }}</p>
                </div>
                
                <div class="service-footer">
                  <div class="service-info">
                    <span class="info-label">地址</span>
                    <span class="info-value">{{ service.ip }}<span v-if="service.port">:{{ service.port }}</span></span>
                  </div>
                  <div class="service-info">
                    <span class="info-label">响应</span>
                    <span class="info-value" :class="{ 'text-success': service.status === 'online', 'text-error': service.status === 'offline' }">
                      {{ service.responseTime }}
                    </span>
                  </div>
                </div>
                
                <div class="status-bar" :class="service.status">
                  <div class="status-fill"></div>
                </div>
                
                <div class="link-indicator">
                  <el-icon><ArrowRight /></el-icon>
                  <span>点击访问</span>
                </div>
              </a>
            </div>

            <div class="system-status-bar">
              <div class="status-left">
                <div class="status-indicator" :class="systemHealth.status">
                  <span class="pulse-dot"></span>
                  <span class="status-label">整体状态</span>
                  <span class="status-value">{{ systemHealth.text }}</span>
                </div>
                <div class="status-count">
                  <span class="count-label">在线平台</span>
                  <span class="count-value">{{ systemHealth.onlineCount }}/{{ systemHealth.totalCount }}</span>
                </div>
              </div>
              <div class="status-right">
                <span class="update-time">
                  <el-icon><Clock /></el-icon>
                  最后检测: {{ systemHealth.lastUpdate }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <!-- End of content-wrapper -->
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  FolderOpened,
  Grid,
  Tickets,
  Reading,
  Finished,
  PieChart,
  ChatDotRound,
  MagicStick,
  Check,
  ArrowRight,
  User,
  Refresh,
  Link,
  Top,
  Bottom,
  Document,
  DataAnalysis,
  Setting,
  Monitor,
  Connection,
  TrendCharts,
  Clock,
  Compass,
  Box,
  Lock,
  SuccessFilled,
  WarningFilled,
  CircleClose,
  Loading,
} from '@element-plus/icons-vue'
import { systemApi } from '@/api/system'
import { getHomeLinks } from '@/api/homeLink'

// Tab 相关状态
const activeTab = ref('')

// 首页链接数据
const docLinkGroups = ref([])
const platformLinks = ref([])

// 从分组的链接中计算排序值（取最小 sort_order 的百位数）
const getGroupSortOrder = (group) => {
  if (!group.links || group.links.length === 0) {
    return 999  // 没有链接的分组排最后
  }
  
  // 找到该分组中最小的 sort_order
  const minSortOrder = Math.min(...group.links.map(link => link.sort_order || 999))
  
  // 取百位数作为分组排序值
  // 例如：sort_order = 123 → 百位数 = 1
  //       sort_order = 234 → 百位数 = 2
  return Math.floor(minSortOrder / 100)
}

// 动态生成系统 Tab 配置（从 docLinkGroups 中提取并排序）
const systemTabs = computed(() => {
  return docLinkGroups.value
    .map(group => ({
      id: group.group_name.toLowerCase(),
      label: group.group_title,
      icon: getGroupIcon(group.group_name),
      badge: null,
      sortOrder: getGroupSortOrder(group)  // 从数据库 sort_order 计算
    }))
    .sort((a, b) => a.sortOrder - b.sortOrder)  // 按排序值排序
})

// 根据分组名称获取图标
const getGroupIcon = (groupName) => {
  const iconMap = {
    'devops': 'FolderOpened',
    'jira': 'Tickets',
    'ai': 'ChatDotRound',
    'ai 开发平台': 'ChatDotRound',
    'ai工具': 'MagicStick'
  }
  return iconMap[groupName.toLowerCase()] || 'Document'
}

// 获取当前激活的分组
const currentGroup = computed(() => {
  return docLinkGroups.value.find(
    group => group.group_name.toLowerCase() === activeTab.value
  )
})

// 监控数据 - 平台服务状态
const monitoringLoading = ref(false)

// 平台服务运行时状态（status, responseTime）
const platformStatus = ref({})

const platformServices = computed(() => {
  return platformLinks.value.map(link => {
    const key = link.title.toLowerCase().replace(/\s+/g, '_')
    const runtimeStatus = platformStatus.value[key] || {}
    
    return {
      key,
      name: link.title,
      desc: link.description || '',
      ip: link.ip || '',
      port: link.port || '',
      url: link.url,
      status: runtimeStatus.status || 'checking',
      responseTime: runtimeStatus.responseTime || '-',
      icon: link.icon || 'Connection',
      color: link.color || 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }
  })
})

const systemHealth = ref({
  status: 'checking',
  text: '正在检测平台状态...',
  lastUpdate: '刚刚',
  onlineCount: 0,
  totalCount: 6
})

// 刷新监控数据 - 检查平台状态
const refreshMonitoring = async () => {
  monitoringLoading.value = true
  
  try {
    // 重置所有状态为检测中
    platformServices.value.forEach(service => {
      platformStatus.value[service.key] = {
        status: 'checking',
        responseTime: '-'
      }
    })
    
    systemHealth.value.status = 'checking'
    systemHealth.value.text = '正在检测平台状态...'
    
    // 真实的 ping 检测（前端实现）
    // 使用 fetch + 图片加载 的方式来检测网站可用性
    
    const checkPromises = platformServices.value.map(async (service) => {
      const startTime = performance.now()
      
      try {
        // 方法1: 尝试使用 fetch 检测（no-cors 模式）
        // 即使跨域，只要请求能发出去并得到响应，就说明服务可用
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 8000) // 8秒超时
        
        await fetch(service.url, {
          method: 'HEAD', // 使用 HEAD 请求，不获取内容
          mode: 'no-cors', // 允许跨域请求
          cache: 'no-store', // 不使用缓存
          signal: controller.signal
        })
        
        clearTimeout(timeoutId)
        const responseTime = Math.round(performance.now() - startTime)
        
        // fetch 成功（即使是 opaque 响应也说明服务在线）
        platformStatus.value[service.key] = {
          status: 'online',
          responseTime: `${responseTime}ms`
        }
        
      } catch (error) {
        // 检查是否是超时错误
        if (error.name === 'AbortError') {
          platformStatus.value[service.key] = {
            status: 'offline',
            responseTime: '超时'
          }
        } else {
          // 网络错误、服务不可达
          platformStatus.value[service.key] = {
            status: 'offline',
            responseTime: '无法访问'
          }
        }
      }
    })
    
    // 等待所有检测完成
    await Promise.all(checkPromises)
    
    // 统计在线数量
    const onlineCount = Object.values(platformStatus.value).filter(s => s.status === 'online').length
    const totalCount = platformServices.value.length
    
    systemHealth.value.onlineCount = onlineCount
    systemHealth.value.totalCount = totalCount
    
    // 更新整体状态
    if (onlineCount === totalCount) {
      systemHealth.value.status = 'healthy'
      systemHealth.value.text = '所有平台运行正常'
    } else if (onlineCount > 0) {
      systemHealth.value.status = 'warning'
      systemHealth.value.text = `${totalCount - onlineCount} 个平台离线`
    } else {
      systemHealth.value.status = 'error'
      systemHealth.value.text = '所有平台离线'
    }
    
    systemHealth.value.lastUpdate = new Date().toLocaleTimeString('zh-CN')
    
    ElMessage.success('平台状态检测完成')
  } catch (error) {
    console.error('检测平台状态失败:', error)
    ElMessage.error('检测平台状态失败')
  } finally {
    monitoringLoading.value = false
  }
}

// 加载首页链接数据
const loadHomeLinks = async () => {
  try {
    const res = await getHomeLinks()
    if (res.data) {
      docLinkGroups.value = res.data.doc_links || []
      platformLinks.value = res.data.platform_links || []
      
      // 设置默认选中的分组（选择 sort_order 最小的分组）
      if (docLinkGroups.value.length > 0 && !activeTab.value) {
        // 按 sort_order 排序后取第一个
        const sortedGroups = [...docLinkGroups.value].sort((a, b) => {
          return getGroupSortOrder(a) - getGroupSortOrder(b)
        })
        
        if (sortedGroups.length > 0) {
          activeTab.value = sortedGroups[0].group_name.toLowerCase()
        }
      }
    }
  } catch (error) {
    console.error('加载首页链接失败:', error)
  }
}

// 组件挂载时获取监控数据
onMounted(async () => {
  await loadHomeLinks()
  refreshMonitoring()
})

const showComingSoon = (feature) => {
  ElMessage.info(`${feature}功能即将上线，敬请期待！`)
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.home {
  .main-content {
    max-width: 1400px;
    margin: 0 auto;
    padding: 60px 40px 100px;
    
    .content-wrapper {
      display: flex;
      flex-direction: column;
      gap: 40px;
      
      // 主内容区布局
      .main-content-grid {
        display: flex;
        gap: 32px;
        align-items: stretch;
      }
      
      // 底部新增板块
      .bottom-sections {
        display: flex;
        flex-direction: column;
        gap: 32px;
        
        // 系统监控大屏
        .monitoring-dashboard {
          background: white;
          border-radius: 28px;
          overflow: hidden;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
          border: 1px solid rgba(226, 232, 240, 0.8);
          transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
          
          &:hover {
            box-shadow: 0 16px 48px rgba(0, 0, 0, 0.12);
            transform: translateY(-4px);
          }
          
          .dashboard-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 32px 40px;
            
            .header-content {
              display: flex;
              align-items: center;
              justify-content: space-between;
              
              .title-wrapper {
                display: flex;
                align-items: center;
                gap: 16px;
                
                .icon-badge {
                  width: 56px;
                  height: 56px;
                  background: rgba(255, 255, 255, 0.2);
                  backdrop-filter: blur(10px);
                  border-radius: 16px;
                  display: flex;
                  align-items: center;
                  justify-content: center;
                  border: 2px solid rgba(255, 255, 255, 0.3);
                  
                  .el-icon {
                    font-size: 28px;
                    color: white;
                  }
                }
                
                .section-title {
                  font-size: 26px;
                  font-weight: 700;
                  color: white;
                  margin-bottom: 6px;
                  letter-spacing: -0.5px;
                }
                
                .section-subtitle {
                  font-size: 14px;
                  color: rgba(255, 255, 255, 0.85);
                  line-height: 1.5;
                }
              }
              
              .el-button {
                background: rgba(255, 255, 255, 0.2);
                backdrop-filter: blur(10px);
                border: 2px solid rgba(255, 255, 255, 0.3);
                color: white;
                font-weight: 600;
                padding: 12px 28px;
                
                &:hover {
                  background: rgba(255, 255, 255, 0.3);
                  border-color: rgba(255, 255, 255, 0.5);
                  transform: translateY(-2px);
                }
              }
            }
          }
          
          .services-container {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 24px;
            padding: 40px;
            background: #fafbfc;
            
            .service-card {
              background: white;
              border-radius: 20px;
              padding: 24px;
              border: 2px solid #f1f5f9;
              transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
              position: relative;
              overflow: hidden;
              text-decoration: none;
              display: block;
              cursor: pointer;
              
              &::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, transparent, #3b82f6, transparent);
                opacity: 0;
                transition: opacity 0.3s;
              }
              
              &:hover {
                transform: translateY(-8px);
                box-shadow: 0 12px 32px rgba(0, 0, 0, 0.1);
                border-color: #3b82f6;
                
                &::before {
                  opacity: 1;
                }
                
                .service-icon-wrapper {
                  transform: scale(1.1) rotate(5deg);
                }
                
                .link-indicator {
                  opacity: 1;
                  transform: translateX(0);
                }
              }
              
              .service-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 16px;
                
                .service-icon-wrapper {
                  width: 52px;
                  height: 52px;
                  border-radius: 14px;
                  display: flex;
                  align-items: center;
                  justify-content: center;
                  transition: all 0.3s;
                  
                  .el-icon {
                    font-size: 26px;
                    color: white;
                  }
                }
                
                .service-status {
                  display: flex;
                  align-items: center;
                  gap: 6px;
                  padding: 6px 14px;
                  border-radius: 20px;
                  font-size: 13px;
                  font-weight: 700;
                  
                  .el-icon {
                    font-size: 16px;
                  }
                  
                  &.online {
                    background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
                    color: #059669;
                  }
                  
                  &.offline {
                    background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
                    color: #dc2626;
                  }
                  
                  &.checking {
                    background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
                    color: #3b82f6;
                  }
                  
                  .rotating {
                    animation: rotate 1s linear infinite;
                  }
                }
              }
              
              .service-content {
                margin-bottom: 16px;
                
                .service-name {
                  font-size: 20px;
                  font-weight: 700;
                  color: #0f172a;
                  margin-bottom: 6px;
                }
                
                .service-desc {
                  font-size: 13px;
                  color: #64748b;
                  line-height: 1.5;
                }
              }
              
              .service-footer {
                display: flex;
                gap: 16px;
                margin-bottom: 12px;
                
                .service-info {
                  flex: 1;
                  display: flex;
                  flex-direction: column;
                  gap: 4px;
                  
                  .info-label {
                    font-size: 11px;
                    color: #94a3b8;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                  }
                  
                  .info-value {
                    font-size: 13px;
                    color: #1e293b;
                    font-weight: 600;
                    font-family: 'Monaco', 'Menlo', monospace;
                    
                    &.text-success {
                      color: #059669;
                    }
                    
                    &.text-error {
                      color: #dc2626;
                    }
                  }
                }
              }
              
              .status-bar {
                height: 4px;
                background: #f1f5f9;
                border-radius: 2px;
                overflow: hidden;
                position: relative;
                margin-bottom: 12px;
                
                .status-fill {
                  height: 100%;
                  width: 0;
                  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
                }
                
                &.online .status-fill {
                  width: 100%;
                  background: linear-gradient(90deg, #10b981 0%, #059669 100%);
                }
                
                &.offline .status-fill {
                  width: 100%;
                  background: linear-gradient(90deg, #ef4444 0%, #dc2626 100%);
                }
                
                &.checking .status-fill {
                  width: 60%;
                  background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
                  animation: pulse-width 1.5s ease-in-out infinite;
                }
              }
              
              .link-indicator {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                padding: 8px 16px;
                background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
                border-radius: 10px;
                font-size: 13px;
                font-weight: 600;
                color: #64748b;
                opacity: 0;
                transform: translateX(-8px);
                transition: all 0.3s;
                
                .el-icon {
                  font-size: 16px;
                }
              }
            }
          }
          
            .system-status-bar {
              display: flex;
              align-items: center;
              justify-content: space-between;
              padding: 20px 40px;
              background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
              border-top: 2px solid #e2e8f0;
              
              .status-left {
                display: flex;
                align-items: center;
                gap: 24px;
                
                .status-indicator {
                  display: flex;
                  align-items: center;
                  gap: 12px;
                  padding: 10px 20px;
                  background: white;
                  border-radius: 24px;
                  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
                  
                  .pulse-dot {
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    position: relative;
                    animation: pulse-glow 2s infinite;
                  }
                  
                  .status-label {
                    font-size: 13px;
                    color: #64748b;
                    font-weight: 500;
                  }
                  
                  .status-value {
                    font-size: 14px;
                    font-weight: 700;
                  }
                  
                  &.healthy {
                    .pulse-dot {
                      background: #10b981;
                      box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
                    }
                    .status-value {
                      color: #059669;
                    }
                  }
                  
                  &.warning {
                    .pulse-dot {
                      background: #f59e0b;
                      box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.7);
                    }
                    .status-value {
                      color: #d97706;
                    }
                  }
                  
                  &.error {
                    .pulse-dot {
                      background: #ef4444;
                      box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
                    }
                    .status-value {
                      color: #dc2626;
                    }
                  }
                  
                  &.checking {
                    .pulse-dot {
                      background: #3b82f6;
                      box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7);
                    }
                    .status-value {
                      color: #2563eb;
                    }
                  }
                }
                
                .status-count {
                  display: flex;
                  flex-direction: column;
                  gap: 4px;
                  
                  .count-label {
                    font-size: 12px;
                    color: #94a3b8;
                    font-weight: 600;
                  }
                  
                  .count-value {
                    font-size: 20px;
                    font-weight: 700;
                    color: #0f172a;
                    font-family: 'Monaco', 'Menlo', monospace;
                  }
                }
              }            .status-right {
              .update-time {
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 13px;
                color: #64748b;
                
                .el-icon {
                  font-size: 16px;
                }
              }
            }
          }
        }
      }
      
      // 左侧 Tab 区域 (70%)
      .tab-section {
        flex: 1;
        flex: 1;
        background: white;
        border-radius: 24px;
        overflow: hidden;
        box-shadow: 0 4px 24px rgba(59, 130, 246, 0.08);
        border: 1px solid rgba(59, 130, 246, 0.08);
        display: flex;
        flex-direction: column;
        
        // Tab 导航栏
        .tab-nav {
          display: flex;
          gap: 8px;
          padding: 16px 20px;
          background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
          border-bottom: 2px solid rgba(59, 130, 246, 0.1);
          overflow-x: auto;
          
          &::-webkit-scrollbar {
            height: 4px;
          }
          
          &::-webkit-scrollbar-thumb {
            background: rgba(59, 130, 246, 0.3);
            border-radius: 2px;
          }
          
          .tab-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 12px 24px;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.3s;
            white-space: nowrap;
            position: relative;
            background: white;
            border: 2px solid transparent;
            
            .el-icon {
              font-size: 18px;
              color: #64748b;
              transition: all 0.3s;
            }
            
            .tab-label {
              font-size: 15px;
              font-weight: 600;
              color: #475569;
              transition: all 0.3s;
            }
            
            .tab-badge {
              padding: 2px 8px;
              border-radius: 10px;
              font-size: 11px;
              font-weight: 700;
              background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
              color: white;
            }
            
            &:hover {
              background: white;
              border-color: rgba(59, 130, 246, 0.2);
              transform: translateY(-2px);
              box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
              
              .el-icon {
                color: #3b82f6;
              }
              
              .tab-label {
                color: #1e40af;
              }
            }
            
            &.active {
              background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
              border-color: #2563eb;
              box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3);
              
              .el-icon {
                color: white;
              }
              
              .tab-label {
                color: white;
              }
              
              &::after {
                content: '';
                position: absolute;
                bottom: -18px;
                left: 50%;
                transform: translateX(-50%);
                width: 0;
                height: 0;
                border-left: 8px solid transparent;
                border-right: 8px solid transparent;
                border-top: 8px solid #2563eb;
              }
            }
          }
        }
        
        // Tab 内容区
        .tab-content {
          padding: 36px;
          flex: 1;
          display: flex;
          flex-direction: column;
          
          .tab-pane {
            .pane-header {
              display: flex;
              align-items: flex-start;
              gap: 20px;
              margin-bottom: 32px;
              padding-bottom: 24px;
              border-bottom: 2px solid rgba(59, 130, 246, 0.1);
              
              .pane-icon-wrapper {
                width: 72px;
                height: 72px;
                border-radius: 18px;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
                box-shadow: 0 8px 24px rgba(59, 130, 246, 0.2);
                
                .el-icon {
                  font-size: 36px;
                  color: white;
                }
                
                &.devops-icon {
                  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
                }
                
                &.jira-icon {
                  background: linear-gradient(135deg, #1e40af 0%, #1e3a8a 100%);
                }
              }
              
              .pane-info {
                flex: 1;
                
                .pane-title {
                  font-size: 28px;
                  font-weight: 700;
                  color: #1e293b;
                  margin-bottom: 8px;
                  letter-spacing: -0.5px;
                }
                
                .pane-desc {
                  font-size: 15px;
                  color: #64748b;
                  line-height: 1.6;
                }
              }
            }
            
            .links-grid {
              display: grid;
              grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
              gap: 16px;
              
              .link-card {
                display: flex;
                align-items: center;
                gap: 16px;
                padding: 18px 20px;
                border-radius: 14px;
                background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
                border: 1px solid rgba(59, 130, 246, 0.1);
                text-decoration: none;
                transition: all 0.3s;
                cursor: pointer;
                position: relative;
                overflow: hidden;
                
                &::before {
                  content: '';
                  position: absolute;
                  left: 0;
                  top: 0;
                  bottom: 0;
                  width: 4px;
                  background: linear-gradient(180deg, #3b82f6 0%, #2563eb 100%);
                  transform: scaleY(0);
                  transition: transform 0.3s;
                }
                
                .link-icon {
                  width: 48px;
                  height: 48px;
                  background: white;
                  border-radius: 12px;
                  display: flex;
                  align-items: center;
                  justify-content: center;
                  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.12);
                  flex-shrink: 0;
                  transition: all 0.3s;
                  
                  .el-icon {
                    font-size: 22px;
                    color: #3b82f6;
                  }
                }
                
                .link-content {
                  flex: 1;
                  display: flex;
                  flex-direction: column;
                  gap: 4px;
                  
                  .link-title {
                    font-size: 15px;
                    font-weight: 600;
                    color: #1e293b;
                  }
                  
                  .link-desc {
                    font-size: 13px;
                    color: #94a3b8;
                  }
                }
                
                .arrow {
                  font-size: 18px;
                  color: #3b82f6;
                  opacity: 0;
                  transform: translateX(-8px);
                  transition: all 0.3s;
                }
                
                &:hover {
                  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
                  border-color: rgba(59, 130, 246, 0.3);
                  transform: translateY(-4px);
                  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.15);
                  
                  &::before {
                    transform: scaleY(1);
                  }
                  
                  .link-icon {
                    transform: scale(1.1);
                    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
                    
                    .el-icon {
                      color: white;
                    }
                  }
                  
                  .link-content .link-title {
                    color: #1e40af;
                  }
                  
                  .arrow {
                    opacity: 1;
                    transform: translateX(0);
                  }
                }
              }
            }
          }
        }
      }
      
      // 右侧 AI 智能助手区域
      .ai-sidebar {
        width: 340px;
        flex-shrink: 0;
        background: white;
        border-radius: 24px;
        padding: 32px;
        box-shadow: 0 4px 24px rgba(59, 130, 246, 0.08);
        border: 1px solid rgba(59, 130, 246, 0.08);
        display: flex;
        flex-direction: column;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        
        &:hover {
          transform: translateY(-8px);
          box-shadow: 0 20px 48px rgba(59, 130, 246, 0.15);
          border-color: rgba(59, 130, 246, 0.2);
        }
        
        .ai-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 24px;
          
          .ai-icon-wrapper {
            width: 64px;
            height: 64px;
            background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 8px 24px rgba(59, 130, 246, 0.3);
            
            .pulse-icon {
              font-size: 32px;
              color: white;
              animation: pulse 2s infinite;
            }
          }
          
          .ai-badge {
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
            color: white;
            box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
          }
        }
        
        .ai-title {
          font-size: 24px;
          font-weight: 700;
          color: #1e293b;
          margin-bottom: 12px;
          letter-spacing: -0.5px;
        }
        
        .ai-desc {
          font-size: 14px;
          color: #64748b;
          line-height: 1.6;
          margin-bottom: 28px;
        }
        
        .ai-status {
          display: flex;
          align-items: flex-start;
          gap: 14px;
          padding: 20px;
          background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
          border-radius: 16px;
          margin-bottom: 28px;
          border: 2px dashed rgba(59, 130, 246, 0.2);
          
          .status-icon {
            width: 48px;
            height: 48px;
            background: white;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
            flex-shrink: 0;
            
            .el-icon {
              font-size: 24px;
              color: #3b82f6;
            }
          }
          
          .status-info {
            flex: 1;
            
            .status-title {
              font-size: 16px;
              font-weight: 700;
              color: #1e40af;
              margin-bottom: 6px;
            }
            
            .status-desc {
              font-size: 13px;
              color: #64748b;
              line-height: 1.5;
            }
          }
        }
        
        .ai-features {
          display: flex;
          flex-direction: column;
          gap: 12px;
          flex: 1;
          
          .feature-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 14px 16px;
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            border-radius: 12px;
            border: 1px solid rgba(59, 130, 246, 0.1);
            color: #334155;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s;
            
            .el-icon {
              color: #3b82f6;
              font-size: 18px;
              flex-shrink: 0;
            }
            
            &:hover {
              background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
              border-color: rgba(59, 130, 246, 0.3);
              transform: translateX(4px);
            }
          }
        }
      }
    }
  }
}

// Tab 切换动画
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.08);
  }
}

@keyframes pulse-dot {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

@keyframes pulse-glow {
  0% {
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(16, 185, 129, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);
  }
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes pulse-width {
  0%, 100% {
    width: 40%;
  }
  50% {
    width: 80%;
  }
}

@media (max-width: 1200px) {
  .home {
    .main-content {
      .content-wrapper {
        .main-content-grid {
          flex-direction: column;
          
          .ai-sidebar {
            width: 100%;
          }
        }
        
        .bottom-sections {
          .monitoring-dashboard {
            .services-container {
              grid-template-columns: repeat(2, 1fr);
            }
          }
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .home {
    .main-content {
      padding: 40px 20px;
      
      .content-wrapper {
        gap: 24px;
        
        .tab-section {
          .tab-content {
            padding: 24px 20px;
            
            .tab-pane {
              .links-grid {
                grid-template-columns: 1fr;
              }
            }
          }
        }
        
        .bottom-sections {
          .monitoring-dashboard {
            .dashboard-header {
              padding: 24px 20px;
              
              .header-content {
                flex-direction: column;
                gap: 16px;
                align-items: flex-start;
              }
            }
            
            .services-container {
              grid-template-columns: 1fr;
              padding: 24px 20px;
              gap: 16px;
            }
            
            .system-status-bar {
              padding: 16px 20px;
              flex-direction: column;
              gap: 12px;
              align-items: flex-start;
            }
          }
        }
      }
    }
  }
}
</style>
          transform: translateY(-8px);
          box-shadow: 0 20px 40px rgba(0, 0, 0, 0.12);
          border-color: transparent;
        }
        
        .card-icon-wrapper {
          width: 64px;
          height: 64px;
          border-radius: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-bottom: 24px;
          
          .el-icon {
            font-size: 32px;
            color: white;
          }
          
          &.gitlab-icon {
            background: linear-gradient(135deg, #fc6d26 0%, #e24329 100%);
          }
          
          &.jira-icon {
            background: linear-gradient(135deg, #0052cc 0%, #0747a6 100%);
          }
          
          &.ai-icon {
            background: linear-gradient(135deg, #67c23a 0%, #529b2e 100%);
          }
        }
        
        .card-title {
          font-size: 24px;
          font-weight: 600;
          color: #1f2937;
          margin-bottom: 12px;
        }
        
        .card-desc {
          font-size: 15px;
          color: #6b7280;
          margin-bottom: 28px;
          line-height: 1.6;
        }
        
        .links-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
          
          .link-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 14px 16px;
            border-radius: 10px;
            background: #f9fafb;
            color: #374151;
            text-decoration: none;
            transition: all 0.3s;
            cursor: pointer;
            font-size: 15px;
            font-weight: 500;
            
            .el-icon {
              font-size: 18px;
              color: #6b7280;
              transition: all 0.3s;
            }
            
            .arrow {
              margin-left: auto;
              opacity: 0;
              transform: translateX(-8px);
              transition: all 0.3s;
            }
            
            &:hover {
              background: #f3f4f6;
              color: #1f2937;
              transform: translateX(4px);
              
              .el-icon {
                color: #409eff;
              }
              
              .arrow {
                opacity: 1;
                transform: translateX(0);
              }
            }
          }
        }
        
        .ai-placeholder {
          .ai-coming-soon {
            text-align: center;
            padding: 32px 20px;
            background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
            border-radius: 12px;
            margin-bottom: 24px;
            
            .pulse-icon {
              font-size: 56px;
              color: #67c23a;
              margin-bottom: 16px;
              animation: pulse 2s infinite;
            }
            
            .coming-title {
              font-size: 20px;
              font-weight: 600;
              color: #1f2937;
              margin-bottom: 8px;
            }
            
            .coming-desc {
              font-size: 14px;
              color: #6b7280;
            }
          }
          
          .ai-features-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
            
            .ai-feature-item {
              display: flex;
              align-items: center;
              gap: 12px;
              padding: 12px 16px;
              background: #f9fafb;
              border-radius: 8px;
              color: #374151;
              font-size: 15px;
              
              .el-icon {
                color: #67c23a;
                font-size: 18px;
              }
            }
          }
        }
      }
    }
  }


