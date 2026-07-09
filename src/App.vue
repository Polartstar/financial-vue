<template>
  <div id="app">
    <el-container style="min-height: 100vh;">
      
      <!-- 侧边导航栏 -->
      <el-aside width="220px" class="app-aside">
        <div class="logo-area">
          <el-icon :size="28" color="#409eff"><TrendCharts /></el-icon>
          <span class="logo-text">金融数据分析</span>
        </div>
        <el-menu
          :default-active="currentRoute"
          router
          background-color="#001529"
          text-color="#ffffffcc"
          active-text-color="#409eff"
        >
          <el-menu-item index="/">
            <el-icon><HomeFilled /></el-icon>
            <span>首页</span>
          </el-menu-item>
          <el-menu-item index="/stocks">
            <el-icon><DataBoard /></el-icon>
            <span>行情列表</span>
          </el-menu-item>
          <el-menu-item index="/watchlist">
            <el-icon><StarFilled /></el-icon>
            <span>自选股</span>
          </el-menu-item>
          <el-menu-item index="/compare">
            <el-icon><Opportunity /></el-icon>
            <span>个股对比</span>
          </el-menu-item>
          <el-menu-item index="/indicators">
            <el-icon><Coin /></el-icon>
            <span>指标筛选</span>
          </el-menu-item>
          
          <el-menu-item index="/about">
            <el-icon><InfoFilled /></el-icon>
            <span>帮助/关于</span>
          </el-menu-item>
        
        </el-menu>
      </el-aside>

      <!-- 主内容区域 -->
      <el-container>
        <el-header class="app-header">
          <div class="header-left">
            <h2 class="page-title">Vue.js 金融数据分析平台</h2>
          </div>
          <div class="header-right">
            <el-tag type="info" effect="dark">
              <el-icon style="margin-right:4px"><Clock /></el-icon>
              数据来源: json-server Mock API
            </el-tag>
          </div>
        </el-header>
        
        <el-main class="app-main">
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </el-main>
        
        <el-footer class="app-footer">
          <span>Vue3 + Element Plus + ECharts + json-server — 金融数据分析交互大作业</span>
        </el-footer>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
// computed 计算属性
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const currentRoute = computed(() => route.path)
</script>

<style>
/* 全局样式 */
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Microsoft YaHei', sans-serif; }

.app-aside {
  background-color: #001529;
  overflow-y: auto;
}

.logo-area {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.logo-text {
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 1px;
}

.app-header {
  background: linear-gradient(135deg, #1a73e8, #409eff);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 64px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

.page-title {
  font-size: 20px;
  font-weight: 500;
  letter-spacing: 1px;
}

.header-right .el-tag {
  font-size: 13px;
}

.app-main {
  background-color: #f0f2f5;
  padding: 20px 24px;
  min-height: calc(100vh - 64px - 60px);
}

.app-footer {
  background-color: #001529;
  color: rgba(255,255,255,0.65);
  text-align: center;
  line-height: 60px;
  font-size: 13px;
  height: 60px;
}

/* 页面切换动画 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.25s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

/* 公用卡片样式 */
.page-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}

.page-card .card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid #409eff;
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
