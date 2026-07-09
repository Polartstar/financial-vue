import axios from 'axios'

// 创建axios实例，baseURL通过vue.config.js代理到json-server
const service = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 响应拦截器
service.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API请求异常:', error.message || error)
    return Promise.reject(error)
  }
)

// ========== 股票接口 ==========

/**
 * 获取所有股票列表
 * @param {Object} params - 查询参数 (industry, price_gte, price_lte 等)
 */
export function getStocks(params) {
  return service.get('/stocks', { params })
}

/**
 * 根据股票代码获取单只股票详情
 * @param {string} code - 股票代码
 */
export function getStockByCode(code) {
  return service.get('/stocks', { params: { code } })
}

// ========== K线数据接口 ==========

/**
 * 获取某只股票的K线数据
 * @param {string} stockCode - 股票代码
 * @param {number} limit - 限制条数
 */
export function getKLineData(stockCode, limit = 30) {
  return service.get('/kline', {
    params: { stockCode, _sort: 'date', _order: 'asc', _limit: limit }
  })
}

// ========== 财务报表接口 ==========

/**
 * 获取某只股票的财务数据
 * @param {string} stockCode - 股票代码
 */
export function getFinancialData(stockCode) {
  return service.get('/financial', { params: { stockCode, _sort: 'year', _order: 'desc' } })
}

// ========== 指标数据接口 ==========

/**
 * 获取所有股票的指标数据
 * @param {Object} params - 筛选参数
 */
export function getIndicators(params) {
  return service.get('/indicators', { params })
}

/**
 * 获取某只股票的指标数据
 * @param {string} stockCode - 股票代码
 */
export function getIndicatorByStock(stockCode) {
  return service.get('/indicators', { params: { stockCode } })
}

// ========== 自选股接口 ==========

/**
 * 获取自选股列表（包含完整的股票信息）
 */
export function getWatchlist() {
  return service.get('/watchlist')
}

/**
 * 添加自选股
 * @param {Object} data - { stockCode, addedAt, note }
 */
export function addToWatchlist(data) {
  return service.post('/watchlist', data)
}

/**
 * 删除自选股
 * @param {number} id - watchlist条目ID
 */
export function removeFromWatchlist(id) {
  return service.delete(`/watchlist/${id}`)
}

/**
 * 根据股票代码查找自选股条目
 * @param {string} stockCode
 */
export function findWatchlistItem(stockCode) {
  return service.get('/watchlist', { params: { stockCode } })
}

// ========== 行业板块接口 ==========

/**
 * 获取行业列表
 */
export function getSectors() {
  return service.get('/sectors')
}

export default service
