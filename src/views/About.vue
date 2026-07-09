<template>
  <div class="about-page">
    <!-- 项目介绍 -->
    <div class="page-card">
      <div class="card-title">
        <el-icon :size="20"><InfoFilled /></el-icon>
        关于本系统
      </div>
      <el-descriptions title="Vue.js在金融数据分析中的应用" :column="1" border>
        <el-descriptions-item label="项目名称">金融数据分析平台 (Financial Data Analysis Platform)</el-descriptions-item>
        <el-descriptions-item label="技术栈">
          <el-tag style="margin-right:4px">Vue 3</el-tag>
          <el-tag style="margin-right:4px" type="success">Composition API</el-tag>
          <el-tag style="margin-right:4px" type="warning">Vue Router</el-tag>
          <el-tag style="margin-right:4px" type="danger">Vuex</el-tag>
          <el-tag style="margin-right:4px" type="info">Axios</el-tag>
          <el-tag style="margin-right:4px">Element Plus</el-tag>
          <el-tag type="success">ECharts</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="后端模拟">json-server RESTful API (端口 3000)</el-descriptions-item>
        <el-descriptions-item label="运行方式">npm install && npm run dev (前后端同时启动)</el-descriptions-item>
        <el-descriptions-item label="开发目的">Vue.js 前端交互大作业</el-descriptions-item>
      </el-descriptions>
    </div>

    <!-- 功能介绍 -->
    <div class="page-card">
      <div class="card-title">
        <el-icon :size="20"><Menu /></el-icon>
        功能模块说明
      </div>
      <el-collapse accordion>
        <el-collapse-item title="📊 行情列表" name="1">
          <p>展示所有股票的实时行情数据，包括股票代码、名称、最新价、涨跌幅、成交量等。</p>
          <p>支持按行业、价格区间筛选，点击行可进入股票详情。支持CSV数据导出。</p>
        </el-collapse-item>
        <el-collapse-item title="📈 K线图分析" name="2">
          <p>使用 ECharts 渲染交互式日K线图，支持10/20/30日周期切换。</p>
          <p>包含成交量柱状图、均价线、拖拽缩放等交互功能。支持K线数据明细展示与导出。</p>
        </el-collapse-item>
        <el-collapse-item title="📋 财务报表" name="3">
          <p>查看上市公司财务报表数据，包含利润表、资产负债表、财务比率三个维度。</p>
          <p>支持按年份查看营业收入、净利润、总资产、EPS等核心财务指标。</p>
        </el-collapse-item>
        <el-collapse-item title="🔍 指标筛选对比" name="4">
          <p>多维度财务指标筛选：市盈率(PE)、市净率(PB)、ROE等。</p>
          <p>支持自定义指标展示列，按行业筛选，排序与CSV导出。</p>
        </el-collapse-item>
        <el-collapse-item title="⭐ 自选股管理" name="5">
          <p>个人自选股票池管理，支持添加/删除自选股，记录添加时间和备注。</p>
          <p>自选股数据存储在 Vuex 中并与 json-server 同步。</p>
        </el-collapse-item>
        <el-collapse-item title="🔄 个股对比" name="6">
          <p>选择2~4只股票进行横向对比，表格展示价格、涨跌幅、市值、PE/PB等。</p>
          <p>支持雷达图可视化展示多只股票的多维指标对比。</p>
        </el-collapse-item>
        <el-collapse-item title="💾 数据导出" name="7">
          <p>所有数据表格均支持一键导出为CSV格式，使用 Blob 下载。</p>
          <p>导出的CSV文件包含 UTF-8 BOM 头，可直接用 Excel 打开。</p>
        </el-collapse-item>
      </el-collapse>
    </div>

    <!-- 路由说明 -->
    <div class="page-card">
      <div class="card-title">
        <el-icon :size="20"><Connection /></el-icon>
        路由结构说明（共10个路由）
      </div>
      <el-table :data="routeTable" stripe border style="width:100%">
        <el-table-column prop="path" label="路由路径" width="220">
          <template #default="{ row }">
            <code>{{ row.path }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="路由名称" width="150" />
        <el-table-column prop="page" label="页面" width="200" />
        <el-table-column prop="params" label="路由参数说明" min-width="280" />
      </el-table>
    </div>

    <!-- 技术要点 -->
    <div class="page-card">
      <div class="card-title">
        <el-icon :size="20"><Trophy /></el-icon>
        技术实现要点
      </div>
      <el-timeline>
        <el-timeline-item timestamp="Vue 3 Composition API" placement="top">
          <p>使用 setup 语法糖、ref/reactive 响应式数据、computed/watch 计算属性与侦听器</p>
        </el-timeline-item>
        <el-timeline-item timestamp="Vue Router" placement="top">
          <p>10个路由配置，包含3个带params的路径(/stock/:code, /kline/:code, /financial/:code) 和 query 参数</p>
        </el-timeline-item>
        <el-timeline-item timestamp="Vuex 状态管理" placement="top">
          <p>state + getters + mutations + actions 管理自选股、对比列表、筛选条件等全局状态</p>
        </el-timeline-item>
        <el-timeline-item timestamp="Axios HTTP 请求" placement="top">
          <p>封装 axios 实例，6个API接口：获取股票列表、K线数据、财务数据、指标数据、自选股增删查</p>
        </el-timeline-item>
        <el-timeline-item timestamp="Element Plus UI" placement="top">
          <p>Table, Button, Input, Select, Tabs, Dialog, Form, Tag, Descriptions, Collapse, Timeline等组件</p>
        </el-timeline-item>
        <el-timeline-item timestamp="ECharts 可视化" placement="top">
          <p>K线图(candlestick) + 成交量柱状图 + 拖拽缩放(dataZoom) + 雷达图</p>
        </el-timeline-item>
        <el-timeline-item timestamp="CSV 导出" placement="top">
          <p>使用 Blob + URL.createObjectURL 实现浏览器端CSV文件下载，含UTF-8 BOM</p>
        </el-timeline-item>
        <el-timeline-item timestamp="json-server Mock" placement="top">
          <p>5个数据端点(stocks, kline, financial, indicators, watchlist)，支持 RESTful 增删改查</p>
        </el-timeline-item>
      </el-timeline>
    </div>

    <!-- 联系信息 -->
    <div class="page-card" style="text-align:center;color:#909399">
      <p>Vue.js 金融数据分析平台 · 前端交互大作业</p>
      <p style="margin-top:4px">Powered by Vue 3 + Element Plus + ECharts + json-server</p>
      <el-divider />
      <p style="font-size:13px">© 2025 金融数据分析平台 | 数据仅供学习参考，不构成投资建议</p>
    </div>
  </div>
</template>

<script setup>
const routeTable = [
  { path: '/', name: 'Home', page: '首页', params: '无' },
  { path: '/stocks', name: 'StockList', page: '行情列表', params: '无（支持query筛选参数）' },
  { path: '/stock/:code', name: 'StockDetail', page: '股票详情', params: 'code - 股票代码（如 AAPL）' },
  { path: '/kline/:code', name: 'KLineDetail', page: 'K线图详情', params: 'code - 股票代码；query: period' },
  { path: '/financial/:code', name: 'FinancialReport', page: '财务报表', params: 'code - 股票代码' },
  { path: '/watchlist', name: 'Watchlist', page: '自选股管理', params: '无' },
  { path: '/compare', name: 'StockCompare', page: '个股对比选择', params: 'query参数选择股票' },
  { path: '/compare/:ids', name: 'CompareResult', page: '对比结果', params: 'ids - 逗号分隔的股票代码' },
  { path: '/indicators', name: 'IndicatorCompare', page: '指标筛选对比', params: '无（支持query筛选参数）' },
  { path: '/about', name: 'About', page: '帮助/关于', params: '无' }
]
</script>
