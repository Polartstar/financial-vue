# 📊 金融数据分析平台

> Vue.js在金融数据分析中的应用 — 前端交互大作业

## 项目简介

基于 **Vue 3 (Composition API) + Element Plus + ECharts + Vue Router + Vuex + Axios** 构建的交互式金融数据分析工具，后端使用 **json-server** 模拟 RESTful API。

### 功能模块

| 功能 | 说明 |
|------|------|
| 📊 行情列表 | 股票实时行情，支持行业/价格筛选、排序、行点击跳转详情 |
| 📈 K线图分析 | ECharts 交互式日K线，10/20/30日周期，数据表格与CSV导出 |
| 📋 财务报表 | 利润表/资产负债表/财务比率三标签切换，多只股票可选 |
| 🔍 指标筛选 | 市盈率/市净率/ROE等多维度筛选，自定义显示指标列 |
| ⭐ 自选股管理 | 添加/删除自选股，Vuex + json-server 同步存储 |
| 🔄 个股对比 | 2~4只股票横向对比表格 + ECharts 雷达图 |
| 💾 数据导出 | 所有表格一键导出CSV（Blob下载，UTF-8 BOM） |

### 路由结构（共10个）

| 路径 | 页面 | 参数 |
|------|------|------|
| `/` | 首页 | — |
| `/stocks` | 行情列表 | query筛选 |
| `/stock/:code` | 股票详情 | `:code` 股票代码 |
| `/kline/:code` | K线图详情 | `:code` 股票代码 |
| `/financial/:code` | 财务报表 | `:code` 股票代码 |
| `/watchlist` | 自选股管理 | — |
| `/compare` | 个股对比选择 | — |
| `/compare/:ids` | 对比结果 | `:ids` 逗号分隔 |
| `/indicators` | 指标筛选 | query筛选 |
| `/about` | 帮助/关于 | — |

## 技术栈

```
Vue 3 (Composition API) — 前端框架
Vue Router — 路由管理 (10个路由，含3个params)
Vuex — 状态管理 (自选股/对比/筛选条件)
Axios — HTTP请求封装 (6个API接口)
Element Plus — UI组件库 (10+种组件)
ECharts — 数据可视化 (K线图/雷达图)
json-server — Mock RESTful API (5个数据端点)
```

## 快速开始

```bash
# 1. 进入项目目录
cd financial-vue

# 2. 安装依赖
npm install

# 3. 启动后端Mock API
npm run api
# → json-server 运行在 http://localhost:3000

# 4. 另开终端启动前端
npm run serve
# → 开发服务器运行在 http://localhost:8080

# 或者一条命令同时启动
npm run dev
# → 使用 concurrently 同时启动前后端
```

## 项目结构

```
financial-vue/
├── public/index.html          # 入口HTML
├── src/
│   ├── api/index.js           # Axios 封装 (6个API)
│   ├── router/index.js        # 10个路由配置
│   ├── store/index.js         # Vuex 状态管理
│   ├── utils/helpers.js       # CSV导出 + 格式化工具
│   ├── views/                 # 10个页面组件
│   │   ├── Home.vue
│   │   ├── StockList.vue
│   │   ├── StockDetail.vue
│   │   ├── KLineDetail.vue
│   │   ├── FinancialReport.vue
│   │   ├── Watchlist.vue
│   │   ├── StockCompare.vue
│   │   ├── CompareResult.vue
│   │   ├── IndicatorCompare.vue
│   │   └── About.vue
│   ├── App.vue                # 根组件 (布局)
│   └── main.js                # 入口
├── db.json                    # json-server Mock数据
├── API.md                     # API接口文档
├── ASSESSMENT.md              # 考核要点文档
├── vue.config.js              # 代理配置
└── package.json
```

## API 数据端点

| 端点 | 说明 | 数据量 |
|------|------|--------|
| `/stocks` | 股票行情 | 12只 |
| `/kline` | K线数据 | 30条 |
| `/financial` | 财务报表 | 7条 |
| `/indicators` | 财务指标 | 12条 |
| `/watchlist` | 自选股 | 3条 |
| `/sectors` | 行业板块 | 7个 |
