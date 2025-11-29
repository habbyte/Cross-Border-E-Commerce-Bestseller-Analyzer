import { defineStore } from 'pinia'
import { reactive, ref, watch } from 'vue'
import { events } from '@/analytics/events.js'

const STORAGE_KEY = 'onboarding_state_v1'

const defaultState = () => ({
  steps: {
    search: false,
    compare: false,
    monitor: false
  },
  dismissed: false
})

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return defaultState()
    const parsed = JSON.parse(raw)
    return {
      steps: { ...defaultState().steps, ...(parsed.steps || {}) },
      dismissed: Boolean(parsed.dismissed)
    }
  } catch (error) {
    console.warn('Failed to load onboarding state:', error)
    return defaultState()
  }
}

export const useOnboardingStore = defineStore('onboarding', () => {
  const initial = loadState()
  const steps = reactive(initial.steps)
  const dismissed = ref(initial.dismissed)

  const persist = () => {
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          steps,
          dismissed: dismissed.value
        })
      )
    } catch (error) {
      console.warn('Failed to persist onboarding state:', error)
    }
  }

  watch(
    () => ({ ...steps, dismissed: dismissed.value }),
    persist,
    { deep: true }
  )

  const isCompleted = (step) => Boolean(steps[step])

  const mark = (step) => {
    if (!Object.prototype.hasOwnProperty.call(steps, step)) return
    if (steps[step]) return
    steps[step] = true
    events.track('onboarding_step_completed', { step })
  }

  const dismiss = () => {
    if (dismissed.value) return
    dismissed.value = true
    events.track('onboarding_dismissed')
  }

  const reset = () => {
    const fresh = defaultState()
    Object.assign(steps, fresh.steps)
    dismissed.value = fresh.dismissed
    persist()
    events.track('onboarding_reset')
  }

  const currentStep = () => Object.keys(steps).find((key) => !steps[key])

  return {
    steps,
    dismissed,
    isCompleted,
    mark,
    dismiss,
    reset,
    currentStep
  }
})
