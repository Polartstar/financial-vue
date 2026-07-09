import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue')
  },
  {
    path: '/stocks',
    name: 'StockList',
    component: () => import('@/views/StockList.vue')
  },
  {
    // 带params的路径：股票详情页
    path: '/stock/:code',
    name: 'StockDetail',
    component: () => import('@/views/StockDetail.vue'),
    props: true
  },
  {
    // 带params的路径：K线图（使用query参数控制周期）
    path: '/kline/:code',
    name: 'KLineDetail',
    component: () => import('@/views/KLineDetail.vue'),
    props: true
    // 路由参数会以 prop 形式传入
  },
  {
    // 带params的路径：财务报表
    path: '/financial/:code',
    name: 'FinancialReport',
    component: () => import('@/views/FinancialReport.vue'),
    props: true
  },
  {
    path: '/watchlist',
    name: 'Watchlist',
    component: () => import('@/views/Watchlist.vue')
  },
  {
    // 带query参数的路径：个股对比
    path: '/compare',
    name: 'StockCompare',
    component: () => import('@/views/StockCompare.vue')
  },
  {
    path: '/indicators',
    name: 'IndicatorCompare',
    component: () => import('@/views/IndicatorCompare.vue')
  },
  {
    // 带params的路径：对比结果页，ids用逗号分隔
    path: '/compare/:ids',
    name: 'CompareResult',
    component: () => import('@/views/CompareResult.vue'),
    props: true
  },
  {
    path: '/about',
    name: 'About',
    component: () => import('@/views/About.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
