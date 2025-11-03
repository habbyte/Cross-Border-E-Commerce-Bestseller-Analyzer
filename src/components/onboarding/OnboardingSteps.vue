<template>
  <aside
    v-if="visible"
    class="onboarding-steps"
    role="complementary"
    aria-label="onboarding"
  >
    <div class="onboarding-steps__header">
      <h2 class="onboarding-steps__title">
        {{ t('onboarding.title') }}
      </h2>
      <div class="onboarding-steps__actions">
        <button
          v-if="hasProgress"
          type="button"
          class="onboarding-steps__reset"
          @click="handleReset"
        >
          {{ t('onboarding.cta.reset') }}
        </button>
        <button
          type="button"
          class="onboarding-steps__dismiss"
          @click="handleDismiss"
        >
          {{ t('onboarding.cta.dismiss') }}
        </button>
      </div>
    </div>
    <template v-if="allCompleted">
      <div class="onboarding-steps__complete">
        {{ t('onboarding.allDone') }}
      </div>
      <div class="onboarding-steps__footer">
        <button
          type="button"
          class="btn btn-primary"
          @click="handleReset"
        >
          {{ t('onboarding.cta.reset') }}
        </button>
      </div>
    </template>
    <template v-else>
      <ol class="onboarding-steps__list">
        <li
          v-for="step in steps"
          :key="step.id"
          class="onboarding-steps__item"
          :class="{
            'is-completed': step.completed,
            'is-current': step.id === nextStepId
          }"
        >
          <div
            class="onboarding-steps__status"
            aria-hidden="true"
          >
            <span v-if="step.completed">✔</span>
            <span v-else>{{ step.index }}</span>
          </div>
          <div class="onboarding-steps__content">
            <p class="onboarding-steps__label">
              {{ step.label }}
            </p>
            <p
              v-if="step.completed"
              class="onboarding-steps__hint"
            >
              {{ t('onboarding.done') }}
            </p>
          </div>
        </li>
      </ol>
      <div class="onboarding-steps__footer">
        <button
          type="button"
          class="btn btn-primary"
          :disabled="!nextStepId"
          @click="handleNext"
        >
          {{ t('onboarding.cta.next') }}
        </button>
      </div>
    </template>
  </aside>
</template>

<script>
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useOnboardingStore } from '@/stores/useOnboardingStore.js'
import { events } from '@/analytics/events.js'

export default {
  name: 'OnboardingSteps',
  emits: ['next-step'],
  setup(_, { emit }) {
    const { t } = useI18n()
    const onboarding = useOnboardingStore()

    const steps = computed(() => {
      const order = ['search', 'compare', 'monitor']
      return order.map((id, index) => ({
        id,
        index: index + 1,
        label: t(`onboarding.steps.${id}`),
        completed: onboarding.isCompleted(id)
      }))
    })

    const nextStepId = computed(() => onboarding.currentStep())
    const allCompleted = computed(() => steps.value.every((step) => step.completed))
    const hasProgress = computed(() => steps.value.some((step) => step.completed))
    const visible = computed(() => !onboarding.dismissed)

    onMounted(() => {
      steps.value
        .filter((step) => !step.completed)
        .forEach((step) => {
          events.track('onboarding_step_shown', { step: step.id })
        })
    })

    const handleNext = () => {
      if (!nextStepId.value) return
      emit('next-step', nextStepId.value)
      events.track('onboarding_step_next_click', { step: nextStepId.value })
    }

    const handleDismiss = () => {
      onboarding.dismiss()
    }

    const handleReset = () => {
      onboarding.reset()
    }

    return {
      t,
      steps,
      nextStepId,
      handleNext,
      handleDismiss,
      handleReset,
      visible,
      allCompleted,
      hasProgress
    }
  }
}
</script>

<style scoped>
.onboarding-steps {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.onboarding-steps__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.onboarding-steps__actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.onboarding-steps__title {
  margin: 0;
  font-size: 1.1rem;
  color: var(--text-primary);
}

.onboarding-steps__dismiss {
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.9rem;
}

.onboarding-steps__reset {
  border: none;
  background: transparent;
  color: var(--primary-color);
  cursor: pointer;
  font-size: 0.9rem;
}

.onboarding-steps__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 12px;
}

.onboarding-steps__item {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  border: 1px dashed transparent;
}

.onboarding-steps__item.is-current {
  border-color: var(--primary-color);
  background: rgba(59, 130, 246, 0.08);
}

.onboarding-steps__item.is-completed {
  opacity: 0.75;
}

.onboarding-steps__status {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.onboarding-steps__item.is-completed .onboarding-steps__status {
  background: #10b981;
  color: #fff;
}

.onboarding-steps__label {
  margin: 0;
  color: var(--text-primary);
  font-weight: 600;
}

.onboarding-steps__hint {
  margin: 4px 0 0;
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.onboarding-steps__complete {
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.4);
  border-radius: 8px;
  padding: 12px;
  color: var(--text-success, #047857);
  text-align: center;
  font-weight: 600;
}

.onboarding-steps__footer {
  display: flex;
  justify-content: flex-end;
}

.btn {
  padding: 8px 16px;
  border-radius: 9999px;
  border: none;
  cursor: pointer;
  font-weight: 600;
}

.btn-primary {
  background: var(--primary-color);
  color: #fff;
}
</style>
