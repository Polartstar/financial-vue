<template>
  <div class="stock-list-page">
    <div class="page-card">
      <div class="card-title">
        <el-icon :size="20"><DataBoard /></el-icon>
        实时行情列表
        <el-tag type="success" effect="dark" style="margin-left:12px">共 {{ total }} 只股票</el-tag>
      </div>

<!-- v-model双绑searchForm，填啥有啥 -->
      <!-- 搜索筛选区 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="行业">
          <el-select v-model="searchForm.industry" placeholder="全部行业" clearable style="width:140px">
            <el-option v-for="s in sectors" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="最低价">
          <el-input-number v-model="searchForm.minPrice" :min="0" :step="10" placeholder="最低" style="width:120px" />
        </el-form-item>
        <el-form-item label="最高价">
          <el-input-number v-model="searchForm.maxPrice" :min="0" :step="10" placeholder="最高" style="width:120px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchData">
            <el-icon><Search /></el-icon> 搜索
          </el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 数据表格 -->
      <el-table
        :data="stocks"
        stripe
        style="width:100%"
        v-loading="loading"
        @row-click="goToDetail"
        highlight-current-row
      >
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="code" label="代码" width="100">
          <template #default="{ row }">
            <el-tag type="primary" effect="plain">{{ row.code }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="名称" min-width="180" />
        <el-table-column prop="exchange" label="交易所" width="100" />
        <el-table-column prop="industry" label="行业" width="100">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.industry }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="price" label="最新价(USD)" width="130" sortable>
          
          <template #default="{ row }">
            <span style="font-weight:600;font-size:15px">${{ row.price.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="change" label="涨跌额" width="120" sortable>
          <template #default="{ row }">
            <span :style="{ color: row.change >= 0 ? '#67c23a' : '#f56c6c', fontWeight:600 }">
              {{ formatChange(row.change) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="changePercent" label="涨跌幅(%)" width="130" sortable>
          <template #default="{ row }">
            <span :style="{ color: row.changePercent >= 0 ? '#67c23a' : '#f56c6c', fontWeight:600 }">
              {{ formatChange(row.changePercent) }}%
            </span>
            <el-icon v-if="row.changePercent >= 0" color="#67c23a"><Top /></el-icon>
            <el-icon v-else color="#f56c6c"><Bottom /></el-icon>
          </template>
        </el-table-column>
        <el-table-column prop="volume" label="成交量" width="140" sortable>
          <template #default="{ row }">
            {{ formatMoney(row.volume) }}
          </template>
        </el-table-column>
        <el-table-column prop="marketCap" label="市值" width="120" />
        <el-table-column label="操作" width="160" fixed="right">
         
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click.stop="$router.push(`/kline/${row.code}`)">
              K线
            </el-button>
            <el-button text type="primary" size="small" @click.stop="$router.push(`/financial/${row.code}`)">
              财报
            </el-button>
            <!-- 动态绑定颜色，图标 -->
            <el-button
              :type="isFav(row.code) ? 'warning' : 'default'"
              :icon="isFav(row.code) ? 'StarFilled' : 'Star'"
              text
              size="small"
              @click.stop="toggleFavorite(row)"
            />
<!-- .stop事件修饰符， event.stopPropagation()阻止点击跳转详情页-->
          </template>
        </el-table-column>
      </el-table>

      <!-- 导出按钮 -->
      <div style="margin-top:16px;display:flex;justify-content:space-between;align-items:center">
        <el-button type="success" @click="exportCsv">
          <el-icon><Download /></el-icon> 导出CSV
        </el-button>
        <span style="color:#909399;font-size:13px">点击行可查看股票详情</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { ElMessage } from 'element-plus'
import { getStocks } from '@/api'
import { exportToCsv, formatMoney, formatChange } from '@/utils/helpers'

const router = useRouter()
const store = useStore()

// 响应式数据，ref 包装基本/数组类型
const stocks = ref([])
const total = ref(0)
const loading = ref(false)

const sectors = ['科技', '金融', '汽车', '医疗', '零售', '半导体', '电商']

// reactive 包装对象，直接驱动模板更新
const searchForm = reactive({
  industry: '',
  minPrice: null,
  maxPrice: null
})

// 检查是否已经自选
const isFav = (code) => store.getters.isInWatchlist(code)

const fetchData = async () => {
  loading.value = true
  try {
    const params = {}
    if (searchForm.industry) params.industry = searchForm.industry
    if (searchForm.minPrice !== null) params.price_gte = searchForm.minPrice
    if (searchForm.maxPrice !== null) params.price_lte = searchForm.maxPrice
    
    stocks.value = await getStocks(params)
    total.value = stocks.value.length
  } catch (e) {
    ElMessage.error('获取行情数据失败')
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  searchForm.industry = ''
  searchForm.minPrice = null
  searchForm.maxPrice = null
  fetchData()
}

const goToDetail = (row) => {
  router.push(`/stock/${row.code}`)
}

// 异步函数，async 关键字可内部使用 await，等待传参
const toggleFavorite = async (row) => {
  if (isFav(row.code)) {
    await store.dispatch('removeFromWatchlist', row.code)
    ElMessage.success(`已移除 ${row.code}`)
  } else {
    await store.dispatch('addToWatchlist', { stockCode: row.code, note: row.name })
    ElMessage.success(`已添加 ${row.code} 到自选股`)
  }
}

const exportCsv = () => {
  // 导出的数据先应用格式化，让 CSV 里也是可读的格式
  const formattedData = stocks.value.map(s => ({
    code: s.code,
    name: s.name,
    exchange: s.exchange,
    industry: s.industry,
    price: s.price.toFixed(2),
    change: formatChange(s.change),
    changePercent: formatChange(s.changePercent),
    volume: formatMoney(s.volume),
    marketCap: s.marketCap
  }))
  const headers = [
    { key: 'code', label: '股票代码' },
    { key: 'name', label: '股票名称' },
    { key: 'exchange', label: '交易所' },
    { key: 'industry', label: '行业' },
    { key: 'price', label: '最新价(USD)' },
    { key: 'change', label: '涨跌额' },
    { key: 'changePercent', label: '涨跌幅(%)' },
    { key: 'volume', label: '成交量' },
    { key: 'marketCap', label: '市值' }
  ]
  exportToCsv(formattedData, headers, `stocks_${new Date().toISOString().slice(0,10)}.csv`)
  ElMessage.success('数据导出成功')
}

onMounted(fetchData)
</script>

<style scoped>
.search-form {
  padding: 16px;
  background: #fafafa;
  border-radius: 6px;
  margin-bottom: 16px;
}
</style>
