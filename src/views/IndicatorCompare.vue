<template>
  <div class="indicator-page">
    <div class="page-card">
      <div class="card-title">
        <el-icon :size="20"><Coin /></el-icon>
        指标筛选与对比
      </div>

      <!-- 筛选条件 -->
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="行业">
          <el-select v-model="filters.industry" placeholder="全部" clearable style="width:120px">
            <el-option v-for="s in sectors" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="市盈率(PE)">
          <el-input-number v-model="filters.peMin" :min="0" :max="200" placeholder="最低" style="width:100px" /> ~
          <el-input-number v-model="filters.peMax" :min="0" :max="200" placeholder="最高" style="width:100px" />
        </el-form-item>
        <el-form-item label="市净率(PB)">
          <el-input-number v-model="filters.pbMin" :min="0" :max="100" placeholder="最低" style="width:100px" /> ~
          <el-input-number v-model="filters.pbMax" :min="0" :max="100" placeholder="最高" style="width:100px" />
        </el-form-item>
        <el-form-item label="ROE(%)">
          <el-input-number v-model="filters.roeMin" :min="0" :step="5" placeholder="最低" style="width:100px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchData">
            <el-icon><Search /></el-icon> 筛选
          </el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 指标选择 -->
      <div style="margin-bottom:16px">
        <span style="font-weight:600;margin-right:12px">显示指标：</span>
        <el-checkbox-group v-model="selectedIndicators">
          <el-checkbox value="pe" label="pe">市盈率(PE)</el-checkbox>
          <el-checkbox value="pb" label="pb">市净率(PB)</el-checkbox>
          <el-checkbox value="ps" label="ps">市销率(PS)</el-checkbox>
          <el-checkbox value="roe" label="roe">净资产收益率(ROE)</el-checkbox>
          <el-checkbox value="roa" label="roa">总资产收益率(ROA)</el-checkbox>
          <el-checkbox value="debtRatio" label="debtRatio">资产负债率</el-checkbox>
          <el-checkbox value="currentRatio" label="currentRatio">流动比率</el-checkbox>
          <el-checkbox value="dividendYield" label="dividendYield">股息率</el-checkbox>
          <el-checkbox value="beta" label="beta">Beta</el-checkbox>
        </el-checkbox-group>
      </div>

      <!-- 数据表格 -->
      <el-table :data="indicatorList" stripe style="width:100%" v-loading="loading" @row-click="showDetail">
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="stockCode" label="股票代码" width="120">
          <template #default="{ row }">
            <el-tag effect="plain" type="primary">{{ row.stockCode }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="股票名称" width="160">
          <template #default="{ row }">
            {{ getStockName(row.stockCode) }}
          </template>
        </el-table-column>

        <el-table-column v-if="selectedIndicators.includes('pe')" prop="pe" label="PE" width="100" sortable>
          <template #default="{ row }">{{ row.pe?.toFixed(1) }}</template>
        </el-table-column>
        <el-table-column v-if="selectedIndicators.includes('pb')" prop="pb" label="PB" width="100" sortable>
          <template #default="{ row }">{{ row.pb?.toFixed(1) }}</template>
        </el-table-column>
        <el-table-column v-if="selectedIndicators.includes('ps')" prop="ps" label="PS" width="100" sortable>
          <template #default="{ row }">{{ row.ps?.toFixed(1) }}</template>
        </el-table-column>
        <el-table-column v-if="selectedIndicators.includes('roe')" prop="roe" label="ROE" width="110" sortable>
          <template #default="{ row }">{{ (row.roe * 100)?.toFixed(2) }}%</template>
        </el-table-column>
        <el-table-column v-if="selectedIndicators.includes('roa')" prop="roa" label="ROA" width="110" sortable>
          <template #default="{ row }">{{ (row.roa * 100)?.toFixed(2) }}%</template>
        </el-table-column>
        <el-table-column v-if="selectedIndicators.includes('debtRatio')" prop="debtRatio" label="资产负债率" width="120" sortable>
          <template #default="{ row }">{{ (row.debtRatio * 100)?.toFixed(2) }}%</template>
        </el-table-column>
        <el-table-column v-if="selectedIndicators.includes('currentRatio')" prop="currentRatio" label="流动比率" width="110" sortable>
          <template #default="{ row }">{{ row.currentRatio?.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column v-if="selectedIndicators.includes('dividendYield')" prop="dividendYield" label="股息率" width="110" sortable>
          <template #default="{ row }">{{ (row.dividendYield * 100)?.toFixed(2) }}%</template>
        </el-table-column>
        <el-table-column v-if="selectedIndicators.includes('beta')" prop="beta" label="Beta" width="100" sortable>
          <template #default="{ row }">{{ row.beta?.toFixed(2) }}</template>
        </el-table-column>
      </el-table>

      <div style="margin-top:16px;display:flex;gap:12px">
        <el-button type="success" @click="exportCsv">
          <el-icon><Download /></el-icon> 导出CSV
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { ElMessage } from 'element-plus'
import { getIndicators, getStocks } from '@/api'
import { exportToCsv } from '@/utils/helpers'

const router = useRouter()
const store = useStore()

const indicatorList = ref([])
const allStocks = ref([])
const loading = ref(false)
const sectors = ['科技', '金融', '汽车', '医疗', '零售', '半导体', '电商']

const filters = reactive({
  industry: '',
  peMin: null,
  peMax: null,
  pbMin: null,
  pbMax: null,
  roeMin: null
})

const selectedIndicators = ref([...store.getters.getSelectedIndicators])

const getStockName = (code) => {
  const s = allStocks.value.find(st => st.code === code)
  return s ? s.name : code
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.peMin !== null) params.pe_gte = filters.peMin
    if (filters.peMax !== null) params.pe_lte = filters.peMax
    if (filters.pbMin !== null) params.pb_gte = filters.pbMin
    if (filters.pbMax !== null) params.pb_lte = filters.pbMax

    let data = await getIndicators(params)

    // 行业筛选（需要通过股票代码关联行业）
    if (filters.industry) {
      const industryCodes = allStocks.value
        .filter(s => s.industry === filters.industry)
        .map(s => s.code)
      data = data.filter(d => industryCodes.includes(d.stockCode))
    }

    // ROE筛选
    if (filters.roeMin !== null) {
      data = data.filter(d => (d.roe * 100) >= filters.roeMin)
    }

    indicatorList.value = data
  } catch (e) {
    ElMessage.error('获取指标数据失败')
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.industry = ''
  filters.peMin = null
  filters.peMax = null
  filters.pbMin = null
  filters.pbMax = null
  filters.roeMin = null
  fetchData()
}

