import { createI18n } from 'vue-i18n'
import zhCN from './lang/zh-CN.json'

// 仅保留简体中文运行，未来恢复多语言可将 _disabled 下的语言包搬回并在此注册
const DEFAULT_LOCALE = 'zh-CN'

export const SUPPORTED_LOCALES = [DEFAULT_LOCALE]

const messages = {
  'zh-CN': zhCN
}

const i18n = createI18n({
  legacy: false,
  locale: DEFAULT_LOCALE,
  fallbackLocale: DEFAULT_LOCALE,
  messages,
  missingWarn: import.meta.env.DEV,
  fallbackWarn: false
})

export default i18n
