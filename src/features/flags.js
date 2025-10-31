/**
 * 全局功能开关
 * 默认读取 Vite 环境变量；未配置时回退为 true。
 */
const resolveFlag = (name, fallback = true) => {
  const value = import.meta.env?.[`VITE_FLAG_${name.toUpperCase()}`]
  if (typeof value === 'string') {
    return value === 'true'
  }
  return fallback
}

export const FLAGS = {
  emptyWarmCard: resolveFlag('empty_warm_card'),
  onboarding: resolveFlag('onboarding'),
  reasonCard: resolveFlag('reason_card')
}

export const isFeatureEnabled = (flagName) => Boolean(FLAGS[flagName])
