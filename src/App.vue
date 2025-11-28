<template>
  <div id="app" class="app">
    <AppNavigation />
    
    <main class="app-main">
      <div class="app-content">
        <!-- 路由视图：用 Suspense 包裹，fallback 展示 PageSkeleton -->
        <Suspense>
          <template #default>
            <router-view />
          </template>
          <template #fallback>
            <PageSkeleton />
          </template>
        </Suspense>
      </div>
    </main>
    
    <!-- 全局错误提示 -->
    <div v-if="error" class="error-toast" @click="clearError">
      <span class="error-icon">⚠️</span>
      <span class="error-message">{{ error }}</span>
      <button class="error-close">×</button>
    </div>
    
    <!-- 全局加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner">
        <div class="spinner"></div>
        <div class="loading-text">{{ $t('common.loading') }}</div>
      </div>
    </div>
    
    <!-- Strategy Room 悬浮按钮：在非 /strategy 页面显示，点击进入策略室 -->
    <button
      v-if="showStrategyFab"
      class="ai-chatbot-placeholder"
      type="button"
      @click="openStrategy"
      aria-label="Open AI Strategy Room"
    ></button>
  </div>
</template>

<script>
/**
 * 主应用组件
 * 统一的应用布局和全局状态管理
 */
import { computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppNavigation from './components/AppNavigation.vue'
import { useProductStore } from './stores/useProductStore.js'
import { useSettingsStore } from './stores/useSettingsStore.js'
import PageSkeleton from '@/components/common/PageSkeleton.vue'

export default {
  name: 'App',
  
  components: {
    AppNavigation,
    PageSkeleton
  },
  
  setup() {
    const router = useRouter()
    const route = useRoute()
    const productStore = useProductStore()
    const settingsStore = useSettingsStore()
    
    // 计算属性
    const loading = computed(() => productStore.loading)
    const error = computed(() => productStore.error)
    
    // 方法
    const clearError = () => {
      productStore.clearError()
    }

    /**
     * openStrategy
     * 进入 AI 选品策略师页面
     */
    const openStrategy = () => {
      router.push('/strategy')
    }

    /**
     * showStrategyFab
     * 当当前路由不是 /strategy 时显示悬浮入口按钮
     */
    const showStrategyFab = computed(() => route.path !== '/strategy')
    
    // 生命周期
    onMounted(async () => {
      try {
        await settingsStore.initialize()
        await productStore.initialize()
      } catch (err) {
        console.error('App initialization failed:', err)
      }
    })
    
    return {
      loading,
      error,
      clearError,
      openStrategy,
      showStrategyFab
    }
  }
}
</script>

<style>
/* 全局样式重置和基础样式 */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  font-size: 14px;
  line-height: 1.5;
}

body {
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, 
               "Helvetica Neue", Arial, "Noto Sans", sans-serif, "Apple Color Emoji", 
               "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";
  background: #f6f8fb;
  color: #1f2937;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* CSS 变量定义 */
:root {
  --color-bg: #f6f8fb;
  --color-card: #ffffff;
  --color-text: #1f2937;
  --color-text-muted: #6b7280;
  --color-brand: #2563eb;
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-danger: #ef4444;
  --radius: 12px;
  --shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  --shadow-lg: 0 4px 16px rgba(0, 0, 0, 0.12);
}

/* 应用布局 */
.app {
  display: flex;
  min-height: 100vh;
}

.app-main {
  flex: 1;
  margin-left: 240px;
  min-height: 100vh;
}

.app-content {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

/* 全局组件样式 */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--color-brand);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-secondary {
  background: #f3f4f6;
  color: var(--color-text);
}

.btn-secondary:hover:not(:disabled) {
  background: #e5e7eb;
}

.btn-ghost {
  background: transparent;
  color: var(--color-text);
  border: 1px solid #e5e7eb;
}

.btn-ghost:hover:not(:disabled) {
  background: #f9fafb;
}

.btn-danger {
  background: var(--color-danger);
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #dc2626;
}

/* 表单元素 */
.form-input,
.form-select {
  padding: 8px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  background: white;
  transition: border-color 0.2s ease;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: var(--color-brand);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

/* 卡片样式 */
.card {
  background: var(--color-card);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 20px;
}

.card-header {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f3f4f6;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

/* 网格布局 */
.grid {
  display: grid;
  gap: 20px;
}

.grid-2 {
  grid-template-columns: repeat(2, 1fr);
}

.grid-3 {
  grid-template-columns: repeat(3, 1fr);
}

.grid-4 {
  grid-template-columns: repeat(4, 1fr);
}

/* 错误提示 */
.error-toast {
  position: fixed;
  top: 20px;
  right: 20px;
  background: var(--color-danger);
  color: white;
  padding: 12px 16px;
  border-radius: 8px;
  box-shadow: var(--shadow-lg);
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  z-index: 1000;
  animation: slideIn 0.3s ease;
}

.error-icon {
  font-size: 16px;
}

.error-message {
  flex: 1;
  font-size: 14px;
}

.error-close {
  background: none;
  border: none;
  color: white;
  font-size: 18px;
  cursor: pointer;
  padding: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 加载状态 */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

.loading-spinner {
  text-align: center;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #f3f4f6;
  border-top: 3px solid var(--color-brand);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 8px;
}

.loading-text {
  font-size: 14px;
  color: var(--color-text-muted);
}

/* 动画 */
@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .app-main {
    margin-left: 0;
  }
  
  .app-content {
    padding: 16px;
  }
  
  .grid-2,
  .grid-3,
  .grid-4 {
    grid-template-columns: 1fr;
  }
  
  .error-toast {
    left: 16px;
    right: 16px;
    top: 16px;
  }
}

/* 工具类 */
.text-center { text-align: center; }
.text-right { text-align: right; }
.text-muted { color: var(--color-text-muted); }
.text-success { color: var(--color-success); }
.text-warning { color: var(--color-warning); }
.text-danger { color: var(--color-danger); }

.mb-0 { margin-bottom: 0; }
.mb-1 { margin-bottom: 8px; }
.mb-2 { margin-bottom: 16px; }
.mb-3 { margin-bottom: 24px; }

.mt-0 { margin-top: 0; }
.mt-1 { margin-top: 8px; }
.mt-2 { margin-top: 16px; }
.mt-3 { margin-top: 24px; }

/* AI Chatbot 悬浮按钮占位符样式 */
.ai-chatbot-placeholder {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 60px;
  height: 60px;
  background: var(--color-brand);
  border-radius: 50%;
  box-shadow: var(--shadow-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 998;
  transition: all 0.3s ease;
  opacity: 0.7;
}

.ai-chatbot-placeholder:hover {
  opacity: 1;
  transform: scale(1.05);
  box-shadow: 0 8px 24px rgba(37, 99, 235, 0.3);
}

.ai-chatbot-placeholder::before {
  content: "🤖";
  font-size: 24px;
  color: white;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .ai-chatbot-placeholder {
    bottom: 16px;
    right: 16px;
    width: 56px;
    height: 56px;
  }
  
  .ai-chatbot-placeholder::before {
    font-size: 22px;
  }
}
</style>
