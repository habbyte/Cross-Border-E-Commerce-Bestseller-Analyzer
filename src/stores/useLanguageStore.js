import { defineStore } from 'pinia'
import { ref } from 'vue'
import i18n, { SUPPORTED_LOCALES } from '@/i18n/index.js'

/**
 * 语言状态仅保留 zh-CN，待恢复多语言时可解除限制。
 * 操作步骤详见 docs/i18n-reenable.md。
 */
export const useLanguageStore = defineStore('language', () => {
  const defaultLocale = SUPPORTED_LOCALES[0]
  const locale = ref(defaultLocale)

  const setLocale = (nextLocale) => {
    const target = SUPPORTED_LOCALES.includes(nextLocale) ? nextLocale : defaultLocale
    locale.value = target
    // Composition API 模式：通过 i18n.global.locale.value 更新
    if (i18n?.global?.locale) {
      i18n.global.locale.value = target
    }
  }

  return {
    locale,
    setLocale
  }
})
