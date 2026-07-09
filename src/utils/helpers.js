/**
 * 导出数据为CSV文件（浏览器下载）
 * @param {Array} data - 要导出的数据数组
 * @param {Array} headers - 列头定义 [{ key: 'field', label: '列名' }]
 * @param {string} filename - 输出文件名
 */
export function exportToCsv(data, headers, filename = 'export.csv') {
  if (!data || data.length === 0) {
    ElMessage.warning('没有数据可导出')
    return
  }

  // 构建CSV内容
  const headerRow = headers.map(h => `"${h.label}"`).join(',')
  const dataRows = data.map(row => {
    return headers.map(h => {
      const val = row[h.key]
      if (val === null || val === undefined) return '""'
      return `"${String(val).replace(/"/g, '""')}"`
    }).join(',')
  })

  const csvContent = '\uFEFF' + [headerRow, ...dataRows].join('\n')

  // 创建Blob下载
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * 格式化金额（亿/万单位）
 */
export function formatMoney(value) {
  if (value === null || value === undefined) return '-'
  const num = Number(value)
  if (Math.abs(num) >= 1e8) {
    return (num / 1e8).toFixed(2) + '亿'
  } else if (Math.abs(num) >= 1e4) {
    return (num / 1e4).toFixed(2) + '万'
  }
  return num.toLocaleString()
}

/**
 * 格式化百分比
 */
export function formatPercent(value) {
  if (value === null || value === undefined) return '-'
  return (Number(value) * 100).toFixed(2) + '%'
}

/**
 * 格式化涨跌幅显示
 */
export function formatChange(value) {
  if (value === null || value === undefined) return '-'
  const sign = value >= 0 ? '+' : ''
  return sign + Number(value).toFixed(2)
}
