<template>
  <section
    class="empty-warm-card"
    role="status"
    aria-live="polite"
  >
    <slot name="illustration">
      <svg
        class="empty-warm-card__illustration"
        viewBox="0 0 64 64"
        aria-hidden="true"
      >
        <circle
          cx="32"
          cy="32"
          r="30"
          fill="rgba(59,130,246,0.08)"
          stroke="rgba(59,130,246,0.3)"
          stroke-width="2"
        />
        <path
          d="M20 33h16l-5.2 5.2"
          stroke="rgba(59,130,246,0.8)"
          stroke-width="3"
          fill="none"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
        <path
          d="M32 20l9 9-9 9"
          stroke="rgba(59,130,246,0.8)"
          stroke-width="3"
          fill="none"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </slot>
    <h2 class="empty-warm-card__title">
      {{ t(titleKey) }}
    </h2>
    <p class="empty-warm-card__desc">
      {{ t(descKey) }}
    </p>
    <div class="empty-warm-card__actions">
      <button
        type="button"
        class="btn btn-primary"
        @click="handleLoadSample"
      >
        {{ t(primaryKey) }}
      </button>
      <button
        type="button"
        class="btn btn-secondary"
        @click="handleViewGuide"
      >
        {{ t(secondaryKey) }}
      </button>
    </div>
  </section>
</template>

<script>
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { events } from '@/analytics/events.js'

export default {
  name: 'EmptyWarmCard',
  props: {
    titleKey: {
      type: String,
      default: 'empty.warm.title'
    },
    descKey: {
      type: String,
      default: 'empty.warm.desc'
    },
    primaryKey: {
      type: String,
      default: 'empty.warm.ctaPrimary'
    },
    secondaryKey: {
      type: String,
      default: 'empty.warm.ctaSecondary'
    }
  },
  emits: ['load-sample', 'view-guide'],
  setup(props, { emit }) {
    const { t } = useI18n()

    onMounted(() => {
      events.track('empty_warm_shown')
    })

    const handleLoadSample = () => {
      events.track('empty_warm_load_sample_click')
      emit('load-sample')
    }

    const handleViewGuide = () => {
      events.track('empty_warm_view_guide_click')
      emit('view-guide')
    }

    return {
      t,
      handleLoadSample,
      handleViewGuide
    }
  }
}
</script>

<style scoped>
.empty-warm-card {
  background: var(--bg-card);
  border-radius: 16px;
  padding: 32px 24px;
  text-align: center;
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: center;
}

.empty-warm-card__illustration {
  width: 96px;
  height: 96px;
}

.empty-warm-card__title {
  margin: 0;
  font-size: 1.5rem;
  color: var(--text-primary);
  font-weight: 700;
}

.empty-warm-card__desc {
  margin: 0;
  color: var(--text-secondary);
  max-width: 420px;
}

.empty-warm-card__actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

.btn {
  padding: 8px 18px;
  border: none;
  border-radius: 9999px;
  cursor: pointer;
  font-weight: 600;
}

.btn-primary {
  background: var(--primary-color);
  color: #fff;
}

.btn-secondary {
  background: var(--bg-secondary);
  color: var(--text-primary);
}
</style>

