const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    port: 8080,
    // 关闭 webpack 错误遮罩，避免 ResizeObserver 等浏览器警告弹窗
    client: {
      overlay: {
        errors: false,
        warnings: false,
        runtimeErrors: false
      }
    },
    proxy: {
      '/api': {
        target: 'http://localhost:3000',
        changeOrigin: true,
        pathRewrite: { '^/api': '' }
      }
    }
  }
})
