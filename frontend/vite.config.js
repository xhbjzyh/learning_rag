import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],

  // 开发服务器配置
  server: {
    port: 3000, // 前端运行在3000端口
    open: true, // 自动打开浏览器
    cors: true, // 允许跨域

    // 代理配置：解决前端跨域访问后端的问题
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000', // 后端地址
        changeOrigin: true,
        rewrite: (path) => path
      }
    }
  },

  // 路径别名配置
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  }
})