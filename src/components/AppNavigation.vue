<template>
  <aside class="app-navigation">
    <div class="nav-header">
      <h1 class="nav-logo">跨境电商爆款分析器</h1>
    </div>
    
    <nav class="nav-menu">
      <router-link
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ 'nav-item--active': $route.path === item.path }"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>
    
    <div class="nav-footer">
      <div class="nav-version">版本 v1.0.0</div>
    </div>
  </aside>
</template>

<script>
/**
 * 应用导航组件
 * 统一的导航管理，消除原型中的手动路由切换
 */
export default {
  name: 'AppNavigation',
  data() {
    return {
      menuItems: [
        { path: '/search', label: '商品搜索', icon: '🔍' },
        { path: '/', label: '数据仪表盘', icon: '📊' },
        { path: '/products', label: '商品管理', icon: '📦' },
        { path: '/compare', label: '商品对比', icon: '⚖️' },
        { path: '/watchlist', label: '监控列表', icon: '👁️' },
        { path: '/settings', label: '系统设置', icon: '⚙️' }
      ]
    }
  }
}
</script>

<style scoped>
.app-navigation {
  width: 240px;
  background: #0f172a;
  color: #e5e7eb;
  display: flex;
  flex-direction: column;
  height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 100;
}

.nav-header {
  padding: 20px 18px;
  border-bottom: 1px solid #1e293b;
}

.nav-logo {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.3px;
  color: #fff;
}

.nav-menu {
  flex: 1;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 10px;
  color: #cbd5e1;
  text-decoration: none;
  transition: all 0.2s ease;
  font-size: 14px;
  font-weight: 500;
}

.nav-item:hover {
  background: #1e293b;
  color: #fff;
}

.nav-item--active {
  background: #172554;
  color: #fff;
}

.nav-icon {
  font-size: 16px;
  width: 20px;
  text-align: center;
}

.nav-label {
  flex: 1;
}

.nav-footer {
  padding: 16px 18px;
  border-top: 1px solid #1e293b;
}

.nav-version {
  font-size: 12px;
  color: #64748b;
  text-align: center;
}

@media (max-width: 768px) {
  .app-navigation {
    width: 200px;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
  }
  
  .app-navigation.mobile-open {
    transform: translateX(0);
  }
  
  .nav-item {
    padding: 10px 12px;
  }
  
  .nav-label {
    font-size: 13px;
  }
}

@media (max-width: 480px) {
  .app-navigation {
    width: 100%;
  }
  
  .nav-item {
    justify-content: center;
    flex-direction: column;
    gap: 4px;
    padding: 12px 8px;
  }
  
  .nav-icon {
    font-size: 20px;
  }
  
  .nav-label {
    font-size: 11px;
  }
}
</style>
