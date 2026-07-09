import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// 抑制 ResizeObserver 无害警告，防止被 webpack 错误遮罩捕获
const originalOnError = window.onerror
window.onerror = (msg, url, line, col, error) => {
  if (typeof msg === 'string' && msg.includes('ResizeObserver')) {
    return true // 吞掉这个错误
  }
  return originalOnError ? originalOnError(msg, url, line, col, error) : false
}

const app = createApp(App)

// 注册所有Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(store)
app.use(router)
app.use(ElementPlus)
app.mount('#app')
