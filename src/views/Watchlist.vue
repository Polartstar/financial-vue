<template>
  <div class="watchlist-page">
    <div class="page-card">
      <div class="card-title">
        <el-icon :size="20"><StarFilled /></el-icon>
        我的自选股
        <el-tag type="warning" effect="dark" style="margin-left:12px">共 {{ watchlist.length }} 只</el-tag>
      </div>

      <el-alert
        v-if="watchlist.length === 0"
        title="您还没有添加自选股"
        description="前往行情列表点击星标按钮添加自选股，或点击下方按钮快速添加"
        type="info"
        show-icon
        :closable="false"
        style="margin-bottom:16px"
      />

      <!-- 自选股表格 -->
      <el-table
        v-if="watchlist.length > 0"
        :data="watchlistWithDetails"
        stripe
        style="width:100%"
        v-loading="loading"
        @row-click="goToDetail"
      >
        <el-table-column prop="stockCode" label="代码" width="100">
          <template #default="{ row }">
            <el-tag type="warning" effect="plain">{{ row.stockCode }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="detail?.name" label="名称" min-width="180" />
        <el-table-column prop="detail?.price" label="最新价" width="120">
          <template #default="{ row }">
            <span v-if="row.detail" style="font-weight:600">${{ row.detail.price.toFixed(2) }}</span>
            <span v-else class="no-data">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="detail?.changePercent" label="涨跌幅" width="130">
          <template #default="{ row }">
            <span v-if="row.detail" :style="{ color: row.detail.changePercent >= 0 ? '#67c23a' : '#f56c6c', fontWeight:600 }">
              {{ row.detail.changePercent >= 0 ? '+' : '' }}{{ row.detail.changePercent.toFixed(2) }}%
            </span>
            <span v-else class="no-data">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="detail?.industry" label="行业" width="100" />
        <el-table-column prop="addedAt" label="添加时间" width="180">
          <template #default="{ row }">
            {{ new Date(row.addedAt).toLocaleString('zh-CN') }}
          </template>
        </el-table-column>
        <el-table-column prop="note" label="备注" min-width="160" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click.stop="$router.push(`/kline/${row.stockCode}`)">
              K线
            </el-button>
            <el-button text type="primary" size="small" @click.stop="$router.push(`/financial/${row.stockCode}`)">
              财报
            </el-button>
            <el-button text type="danger" size="small" @click.stop="confirmRemove(row)">
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 快速添加区域 -->
      <div class="add-section" style="margin-top:20px">
        <span style="font-weight:600;margin-right:12px">快速添加：</span>
        <el-select v-model="newStockCode" filterable placeholder="选择股票" style="width:200px">
          <el-option v-for="s in availableStocks" :key="s.code" :label="`${s.code} ${s.name}`" :value="s.code" />
        </el-select>
        <el-input v-model="newNote" placeholder="备注（可选）" style="width:200px;margin:0 8px" />
        <el-button type="primary" @click="addStock">
          <el-icon><Plus /></el-icon> 添加
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getStocks, getStockByCode } from '@/api'

const router = useRouter()
const store = useStore()

const loading = ref(false)
const newStockCode = ref('')
const newNote = ref('')
const allStocks = ref([])

// 从Vuex获取自选股列表
const watchlist = computed(() => store.state.watchlist)

// 自选股详情（补充完整的股票信息）
const watchlistWithDetails = ref([])

// 可选的自选股（未添加的）
const availableStocks = computed(() => {
  const codes = watchlist.value.map(w => w.stockCode)
  return allStocks.value.filter(s => !codes.includes(s.code))
})

const loadWatchlistDetails = async () => {
  loading.value = true
  try {
    const details = []
    for (const item of watchlist.value) {
      const res = await getStockByCode(item.stockCode)
      const detail = res[0] || null
      details.push({ ...item, detail })
    }
    watchlistWithDetails.value = details
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const confirmRemove = async (row) => {
  try {
    await ElMessageBox.confirm(`确定将 ${row.stockCode} 移出自选股吗？`, '确认删除', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消'
    })
    await store.dispatch('removeFromWatchlist', row.stockCode)
    ElMessage.success(`已移除 ${row.stockCode}`)
    loadWatchlistDetails()
  } catch { /* 取消 */ }
}

const addStock = async () => {
  if (!newStockCode.value) {
    ElMessage.warning('请选择股票')
    return
  }
  await store.dispatch('addToWatchlist', {
    stockCode: newStockCode.value,
    note: newNote.value
  })
  ElMessage.success(`已添加 ${newStockCode.value}`)
  newStockCode.value = ''
  newNote.value = ''
  loadWatchlistDetails()
}

const goToDetail = (row) => {
  router.push(`/stock/${row.stockCode}`)
}

onMounted(async () => {
  try {
    allStocks.value = await getStocks()
  } catch (e) { /* ignore */ }
  store.dispatch('fetchWatchlist').then(loadWatchlistDetails)
})
</script>

<style scoped>
.add-section {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
}

.no-data {
  color: #c0c4cc;
}
</style>
