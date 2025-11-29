<template>
  <div>
    <!-- 加载状态 -->
    <template v-if="loading">
      <slot name="loading">
        <div
          class="state state--loading"
          role="status"
          aria-live="polite"
        >
          <div
            class="state__spinner"
            aria-hidden="true"
          />
          <p class="state__message">
            {{ loadingText }}
          </p>
        </div>
      </slot>
    </template>

    <!-- 错误状态 -->
    <template v-else-if="error">
      <slot
        name="error"
        :message="error"
      >
        <div
          class="state state--error"
          role="alert"
        >
          <div
            class="state__icon state__icon--error"
            aria-hidden="true"
          />
          <p class="state__message">
            {{ error }}
          </p>
        </div>
      </slot>
    </template>

    <!-- 空状态 -->
    <template v-else-if="isEmpty">
      <slot name="empty">
        <div
          class="state state--empty"
          role="status"
          aria-live="polite"
        >
          <div
            class="state__icon state__icon--empty"
            aria-hidden="true"
          />
          <p class="state__message">
            {{ emptyText }}
          </p>
        </div>
      </slot>
    </template>

    <!-- 正常内容 -->
    <template v-else>
      <slot />
    </template>
  </div>
</template>

<script>
export default {
  name: 'TriState',
  props: {
    loading: { type: Boolean, default: false },
    error: { type: String, default: '' },
    empty: { type: [Boolean, Number], default: false },
    emptyText: { type: String, default: '' },
    loadingText: { type: String, default: '加载中…' }
  },
  computed: {
    isEmpty() {
      return typeof this.empty === 'number' ? this.empty === 0 : !!this.empty
    }
  }
}
</script>

<style scoped>
.state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 24px;
  text-align: center;
  color: var(--text-secondary);
}

.state__message {
  margin: 0;
  font-size: 0.95rem;
}

.state__spinner {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 3px solid rgba(59, 130, 246, 0.2);
  border-top-color: rgba(59, 130, 246, 0.85);
  animation: tri-spin 1s linear infinite;
}

.state__icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.state__icon--error {
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
}

.state__icon--empty {
  background: rgba(148, 163, 184, 0.12);
  color: #475569;
}

@keyframes tri-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