const showDetail = (row) => {
  router.push(`/stock/${row.stockCode}`)
}

const exportCsv = () => {
  const headers = [
    { key: 'stockCode', label: '股票代码' },
    { key: 'stockName', label: '股票名称' }
  ]
  if (selectedIndicators.value.includes('pe')) headers.push({ key: 'pe', label: '市盈率(PE)' })
  if (selectedIndicators.value.includes('pb')) headers.push({ key: 'pb', label: '市净率(PB)' })
  if (selectedIndicators.value.includes('ps')) headers.push({ key: 'ps', label: '市销率(PS)' })
  if (selectedIndicators.value.includes('roe')) headers.push({ key: 'roe', label: 'ROE' })
  if (selectedIndicators.value.includes('roa')) headers.push({ key: 'roa', label: 'ROA' })
  if (selectedIndicators.value.includes('debtRatio')) headers.push({ key: 'debtRatio', label: '资产负债率' })
  if (selectedIndicators.value.includes('currentRatio')) headers.push({ key: 'currentRatio', label: '流动比率' })
  if (selectedIndicators.value.includes('dividendYield')) headers.push({ key: 'dividendYield', label: '股息率' })
  if (selectedIndicators.value.includes('beta')) headers.push({ key: 'beta', label: 'Beta' })

  const exportData = indicatorList.value.map(d => {
    const name = getStockName(d.stockCode)
    return { ...d, stockName: name }
  })

  exportToCsv(exportData, headers, `indicators_${new Date().toISOString().slice(0,10)}.csv`)
  ElMessage.success('指标数据导出成功')
}

onMounted(async () => {
  try {
    allStocks.value = await getStocks()
  } catch (e) { /* ignore */ }
  fetchData()
})
</script>

<style scoped>
.filter-form {
  padding: 16px;
  background: #fafafa;
  border-radius: 6px;
  margin-bottom: 16px;
}
</style>
