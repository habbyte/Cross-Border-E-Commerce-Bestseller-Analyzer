/**
 * Vue Router 配置
 * 统一的路由管理，消除原型中的手动DOM操作路由切换
 */

import { defineAsyncComponent } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import PageSkeleton from '@/components/common/PageSkeleton.vue'
import NotFound from '@/views/NotFound.vue'

/**
 * 统一的懒加载工厂，提供加载和错误占位组件
 */
const lazy = (loader) =>
  defineAsyncComponent({
    loader,
    // 静态导入占位与错误组件，避免动态导入失败导致空白
    loadingComponent: PageSkeleton,
    errorComponent: NotFound,
    delay: 200,
    timeout: 30000
  })

// 多语言路由前缀暂时停用；恢复方案见 docs/i18n-reenable.md
const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: lazy(() => import('@/views/Dashboard.vue')),
    meta: {
      title: 'Dashboard',
      icon: '📊'
    }
  },
  {
    path: '/search',
    name: 'Search',
    component: lazy(() => import('@/views/Search.vue')),
    meta: {
      title: '搜索分析',
      icon: '🔍'
    }
  },
  {
    path: '/products/:id',
    name: 'ProductDetail',
    component: lazy(() => import('@/views/ProductDetail.vue')),
    meta: {
      title: '商品详情',
      icon: '📦'
    },
    props: true
  },
  {
    path: '/compare',
    name: 'Compare',
    component: lazy(() => import('@/views/Compare.vue')),
    meta: {
      title: '对比分析',
      icon: '⚖️'
    }
  },
  {
    path: '/watchlist',
    name: 'Watchlist',
    component: lazy(() => import('@/views/Watchlist.vue')),
    meta: {
      title: '监控列表',
      icon: '👁️'
    }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: lazy(() => import('@/views/Settings.vue')),
    meta: {
      title: '系统设置',
      icon: '⚙️'
    }
  },
  {
    path: '/products',
    name: 'Products',
    component: lazy(() => import('@/views/Products.vue')),
    meta: { title: '商品管理' }
  },
  {
    path: '/strategy',
    name: 'StrategyRoom',
    component: lazy(() => import('@/views/StrategyRoom.vue')),
    meta: {
      title: 'AI 选品策略师',
      icon: '🤖'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: lazy(() => import('@/views/NotFound.vue')),
    meta: { title: '404' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }
    return { top: 0 }
  }
})

// 路由守卫
router.beforeEach((to, from, next) => {
  if (to.meta.title) {
    document.title = `${to.meta.title} - 跨境爆款分析器`
  }

  next()
})

export default router
