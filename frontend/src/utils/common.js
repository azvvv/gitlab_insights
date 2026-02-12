import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.locale('zh-cn')
dayjs.extend(relativeTime)

/**
 * 格式化日期
 */
export function formatDate(date, format = 'YYYY-MM-DD HH:mm:ss') {
  if (!date) return '-'
  return dayjs(date).format(format)
}

/**
 * 相对时间
 */
export function fromNow(date) {
  if (!date) return '-'
  return dayjs(date).fromNow()
}

/**
 * 格式化文件大小
 */
export function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

/**
 * 下载文件
 */
export function downloadFile(blob, filename) {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

/**
 * 防抖函数
 */
export function debounce(fn, delay = 300) {
  let timer = null
  return function (...args) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      fn.apply(this, args)
    }, delay)
  }
}

/**
 * 节流函数
 */
export function throttle(fn, delay = 300) {
  let timer = null
  return function (...args) {
    if (timer) return
    timer = setTimeout(() => {
      fn.apply(this, args)
      timer = null
    }, delay)
  }
}

/**
 * 深拷贝
 */
export function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') return obj
  if (obj instanceof Date) return new Date(obj)
  if (obj instanceof RegExp) return new RegExp(obj)
  
  const cloneObj = new obj.constructor()
  for (let key in obj) {
    if (obj.hasOwnProperty(key)) {
      cloneObj[key] = deepClone(obj[key])
    }
  }
  return cloneObj
}

/**
 * 获取任务状态标签类型
 */
export function getTaskStatusType(status) {
  const typeMap = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info',
  }
  return typeMap[status] || 'info'
}

/**
 * 获取任务状态文本
 */
export function getTaskStatusText(status) {
  const textMap = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
  }
  return textMap[status] || status
}

/**
 * 导出数据为CSV文件
 * @param {Array} data - 要导出的数据数组，每个元素是一个对象
 * @param {String} filename - 文件名（不含扩展名）
 * @param {Object} options - 可选配置
 * @param {Array} options.columns - 列配置数组，格式：[{ key: 'field', label: '列名', formatter: (value) => {} }]
 * @param {Boolean} options.addTimestamp - 是否在文件名添加时间戳，默认true
 * @returns {Boolean} - 是否导出成功
 */
export function exportToCSV(data, filename, options = {}) {
  if (!data || data.length === 0) {
    return false
  }

  try {
    const { columns, addTimestamp = true } = options
    
    let headers, rows
    
    if (columns && columns.length > 0) {
      // 使用自定义列配置
      headers = columns.map(col => col.label)
      rows = data.map(item => 
        columns.map(col => {
          let value = item[col.key]
          // 应用自定义格式化函数
          if (col.formatter && typeof col.formatter === 'function') {
            value = col.formatter(value, item)
          }
          return value
        })
      )
    } else {
      // 自动从第一条数据提取所有字段
      headers = Object.keys(data[0])
      rows = data.map(item => Object.values(item))
    }
    
    // 构建CSV内容
    const csvContent = [
      headers.join(','),
      ...rows.map(row => 
        row.map(cell => {
          const value = cell ?? ''
          const strValue = String(value)
          // 处理包含逗号、换行符、引号的值
          if (strValue.includes(',') || strValue.includes('\n') || strValue.includes('"')) {
            return `"${strValue.replace(/"/g, '""')}"`
          }
          return strValue
        }).join(',')
      )
    ].join('\n')
    
    // 添加BOM以支持Excel正确显示中文
    const BOM = '\uFEFF'
    const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' })
    
    // 生成文件名
    let finalFilename = filename
    if (addTimestamp) {
      const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-')
      finalFilename = `${filename}_${timestamp}`
    }
    finalFilename += '.csv'
    
    // 下载文件
    downloadFile(blob, finalFilename)
    
    return true
  } catch (error) {
    console.error('CSV导出失败:', error)
    return false
  }
}
