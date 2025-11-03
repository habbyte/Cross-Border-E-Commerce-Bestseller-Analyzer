<template>
  <section
    class="reason-card"
    role="note"
    aria-live="polite"
  >
    <header class="reason-card__header">
      <h3 class="reason-card__title">
        {{ t('recommendation.title') }}
      </h3>
    </header>
    <ul class="reason-card__list">
      <li
        v-for="(reason, index) in translatedReasons"
        :key="index"
      >
        {{ reason }}
      </li>
    </ul>
    <footer class="reason-card__footer">
      <button
        type="button"
        class="btn btn-link"
        @click="handleDetails"
      >
        {{ t('recommendation.actions.details') }}
      </button>
    </footer>
  </section>
</template>

<script>
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { mapReasons } from '@/services/ReasonMapper.js'
import { events } from '@/analytics/events.js'

export default {
  name: 'ReasonCard',
  props: {
    product: {
      type: Object,
      required: true
    }
  },
  emits: ['view-details'],
  setup(props, { emit }) {
    const { t } = useI18n()

    const translatedReasons = computed(() =>
      mapReasons(props.product).map((reason) => t(reason.key, reason.values || {}))
    )

    onMounted(() => {
      events.track('reason_card_shown', { id: props.product?.id })
    })

    const handleDetails = () => {
      const productId = props.product?.id
      events.track('recommendation_reason_click_detail', { productId })
      events.track('reason_card_view_details_click', { id: productId })
      emit('view-details', props.product)
    }

    return {
      t,
      translatedReasons,
      handleDetails
    }
  }
}
</script>

<style scoped>
.reason-card {
  background: var(--bg-secondary);
  border-radius: 12px;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  border: 1px solid var(--border-color);
}

.reason-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.reason-card__title {
  margin: 0;
  font-size: 0.95rem;
  color: var(--text-primary);
}

.reason-card__list {
  margin: 0;
  padding-left: 18px;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.reason-card__list li + li {
  margin-top: 4px;
}

.reason-card__footer {
  display: flex;
  justify-content: flex-end;
}

.btn-link {
  background: transparent;
  border: none;
  color: var(--primary-color);
  cursor: pointer;
  font-size: 0.9rem;
  text-decoration: underline;
  padding: 0;
}
</style>
