<template>
  <div class="not-found">
    <div class="icon">🧭</div>
    <h1 class="title">{{ $t('notFound.title') }}</h1>
    <p class="desc">{{ $t('notFound.description') }}</p>
    <router-link to="/" class="btn btn-primary">{{ $t('notFound.goHome') }}</router-link>
  </div>
</template>

<script>
/**
 * NotFound 页面
 * 404 兜底，保证路由错误不会导致白屏或不可见。
 */
export default {
  name: 'NotFound'
}
</script>

<style scoped>
.not-found {
  display: grid;
  place-items: center;
  gap: 12px;
  padding: 48px;
}
.icon { font-size: 48px; }
.title { font-size: 20px; font-weight: 700; }
.desc { color: var(--text-secondary); }
</style>
