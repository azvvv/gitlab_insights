/**
 * 格式化工具函数
 */

/**
 * 格式化日期时间
 * @param {string|Date} datetime - 日期时间字符串或Date对象
 * @param {string} format - 格式化模式，默认 'YYYY-MM-DD HH:mm:ss'
 * @returns {string} 格式化后的日期时间字符串
 */
export function formatDateTime(datetime, format = 'YYYY-MM-DD HH:mm:ss') {
  if (!datetime) return '-'
  
  const date = typeof datetime === 'string' ? new Date(datetime) : datetime
  
  if (isNaN(date.getTime())) return '-'
  
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  
  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}

/**
 * 格式化日期
 * @param {string|Date} date - 日期字符串或Date对象
 * @returns {string} 格式化后的日期字符串
 */
export function formatDate(date) {
  return formatDateTime(date, 'YYYY-MM-DD')
}

/**
 * 格式化时间
 * @param {string|Date} time - 时间字符串或Date对象
 * @returns {string} 格式化后的时间字符串
 */
export function formatTime(time) {
  return formatDateTime(time, 'HH:mm:ss')
}

/**
 * 格式化相对时间（如：3分钟前）
 * @param {string|Date} datetime - 日期时间
 * @returns {string} 相对时间描述
 */
export function formatRelativeTime(datetime) {
  if (!datetime) return '-'
  
  const date = typeof datetime === 'string' ? new Date(datetime) : datetime
  const now = new Date()
  const diff = now - date
  
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  if (seconds < 60) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  
  return formatDate(date)
}

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @returns {string} 格式化后的文件大小
 */
export function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 格式化数字（添加千分位分隔符）
 * @param {number} num - 数字
 * @returns {string} 格式化后的数字字符串
 */
export function formatNumber(num) {
  if (num === null || num === undefined) return '-'
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

/**
 * 格式化百分比
 * @param {number} value - 数值（0-1 或 0-100）
 * @param {number} decimals - 小数位数
 * @param {boolean} isDecimal - 是否为小数（0-1），默认 true
 * @returns {string} 格式化后的百分比字符串
 */
export function formatPercent(value, decimals = 2, isDecimal = true) {
  if (value === null || value === undefined) return '-'
  
  const percent = isDecimal ? value * 100 : value
  return `${percent.toFixed(decimals)}%`
}
