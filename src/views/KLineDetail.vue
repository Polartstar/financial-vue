<template>
  <div class="kline-page">
    <div class="page-card">
      <div class="card-title">
        <el-icon :size="20"><TrendCharts /></el-icon>
        {{ stockInfo ? `${stockInfo.code} ${stockInfo.name} - ` : '' }}K线图
      </div>

      <!-- 控制栏 -->
      <div style="margin-bottom:16px;display:flex;gap:12px;align-items:center;flex-wrap:wrap">
        <el-select v-model="selectedStock" filterable style="width:200px" @change="loadKLine">
          <el-option v-for="s in stockOptions" :key="s.code" :label="`${s.code} ${s.name}`" :value="s.code" />
        </el-select>
        <el-radio-group v-model="klinePeriod" @change="loadKLine">
          <el-radio-button value="10">10日</el-radio-button>
          <el-radio-button value="20">20日</el-radio-button>
          <el-radio-button value="30">30日</el-radio-button>
        </el-radio-group>
        <el-button type="primary" @click="loadKLine">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
        <el-tag v-if="lastPrice" type="success" effect="dark" size="large">
          最新价: ${{ lastPrice.close.toFixed(2) }}
        </el-tag>
      </div>

      <!-- K线图容器 -->
      <div ref="chartRef" style="width:100%;height:520px" v-loading="loading"></div>
    </div>

    <!-- 最近交易日数据表格 -->
    <div class="page-card">
      <div class="card-title">
        <el-icon :size="18"><List /></el-icon>
        K线数据明细
      </div>
      <el-table :data="klineData" stripe style="width:100%" max-height="300">
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="open" label="开盘价" width="120" />
        <el-table-column prop="close" label="收盘价" width="120" />
        <el-table-column prop="high" label="最高价" width="120" />
        <el-table-column prop="low" label="最低价" width="120" />
        <el-table-column prop="volume" label="成交量" width="140">
          <template #default="{ row }">
            {{ (row.volume / 10000).toFixed(0) }}万
          </template>
        </el-table-column>
      </el-table>
      <div style="margin-top:12px">
        <el-button type="success" @click="exportCsv">
          <el-icon><Download /></el-icon> 导出K线数据CSV
        </el-button>
      </div>
    </div>
  </div>
</template>

