<template>
  <div class="home-page">
    <!-- 欢迎横幅 -->
    <div class="welcome-banner page-card">
      <div class="banner-content">
        <h1>
          <el-icon :size="32" color="#409eff"><TrendCharts /></el-icon>
          金融数据分析平台
        </h1>
        <p>基于 Vue 3 + Element Plus + ECharts 构建的交互式金融数据分析工具</p>
        <div class="banner-stats">
          <el-statistic title="可查询股票" :value="12" suffix="只" />
          <el-statistic title="行业覆盖" :value="7" suffix="个" />
          <el-statistic title="数据端点" :value="6" suffix="个" />
        </div>
        <div class="banner-actions">
          <el-button type="primary" size="large" @click="$router.push('/stocks')">
            <el-icon><DataBoard /></el-icon> 查看行情
          </el-button>
          <el-button size="large" @click="$router.push('/indicators')">
            <el-icon><Coin /></el-icon> 筛选指标
          </el-button>
        </div>
      </div>
    </div>

    <!-- 功能概览 -->
    <div class="page-card">
      <div class="card-title">
        <el-icon :size="20"><Menu /></el-icon>
        功能模块
      </div>
      <el-row :gutter="20">
        <el-col :span="8" v-for="mod in modules" :key="mod.title">
          <el-card shadow="hover" class="module-card" @click="$router.push(mod.route)">
            <el-icon :size="36" :color="mod.color">{{ mod.iconComp }}</el-icon>
            <h3>{{ mod.title }}</h3>
            <p>{{ mod.desc }}</p>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 热门股票行情概览 -->
    <div class="page-card">
      <div class="card-title">
        <el-icon :size="20"><DataBoard /></el-icon>
        热门股票行情概览
      </div>
      <el-table :data="hotStocks" stripe style="width:100%" v-loading="loading" @row-click="goToDetail">
        <el-table-column prop="code" label="代码" width="100" />
        <el-table-column prop="name" label="名称" min-width="160" />
        <el-table-column prop="price" label="最新价" width="120">
          <template #default="{ row }">
            <span style="font-weight:600">${{ row.price.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="changePercent" label="涨跌幅" width="120">
          <template #default="{ row }">
            <span :style="{ color: row.changePercent >= 0 ? '#67c23a' : '#f56c6c', fontWeight:600 }">
              {{ row.changePercent >= 0 ? '+' : '' }}{{ row.changePercent.toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="volume" label="成交量" width="140">
          <template #default="{ row }">
            {{ (row.volume / 10000).toFixed(0) }}万
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click.stop="$router.push(`/stock/${row.code}`)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 快速操作 -->
    <div class="page-card">
      <div class="card-title">
        <el-icon :size="20"><Connection /></el-icon>
        快速跳转
      </div>
      <el-space wrap>
        <el-button @click="$router.push('/stocks')">
          <el-icon><DataBoard /></el-icon> 完整行情列表
        </el-button>
        <el-button @click="$router.push('/watchlist')">
          <el-icon><StarFilled /></el-icon> 我的自选股
        </el-button>
        <el-button @click="$router.push('/compare')">
          <el-icon><Opportunity /></el-icon> 个股对比
        </el-button>
        <el-button @click="$router.push('/indicators')">
          <el-icon><Coin /></el-icon> 指标筛选
        </el-button>
        <el-button @click="$router.push('/about')">
          <el-icon><InfoFilled /></el-icon> 帮助文档
        </el-button>
      </el-space>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getStocks } from '@/api'

const router = useRouter()
// 首页热门股票列表
const hotStocks = ref([])
const loading = ref(false)

const modules = [
  { title: '行情列表', desc: '查看所有股票实时行情数据，支持排序与筛选', route: '/stocks', color: '#409eff', iconComp: 'DataBoard' },
  { title: 'K线图分析', desc: '交互式K线图表，支持多周期切换与技术分析', route: '/kline/AAPL', color: '#67c23a', iconComp: 'TrendCharts' },
  { title: '财务报表', desc: '利润表、资产负债表等财务数据一览', route: '/financial/AAPL', color: '#e6a23c', iconComp: 'Document' },
  { title: '指标筛选对比', desc: '市盈率、市净率等多维度指标筛选与对比', route: '/indicators', color: '#f56c6c', iconComp: 'Coin' },
  { title: '自选股管理', desc: '管理个人自选股票池，一键关注', route: '/watchlist', color: '#909399', iconComp: 'StarFilled' },
  { title: '个股对比', desc: '多只股票同框对比，辅助投资决策', route: '/compare', color: '#b37feb', iconComp: 'Opportunity' }
]

const goToDetail = (row) => {
  router.push(`/stock/${row.code}`)
}

onMounted(async () => {
  loading.value = true
  try {
    hotStocks.value = await getStocks({ _limit: 6 })
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.welcome-banner {
  background: linear-gradient(135deg, #1a73e8 0%, #409eff 50%, #66b1ff 100%);
  color: #fff;
  padding: 40px;
}

.banner-content h1 {
  font-size: 28px;
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.banner-content p {
  font-size: 15px;
  opacity: 0.9;
  margin-bottom: 24px;
}

.banner-stats {
  display: flex;
  gap: 40px;
  margin-bottom: 24px;
}

.banner-stats :deep(.el-statistic__head) {
  color: rgba(255,255,255,0.8);
}

.banner-stats :deep(.el-statistic__content) {
  color: #fff;
  font-size: 28px;
}

.banner-actions {
  display: flex;
  gap: 12px;
}

.banner-actions .el-button--default {
  color: #409eff;
  border-color: #fff;
  background: #fff;
}

.module-card {
  cursor: pointer;
  text-align: center;
  padding: 16px 0;
  transition: transform 0.2s;
}

.module-card:hover {
  transform: translateY(-4px);
}

.module-card h3 {
  margin: 12px 0 8px;
  font-size: 16px;
}

.module-card p {
  font-size: 13px;
  color: #909399;
  line-height: 1.5;
}
</style>
