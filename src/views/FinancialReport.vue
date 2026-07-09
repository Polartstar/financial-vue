<template>
  <div class="financial-page">
    <div class="page-card">
      <div class="card-title">
        <el-icon :size="20"><Document /></el-icon>
        财务报表数据
      </div>

      <!-- 股票选择 -->
      <div style="margin-bottom:16px;display:flex;gap:12px;align-items:center;flex-wrap:wrap">
        <el-select v-model="selectedStock" filterable style="width:200px" @change="fetchData">
          <el-option v-for="s in stockOptions" :key="s.code" :label="`${s.code} ${s.name}`" :value="s.code" />
        </el-select>
        <el-tag v-if="stockInfo" type="primary" effect="dark">
          {{ stockInfo.code }} {{ stockInfo.name }}
        </el-tag>
      </div>

      <!-- 利润表 -->
      <el-tabs v-model="activeTab" type="border-card">
        <el-tab-pane label="利润表" name="income">
          <div class="table-scroll-wrap">
          <el-table :data="financialData" stripe style="width:100%" v-loading="loading">
            <el-table-column prop="year" label="年份" width="100" />
            <el-table-column prop="quarter" label="季度" width="80" />
            <el-table-column label="营业收入" width="150">
              <template #default="{ row }">{{ formatMoney(row.revenue) }}</template>
            </el-table-column>
            <el-table-column label="营业成本" width="150">
              <template #default="{ row }">{{ formatMoney(row.costOfRevenue) }}</template>
            </el-table-column>
            <el-table-column label="毛利润" width="150">
              <template #default="{ row }">{{ formatMoney(row.grossProfit) }}</template>
            </el-table-column>
            <el-table-column label="营业利润" width="150">
              <template #default="{ row }">{{ formatMoney(row.operatingIncome) }}</template>
            </el-table-column>
            <el-table-column label="净利润" width="150">
              <template #default="{ row }">
                <span style="font-weight:600;color:#303133">{{ formatMoney(row.netIncome) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="每股收益(EPS)" width="140">
              <template #default="{ row }">${{ row.eps }}</template>
            </el-table-column>
          </el-table>
          </div>
        </el-tab-pane>

        <el-tab-pane label="资产负债表" name="balance">
          <div class="table-scroll-wrap">
          <el-table :data="financialData" stripe style="width:100%" v-loading="loading">
            <el-table-column prop="year" label="年份" width="100" />
            <el-table-column prop="quarter" label="季度" width="80" />
            <el-table-column label="总资产" width="180">
              <template #default="{ row }">{{ formatMoney(row.totalAssets) }}</template>
            </el-table-column>
            <el-table-column label="总负债" width="180">
              <template #default="{ row }">{{ formatMoney(row.totalLiabilities) }}</template>
            </el-table-column>
            <el-table-column label="股东权益" width="180">
              <template #default="{ row }">{{ formatMoney(row.totalEquity) }}</template>
            </el-table-column>
            <el-table-column label="现金流" width="180">
              <template #default="{ row }">{{ formatMoney(row.cashFlow) }}</template>
            </el-table-column>
          </el-table>
          </div>
        </el-tab-pane>

        <el-tab-pane label="财务比率" name="ratios">
          <div class="table-scroll-wrap">
          <el-table :data="financialData" stripe style="width:100%" v-loading="loading">
            <el-table-column prop="year" label="年份" width="100" />
            <el-table-column prop="quarter" label="季度" width="80" />
            <el-table-column label="毛利率" width="130">
              <template #default="{ row }">
                {{ row.revenue ? ((row.grossProfit / row.revenue) * 100).toFixed(2) + '%' : '-' }}
              </template>
            </el-table-column>
            <el-table-column label="净利率" width="130">
              <template #default="{ row }">
                {{ row.revenue ? ((row.netIncome / row.revenue) * 100).toFixed(2) + '%' : '-' }}
              </template>
            </el-table-column>
            <el-table-column label="营业利润率" width="130">
              <template #default="{ row }">
                {{ row.revenue ? ((row.operatingIncome / row.revenue) * 100).toFixed(2) + '%' : '-' }}
              </template>
            </el-table-column>
            <el-table-column label="资产负债率" width="130">
              <template #default="{ row }">
                {{ row.totalAssets ? ((row.totalLiabilities / row.totalAssets) * 100).toFixed(2) + '%' : '-' }}
              </template>
            </el-table-column>
            <el-table-column label="EPS" width="130">
              <template #default="{ row }">${{ row.eps }}</template>
            </el-table-column>
          </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>

      <div style="margin-top:16px">
        <el-button type="success" @click="exportCsv">
          <el-icon><Download /></el-icon> 导出当前数据CSV
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getFinancialData, getStocks, getStockByCode } from '@/api'
import { exportToCsv, formatMoney } from '@/utils/helpers'

const props = defineProps({ code: String })
const route = useRoute()

const selectedStock = ref(props.code || route.params.code || 'AAPL')
const financialData = ref([])
const stockOptions = ref([])
const stockInfo = ref(null)
const loading = ref(false)
const activeTab = ref('income')

const fetchData = async () => {
  loading.value = true
  try {
    // 获取股票信息
    const info = await getStockByCode(selectedStock.value)
    stockInfo.value = info[0] || null
    // 获取财务数据
    financialData.value = await getFinancialData(selectedStock.value)
  } catch (e) {
    ElMessage.error('获取财务数据失败')
  } finally {
    loading.value = false
  }
}

const exportCsv = () => {
  // 导出前先应用格式化，让 CSV 里的金额带单位
  const formattedData = financialData.value.map(d => ({
    year: d.year,
    quarter: d.quarter,
    revenue: formatMoney(d.revenue),
    costOfRevenue: formatMoney(d.costOfRevenue),
    grossProfit: formatMoney(d.grossProfit),
    operatingIncome: formatMoney(d.operatingIncome),
    netIncome: formatMoney(d.netIncome),
    eps: d.eps,
    totalAssets: formatMoney(d.totalAssets),
    totalLiabilities: formatMoney(d.totalLiabilities),
    totalEquity: formatMoney(d.totalEquity),
    cashFlow: formatMoney(d.cashFlow)
  }))
  const headers = [
    { key: 'year', label: '年份' },
    { key: 'quarter', label: '季度' },
    { key: 'revenue', label: '营业收入' },
    { key: 'grossProfit', label: '毛利润' },
    { key: 'operatingIncome', label: '营业利润' },
    { key: 'netIncome', label: '净利润' },
    { key: 'eps', label: '每股收益(EPS)' },
    { key: 'totalAssets', label: '总资产' },
    { key: 'totalEquity', label: '股东权益' },
    { key: 'cashFlow', label: '现金流' }
  ]
  exportToCsv(formattedData, headers, `financial_${selectedStock.value}_${new Date().toISOString().slice(0,10)}.csv`)
  ElMessage.success('财报数据导出成功')
}

onMounted(async () => {
  try {
    stockOptions.value = await getStocks()
  } catch (e) { /* ignore */ }
  fetchData()
})
</script>

<style scoped>
.table-scroll-wrap {
  overflow-x: auto;
}
.table-scroll-wrap :deep(.el-table) {
  min-width: 820px;
}
</style>