<!-- 让顶层的变量、函数直接暴露给模板，不再需要 export default { setup() { return {} } } 的样板（vue 2） -->
<script setup>
import { ref, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { getKLineData, getStocks, getStockByCode } from '@/api'
import { exportToCsv } from '@/utils/helpers'

const props = defineProps({ code: String })
const route = useRoute()

const chartRef = ref(null)
const chartInstance = ref(null)
const klineData = ref([])
const loading = ref(false)
const selectedStock = ref(props.code || route.params.code || 'AAPL')
// 控制K线周期切换，标准30天
const klinePeriod = ref('30')
const stockInfo = ref(null)
const stockOptions = ref([])
const lastPrice = ref(null)

// 数据转换
const formatKLineData = (data) => {
  return {
    dates: data.map(d => d.date),
    opens: data.map(d => d.open),
    closes: data.map(d => d.close),
    highs: data.map(d => d.high),
    lows: data.map(d => d.low),
    volumes: data.map(d => d.volume)
  }
}

// 初始化图表
const initChart = () => {
  if (chartInstance.value) {
    chartInstance.value.dispose()
    chartInstance.value = null
  }
  if (!chartRef.value) return
  chartInstance.value = echarts.init(chartRef.value)
  window.addEventListener('resize', handleResize)
}

// 用 requestAnimationFrame 防抖，避免 ResizeObserver loop 警告
let resizeRaf = null
const handleResize = () => {
  if (resizeRaf) cancelAnimationFrame(resizeRaf)
  resizeRaf = requestAnimationFrame(() => {
    try {
      chartInstance.value?.resize()
    } catch (e) {
      // 忽略 resize 过程中的 ECharts 内部错误
    }
  })
}

// （Core）
const renderKLine = (data) => {
  if (!data || data.length === 0) return
  if (!chartInstance.value) return

  const { dates, opens, closes, highs, lows, volumes } = formatKLineData(data)

  // 计算均价
  const avgPrice = (closes.reduce((a, b) => a + b, 0) / closes.length).toFixed(2)

  const option = {
    // mouse悬停
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      formatter: (params) => {
        if (!params || params.length < 2) return ''
        const k = params[0]
        const i = k.dataIndex
        return `<div style="font-size:13px">
          <b>${dates[i]}</b><br/>
          开盘: $${opens[i]}<br/>
          收盘: $${closes[i]}<br/>
          最高: $${highs[i]}<br/>
          最低: $${lows[i]}<br/>
          成交量: ${(volumes[i] / 10000).toFixed(0)}万
        </div>`
      }
    },
    // 两区域
    grid: [
      { left: '8%', right: '8%', top: '8%', height: '60%' },
      { left: '8%', right: '8%', top: '76%', height: '16%' }
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        axisLine: { lineStyle: { color: '#ccc' } },
        splitLine: { show: false }
      },
      {
        type: 'category',
        gridIndex: 1,
        data: dates,
        axisLabel: { show: false },
        splitLine: { show: false },
        axisLine: { show: false }
      }
    ],
    yAxis: [
      {
        type: 'value',
        scale: true,
        splitLine: { lineStyle: { type: 'dashed', color: '#eee' } },
        axisLabel: { formatter: '"{value}"' }
      },
      {
        type: 'value',
        gridIndex: 1,
        splitNumber: 2,
        axisLabel: { formatter: (v) => (v / 10000).toFixed(0) + '万' },
        splitLine: { show: false }
      }
    ],
    // 蜡烛图类型
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: opens.map((v, i) => [v, closes[i], lows[i], highs[i]]),
        itemStyle: {
          color: '#26a69a',
          color0: '#ef5350',
          borderColor: '#26a69a',
          borderColor0: '#ef5350'
        },
        // 计算好的均价线
        markLine: {
          silent: true,
          symbol: ['none', 'none'],
          data: [
            {
              yAxis: parseFloat(avgPrice),
              name: '均价',
              label: { formatter: `均价: $${avgPrice}` }
            }
          ],
          lineStyle: { type: 'dashed', color: '#ff9800' }
        }
      },
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumes.map((v, i) => ({
          value: v,
          itemStyle: {
            color: closes[i] >= opens[i] ? '#26a69a' : '#ef5350'
          }
        }))
      }
    ],
    // 拖拽
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 0, end: 100 },
      { type: 'slider', xAxisIndex: [0, 1], start: 0, end: 100, height: 20, bottom: 0 }
    ]
  }
// 渲染
  try {
    chartInstance.value.setOption(option, { notMerge: true, lazyUpdate: false })
  } catch (e) {
    console.warn('ECharts渲染异常:', e.message)
  }
}


const loadKLine = async () => {
  loading.value = true
  try {
    // 切换股票时同步更新卡片标题的股票信息
    try {
      // 获取股票信息
      const info = await getStockByCode(selectedStock.value)
      stockInfo.value = info[0] || null
    } catch (e) { /* ignore */ }

// 获取K线数据
    const data = await getKLineData(selectedStock.value, parseInt(klinePeriod.value))
    klineData.value = data
    if (data.length > 0) {
      lastPrice.value = data[data.length - 1]
    }
    // 确保DOM更新，初始化然后渲染数据
    await nextTick()
    initChart()
    renderKLine(data)
  
  } catch (e) {
    ElMessage.error('获取K线数据失败')
  } finally {
    loading.value = false
  }
}

const exportCsv = () => {
  const headers = [
    { key: 'date', label: '日期' },
    { key: 'open', label: '开盘价' },
    { key: 'close', label: '收盘价' },
    { key: 'high', label: '最高价' },
    { key: 'low', label: '最低价' },
    { key: 'volume', label: '成交量' }
  ]
  exportToCsv(klineData.value, headers, `kline_${selectedStock.value}_${new Date().toISOString().slice(0,10)}.csv`)
  ElMessage.success('K线数据导出成功')
}

onMounted(async () => {
  // 加载股票选项
  try {
    const allStocks = await getStocks()
    stockOptions.value = allStocks
  } catch (e) { /* ignore */ }

  // 获取当前股票信息
  try {
    const info = await getStockByCode(selectedStock.value)
    stockInfo.value = info[0] || null
  } catch (e) { /* ignore */ }

  loadKLine()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (resizeRaf) cancelAnimationFrame(resizeRaf)
  chartInstance.value?.dispose()
})
</script>
