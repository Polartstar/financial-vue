<template>
  <div class="compare-page">
    <div class="page-card">
      <div class="card-title">
        <el-icon :size="20"><Opportunity /></el-icon>
        个股对比
      </div>

      <!-- 对比选择 -->
      <div style="margin-bottom:20px">
        <p style="color:#606266;margin-bottom:12px">
          选择2~4只股票进行对比分析，从下方下拉框中选择股票（最多4只）：
        </p>
        <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center">
          <el-select v-model="compareCodes" multiple placeholder="选择要对比的股票" style="width:400px" :max="4" @change="onCompareChange">
            <el-option v-for="s in allStocks" :key="s.code" :label="`${s.code} ${s.name}`" :value="s.code" />
          </el-select>
          <el-button type="primary" :disabled="compareCodes.length < 2" @click="doCompare">
            <el-icon><Opportunity /></el-icon> 开始对比
          </el-button>
          <el-button @click="clearCompare">清空</el-button>
          <el-tag v-if="compareCodes.length > 0" type="info">
            已选择 {{ compareCodes.length }} 只股票
          </el-tag>
        </div>
      </div>

      <!-- 对比结果表格 -->
      <div v-if="compareData.length > 0">
        <el-table :data="compareTableData" stripe style="width:100%" border>
          <el-table-column prop="indicator" label="对比指标" width="160" fixed>
            <template #default="{ row }">
              <span style="font-weight:600">{{ row.indicator }}</span>
            </template>
          </el-table-column>
          <el-table-column v-for="c in compareData" :key="c.code" :label="`${c.code} ${c.name}`" min-width="160">
            <template #default="{ row }">
              <span :class="{ 'highlight-value': isBestValue(row.indicator, c) }">
                {{ row[c.code] || '-' }}
              </span>
            </template>
          </el-table-column>
        </el-table>

        <!-- 导出按钮 -->
        <div style="margin-top:16px">
          <el-button type="success" @click="exportCompareCsv">
            <el-icon><Download /></el-icon> 导出对比数据CSV
          </el-button>
        </div>
      </div>

      <el-empty v-else-if="!loading" description="请选择2~4只股票开始对比" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getStocks, getStockByCode, getIndicatorByStock } from '@/api'
import { exportToCsv } from '@/utils/helpers'

const store = useStore()
const router = useRouter()

const allStocks = ref([])
const compareCodes = ref([...store.getters.getCompareList])
const compareData = ref([])
const loading = ref(false)

const compareTableData = computed(() => {
  if (compareData.value.length === 0) return []

  const indicators = [
    { key: 'price', label: '最新价(USD)' },
    { key: 'changePercent', label: '涨跌幅(%)' },
    { key: 'marketCap', label: '市值' },
    { key: 'pe', label: '市盈率(PE)' },
    { key: 'pb', label: '市净率(PB)' },
    { key: 'roe', label: '净资产收益率(ROE)' },
    { key: 'debtRatio', label: '资产负债率' },
    { key: 'high', label: '当日最高价' },
    { key: 'low', label: '当日最低价' },
    { key: 'volume', label: '成交量' }
  ]

  return indicators.map(ind => {
    const row = { indicator: ind.label }
    compareData.value.forEach(c => {
      let val = c[ind.key]
      if (ind.key === 'roe' || ind.key === 'debtRatio') {
        val = (val * 100).toFixed(2) + '%'
      } else if (typeof val === 'number') {
        val = val.toFixed(2)
      }
      row[c.code] = val
    })
    return row
  })
})

// 简单标记最优值（涨跌幅最高标记绿色）
const isBestValue = (indicator, stock) => {
  return false
}

const onCompareChange = () => {
  store.commit('CLEAR_COMPARE')
  compareCodes.value.forEach(code => store.commit('ADD_TO_COMPARE', code))
}

const doCompare = async () => {
  if (compareCodes.value.length < 2) {
    ElMessage.warning('请至少选择2只股票进行对比')
    return
  }
  loading.value = true
  try {
    const data = []
    for (const code of compareCodes.value) {
      const res = await getStockByCode(code)
      const stockDetail = res[0]
      if (stockDetail) {
        const indicatorRes = await getIndicatorByStock(code)
        const ind = indicatorRes[0] || {}
        data.push({ ...stockDetail, ...ind })
      }
    }
    compareData.value = data
  } catch (e) {
    ElMessage.error('获取对比数据失败')
  } finally {
    loading.value = false
  }
}

const clearCompare = () => {
  compareCodes.value = []
  compareData.value = []
  store.commit('CLEAR_COMPARE')
}

const exportCompareCsv = () => {
  const headers = [
    { key: 'indicator', label: '对比指标' }
  ]
  compareData.value.forEach(c => {
    headers.push({ key: c.code, label: `${c.code} ${c.name}` })
  })
  exportToCsv(compareTableData.value, headers, `compare_${new Date().toISOString().slice(0,10)}.csv`)
  ElMessage.success('对比数据导出成功')
}

onMounted(async () => {
  try {
    allStocks.value = await getStocks()
  } catch (e) { /* ignore */ }
})
</script>

<style scoped>
.highlight-value {
  color: #67c23a;
  font-weight: 600;
}
</style>
