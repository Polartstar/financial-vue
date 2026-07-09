import { createStore } from 'vuex'

export default createStore({
  state: {
    // 自选股列表 - 存储股票代码数组
    watchlist: [],
    // 当前对比的股票代码列表
    compareList: [],
    // 用户筛选条件
    filterConditions: {
      industry: '',
      minPrice: null,
      maxPrice: null,
      minChange: null,
      maxPe: null
    },
    // 当前选择的指标
    selectedIndicators: ['pe', 'pb', 'roe', 'debtRatio'],
    // 全局加载状态
    loading: false
  },
  
  getters: {
    // 获取自选股列表
    getWatchlist: state => state.watchlist,
    // 检查某股票是否已加入自选
    isInWatchlist: state => code => state.watchlist.some(item => item.stockCode === code),
    // 获取对比列表
    getCompareList: state => state.compareList,
    // 获取筛选条件
    getFilterConditions: state => state.filterConditions,
    // 获取选中的指标
    getSelectedIndicators: state => state.selectedIndicators
  },
  mutations: {
    // 设置自选股列表
    SET_WATCHLIST(state, list) {
      state.watchlist = list
    },
    // 添加自选股
    ADD_TO_WATCHLIST(state, item) {
      if (!state.watchlist.some(w => w.stockCode === item.stockCode)) {
        state.watchlist.push(item)
      }
    },
    // 从自选股移除
    REMOVE_FROM_WATCHLIST(state, stockCode) {
      state.watchlist = state.watchlist.filter(w => w.stockCode !== stockCode)
    },
    // 添加到对比列表
    ADD_TO_COMPARE(state, stockCode) {
      if (!state.compareList.includes(stockCode) && state.compareList.length < 4) {
        state.compareList.push(stockCode)
      }
    },
    // 从对比列表移除
    REMOVE_FROM_COMPARE(state, stockCode) {
      state.compareList = state.compareList.filter(c => c !== stockCode)
    },
    // 清空对比列表
    CLEAR_COMPARE(state) {
      state.compareList = []
    },
    // 设置筛选条件
    SET_FILTER_CONDITIONS(state, conditions) {
      state.filterConditions = { ...state.filterConditions, ...conditions }
    },
    // 重置筛选条件
    RESET_FILTER_CONDITIONS(state) {
      state.filterConditions = {
        industry: '',
        minPrice: null,
        maxPrice: null,
        minChange: null,
        maxPe: null
      }
    },
    // 设置选中的指标
    SET_SELECTED_INDICATORS(state, indicators) {
      state.selectedIndicators = indicators
    },
    // 设置加载状态
    SET_LOADING(state, val) {
      state.loading = val
    }
  },
  actions: {
    // 从服务器同步自选股列表
    async fetchWatchlist({ commit }) {
      try {
        const axios = (await import('axios')).default
        const res = await axios.get('/api/watchlist')
        commit('SET_WATCHLIST', res.data)
      } catch (e) {
        console.error('获取自选股失败:', e)
        commit('SET_WATCHLIST', [])
      }
    },
    // 添加自选股（同时同步到服务器）
    async addToWatchlist({ commit, state }, { stockCode, note = '' }) {
      try {
        const axios = (await import('axios')).default
        const newItem = {
          stockCode,
          addedAt: new Date().toISOString(),
          note
        }
        const res = await axios.post('/api/watchlist', newItem)
        commit('ADD_TO_WATCHLIST', res.data)
      } catch (e) {
        console.error('添加自选股失败:', e)
      }
    },
    // 移除自选股（同时同步到服务器）
    async removeFromWatchlist({ commit }, stockCode) {
      try {
        const axios = (await import('axios')).default
        // 查找要删除的条目ID
        const res = await axios.get('/api/watchlist', {
          params: { stockCode }
        })
        if (res.data.length > 0) {
          await axios.delete(`/api/watchlist/${res.data[0].id}`)
        }
        commit('REMOVE_FROM_WATCHLIST', stockCode)
      } catch (e) {
        console.error('移除自选股失败:', e)
      }
    }
  },
  modules: {}
})
