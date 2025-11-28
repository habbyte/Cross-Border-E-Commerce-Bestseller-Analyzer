import { createI18n } from 'vue-i18n'
import zhCN from './lang/zh-CN.json'
import en from './lang/en.json'
// 默认语言：简体中文；支持双语（zh-CN, en）
const DEFAULT_LOCALE = 'zh-CN'

export const SUPPORTED_LOCALES = [DEFAULT_LOCALE, 'en']

const messages = {
  'zh-CN': zhCN,
  en
}

const i18n = createI18n({
  legacy: false,
  // 在模板中启用全局 $t 注入，避免各页面重复 useI18n
  globalInjection: true,
  locale: DEFAULT_LOCALE,
  fallbackLocale: DEFAULT_LOCALE,
  messages,
  missingWarn: import.meta.env.DEV,
  fallbackWarn: false
})

export default i18n
