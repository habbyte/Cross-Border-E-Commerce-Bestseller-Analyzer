import { defineStore } from 'pinia'
import { ref } from 'vue'
import { SUPPORTED_LOCALES } from '@/i18n/index.js'

/**
 * 语言状态仅保留 zh-CN，待恢复多语言时可解除限制。
 * 操作步骤详见 docs/i18n-reenable.md。
 */
export const useLanguageStore = defineStore('language', () => {
  const lockedLocale = SUPPORTED_LOCALES[0]
  const locale = ref(lockedLocale)

  const setLocale = (nextLocale) => {
    // 冻结语言选择，恢复流程参考 docs/i18n-reenable.md
    if (nextLocale !== lockedLocale) {
      console.info('[i18n] 多语言切换已冻结，当前仅使用 zh-CN。请查看 docs/i18n-reenable.md 了解恢复步骤。')
    }
    locale.value = lockedLocale
  }

  return {
    locale,
    setLocale
  }
})
