<template>
  <div class="page-skeleton">
    <div class="skeleton-header"></div>
    <div class="skeleton-grid">
      <div v-for="n in 6" :key="n" class="skeleton-card"></div>
    </div>
  </div>
</template>

<script>
/**
 * PageSkeleton / 页面骨架组件
 * 用于 Suspense fallback 展示，避免空白或闪烁。
 */
export default { name: 'PageSkeleton' }
</script>

<style scoped>
.page-skeleton { padding: 24px; }
.skeleton-header { height: 24px; background: #e5e7eb; border-radius: 6px; margin-bottom: 16px; }
.skeleton-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }
.skeleton-card { height: 160px; background: #f3f4f6; border-radius: 8px; }
</style>