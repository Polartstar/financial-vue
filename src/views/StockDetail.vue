<template>
  <div class="stock-detail-page">
    <div v-if="loading" style="text-align:center;padding:60px">
      <el-icon class="is-loading" :size="32"><Loading /></el-icon>
      <p style="margin-top:12px;color:#909399">加载中...</p>
    </div>
    <template v-else-if="stock">
      <!-- 股票信息头 -->
      <div class="page-card stock-header">
        <div class="header-left">
          <el-tag type="primary" size="large" effect="dark" style="font-size:16px;padding:6px 16px">
            {{ stock.code }}
          </el-tag>
          <span class="stock-name">{{ stock.name }}</span>
          <el-tag effect="plain" size="small">{{ stock.exchange }}</el-tag>
          <el-tag effect="plain" size="small" type="warning">{{ stock.industry }}</el-tag>
        </div>
        <div class="header-price">
          <span class="price">${{ stock.price.toFixed(2) }}</span>
          <span class="change" :style="{ color: stock.changePercent >= 0 ? '#67c23a' : '#f56c6c' }">
            {{ stock.change >= 0 ? '+' : '' }}{{ stock.change.toFixed(2) }}
            ({{ stock.changePercent >= 0 ? '+' : '' }}{{ stock.changePercent.toFixed(2) }}%)
          </span>
        </div>
        <div class="header-actions">
          <el-button type="primary" @click="$router.push(`/kline/${stock.code}`)">
            <el-icon><TrendCharts /></el-icon> K线图
          </el-button>
          <el-button @click="$router.push(`/financial/${stock.code}`)">
            <el-icon><Document /></el-icon> 财务报表
          </el-button>
          <el-button
            :type="isFav ? 'warning' : 'default'"
            @click="toggleFav"
          >
            <el-icon><StarFilled /></el-icon>
            {{ isFav ? '已自选' : '加入自选' }}
          </el-button>
        </div>
      </div>

      <!-- 基本信息 -->
      <el-row :gutter="20">
        <el-col :span="8">
          <div class="page-card">
            <div class="card-title"><el-icon :size="18"><InfoFilled /></el-icon> 交易信息</div>
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="开盘价">${{ stock.open.toFixed(2) }}</el-descriptions-item>
              <el-descriptions-item label="最高价">${{ stock.high.toFixed(2) }}</el-descriptions-item>
              <el-descriptions-item label="最低价">${{ stock.low.toFixed(2) }}</el-descriptions-item>
              <el-descriptions-item label="成交量">{{ formatMoney(stock.volume) }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="page-card">
            <div class="card-title"><el-icon :size="18"><Coin /></el-icon> 财务指标</div>
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="市值">{{ stock.marketCap }}</el-descriptions-item>
              <el-descriptions-item label="市盈率(PE)">{{ stock.pe }}</el-descriptions-item>
              <el-descriptions-item label="市净率(PB)">{{ stock.pb }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="page-card">
            <div class="card-title"><el-icon :size="18"><Link /></el-icon> 快捷操作</div>
            <el-space direction="vertical" style="width:100%">
              <el-button style="width:100%" @click="addToCompare">
                <el-icon><Opportunity /></el-icon> 加入对比
              </el-button>
              <el-button style="width:100%" @click="showIndicatorDialog">
                <el-icon><Coin /></el-icon> 查看详细指标
              </el-button>
            </el-space>
          </div>
        </el-col>
      </el-row>
    </template>
    <el-empty v-else description="未找到该股票" />

    <!-- 指标详情对话框 -->
    <el-dialog v-model="indicatorVisible" :title="`${stock?.code} 详细指标`" width="600px">
      <el-descriptions v-if="indicatorData" :column="2" border>
        <el-descriptions-item label="市盈率(PE)">{{ indicatorData.pe }}</el-descriptions-item>
        <el-descriptions-item label="市净率(PB)">{{ indicatorData.pb }}</el-descriptions-item>
        <el-descriptions-item label="市销率(PS)">{{ indicatorData.ps }}</el-descriptions-item>
        <el-descriptions-item label="净资产收益率(ROE)">{{ (indicatorData.roe * 100).toFixed(2) }}%</el-descriptions-item>
        <el-descriptions-item label="总资产收益率(ROA)">{{ (indicatorData.roa * 100).toFixed(2) }}%</el-descriptions-item>
        <el-descriptions-item label="资产负债率">{{ (indicatorData.debtRatio * 100).toFixed(2) }}%</el-descriptions-item>
        <el-descriptions-item label="流动比率">{{ indicatorData.currentRatio }}</el-descriptions-item>
        <el-descriptions-item label="股息率">{{ (indicatorData.dividendYield * 100).toFixed(2) }}%</el-descriptions-item>
        <el-descriptions-item label="Beta系数">{{ indicatorData.beta }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
// 引入computed 计算属性
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useStore } from 'vuex'
import { ElMessage } from 'element-plus'
import { getStockByCode, getIndicatorByStock } from '@/api'
import { formatMoney, formatPercent, formatChange } from '@/utils/helpers'

const props = defineProps({ code: String })
const route = useRoute()
const store = useStore()

//计算属性依赖 route 对象，route.params只会在语法糖组件创建时执行一次
const stockCode = computed(() => props.code || route.params.code)
const stock = ref(null)
const loading = ref(true)
const indicatorData = ref(null)
const indicatorVisible = ref(false)

//getter分装在store中，检查当前股票代码是否存在于 Vuex 的自选股列表中，返回 true/false
const isFav = computed(() => store.getters.isInWatchlist(stockCode.value))

const toggleFav = async () => {
  if (isFav.value) {
    await store.dispatch('removeFromWatchlist', stockCode.value)
    ElMessage.success('已取消自选')
  } else {
    await store.dispatch('addToWatchlist', { stockCode: stockCode.value, note: stock.value?.name })
    ElMessage.success('已加入自选股')
  }
}

const addToCompare = () => {
  store.commit('ADD_TO_COMPARE', stockCode.value)
  ElMessage.success(`${stockCode.value} 已加入对比列表`)
}

const showIndicatorDialog = async () => {
  try {
    const res = await getIndicatorByStock(stockCode.value)
    indicatorData.value = res[0] || null
    indicatorVisible.value = true
  } catch (e) {
    ElMessage.error('获取指标数据失败')
  }
}

onMounted(async () => {
  try {
    const res = await getStockByCode(stockCode.value)
    stock.value = res[0] || null
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.stock-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stock-name {
  font-size: 22px;
  font-weight: 600;
}

.header-price {
  text-align: center;
}

.price {
  font-size: 32px;
  font-weight: 700;
  color: #303133;
  display: block;
}

.change {
  font-size: 16px;
  font-weight: 500;
}
</style>
