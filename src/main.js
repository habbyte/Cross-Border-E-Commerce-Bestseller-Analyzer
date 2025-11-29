/**
 * Vue应用入口文件
 * 初始化Vue应用、Pinia状态管理和Vue Router
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router/index.js'
import i18n from './i18n/index.js'
import './styles/global.css'
import imgFallback from './directives/imgFallback.js'

// 创建应用实例
const app = createApp(App)

// 创建 Pinia 状态管理
const pinia = createPinia()

// 注册插件
app.use(pinia)
app.use(router)
app.use(i18n)

// 注册全局指令：图片失败回退
app.directive('img-fallback', imgFallback)

// 全局错误处理（仅开发环境输出简洁日志）
app.config.errorHandler = (err, vm, info) => {
  if (import.meta.env.DEV) {
    // 仅输出一行摘要，避免刷屏
    console.error('[Vue Error]', info, '\n', err)
  }
}

// 全局错误监听：捕获窗口级错误与未处理的Promise拒绝
// 仅记录日志，不改变业务流程和UI行为
window.addEventListener('error', (e) => {
  if (import.meta.env.DEV) {
    console.error('[WindowError]', e.error || e)
  }
})

window.addEventListener('unhandledrejection', (e) => {
  if (import.meta.env.DEV) {
    console.error('[PromiseRejection]', e.reason)
  }
})

// 挂载应用
app.mount('#app')
