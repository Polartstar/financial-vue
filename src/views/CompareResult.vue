<template>
  <div class="compare-result-page">
    <div class="page-card">
      <div class="card-title">
        <el-icon :size="20"><Opportunity /></el-icon>
        对比结果 — {{ stockCodes.length }} 只股票对比
      </div>

      <el-alert
        title="对比参数说明"
        type="info"
        show-icon
        :closable="false"
        style="margin-bottom:16px"
      >
        <template #default>
          <p>对比参数（通过路由传入）：<code>/compare/{{ stockCodes.join(',') }}</code></p>
          <p>股票代码：<el-tag v-for="c in stockCodes" :key="c" style="margin-right:4px">{{ c }}</el-tag></p>
        </template>
      </el-alert>

      <!-- 对比图表（雷达图） -->
      <div ref="radarRef" style="width:100%;height:400px" v-loading="loading"></div>

      <!-- 详细数据表格 -->
      <div v-if="compareData.length > 0" style="margin-top:20px">
        <el-table :data="tableData" stripe border style="width:100%">
          <el-table-column prop="indicator" label="指标" width="150" fixed>
            <template #default="{ row }">
              <span style="font-weight:600">{{ row.indicator }}</span>
            </template>
          </el-table-column>
          <el-table-column v-for="c in compareData" :key="c.code" :label="`${c.code} ${c.name}`" min-width="150">
            <template #default="{ row }">
              {{ row[c.code] || '-' }}
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { getStockByCode, getIndicatorByStock } from '@/api'

const props = defineProps({ ids: String })
const route = useRoute()

const stockCodes = computed(() => {
  const ids = props.ids || route.params.ids || ''
  return ids.split(',').filter(Boolean)
})

const compareData = ref([])
const loading = ref(true)
const radarRef = ref(null)
let chartInstance = null

// compute计算属性：将原始指标数据转换为对比表格的行列格式
const tableData = computed(() => {
  if (compareData.value.length === 0) return []

  const indicators = [
    { key: 'price', label: '最新价(USD)' },
    { key: 'changePercent', label: '涨跌幅(%)' },
    { key: 'marketCap', label: '市值' },
    { key: 'high', label: '最高价' },
    { key: 'low', label: '最低价' },
    { key: 'volume', label: '成交量' },
    { key: 'pe', label: '市盈率(PE)' },
    { key: 'pb', label: '市净率(PB)' },
    { key: 'roe', label: 'ROE' },
    { key: 'debtRatio', label: '资产负债率' }
  ]


   // compute计算属性2衔接
  return indicators.map(ind => {
    const row = { indicator: ind.label }
    compareData.value.forEach(c => {
      let val = c[ind.key]
      if (ind.key === 'roe' || ind.key === 'debtRatio') {
        val = (val !== undefined ? (val * 100).toFixed(2) + '%' : '-')
      } else if (typeof val === 'number') {
        val = val.toFixed(2)
      } else {
        val = val || '-'
      }
      row[c.code] = val
    })
    return row
  })
})

// resize 防抖
let resizeRaf = null
const handleResize = () => {
  if (resizeRaf) cancelAnimationFrame(resizeRaf)
  resizeRaf = requestAnimationFrame(() => {
    try { chartInstance?.resize() } catch (e) { /* ignore */ }
  })
}

const renderRadar = () => {
  if (chartInstance) chartInstance.dispose()
  chartInstance = echarts.init(radarRef.value)
  window.addEventListener('resize', handleResize)

  const indicatorNames = ['涨跌幅', '市盈率', '市净率', 'ROE', '资产负债率']
  const maxValues = [5, 80, 50, 0.5, 1]

  const series = compareData.value.map(c => ({
    name: `${c.code} ${c.name}`,
    value: [
      Math.abs(c.changePercent || 0),
      c.pe ? Math.min(c.pe, 80) : 0,
      c.pb ? Math.min(c.pb, 50) : 0,
      c.roe || 0,
      c.debtRatio || 0
    ]
  }))

  chartInstance.setOption({
    title: { text: '股票指标雷达图', left: 'center' },
    tooltip: {},
    legend: {
      data: compareData.value.map(c => `${c.code} ${c.name}`),
      bottom: 0
    },
    radar: {
      indicator: indicatorNames.map((name, i) => ({ name, max: maxValues[i] })),
      center: ['50%', '50%'],
      radius: '60%'
    },
    series: [{
      type: 'radar',
      data: series,
      areaStyle: { opacity: 0.15 }
    }]
  })
}

onMounted(async () => {
  try {
    const data = []
    for (const code of stockCodes.value) {
      const stockRes = await getStockByCode(code)
      const stock = stockRes[0]
      if (stock) {
        const indRes = await getIndicatorByStock(code)
        const ind = indRes[0] || {}
        data.push({ ...stock, ...ind })
      }
    }
    compareData.value = data
    await nextTick()
    if (data.length > 0) renderRadar()
  } catch (e) {
    ElMessage.error('获取对比数据失败')
  } finally {
    loading.value = false
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (resizeRaf) cancelAnimationFrame(resizeRaf)
  chartInstance?.dispose()
})
</script>
