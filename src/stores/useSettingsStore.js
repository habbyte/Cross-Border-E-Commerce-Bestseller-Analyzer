/**
 * 设置状态管理
 * 统一管理应用设置，包括主题、语言、货币等
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useSettingsStore = defineStore('settings', () => {
  // 默认设置
  const defaultSettings = {
    general: {
      language: 'zh-CN',
      theme: 'light',
      currency: 'USD'
    },
    search: {
      defaultPlatform: '',
      pageSize: 12,
      autoRefresh: 0
    },
    alerts: {
      priceChangeThreshold: 10,
      salesChangeThreshold: 20,
      emailNotification: false,
      email: ''
    }
  }

  // 响应式状态 - 使用reactive确保深度响应式
  const settings = ref(JSON.parse(JSON.stringify(defaultSettings)))
  const originalSettings = ref(JSON.parse(JSON.stringify(defaultSettings)))
  const saving = ref(false)
  // 语言强制锁定 zh-CN，恢复多语言时请参阅 docs/i18n-reenable.md
  const lockedLanguage = defaultSettings.general.language

  // 汇率数据
  const exchangeRates = ref({
    USD: 1,
    EUR: 0.85,
    CNY: 7.2,
    JPY: 110,
    lastUpdate: new Date().toISOString(),
    source: 'ECB API'
  })

  // 计算属性
  const hasChanges = computed(() => {
    return JSON.stringify(settings.value) !== JSON.stringify(originalSettings.value)
  })

  const currentTheme = computed(() => settings.value.general.theme)
  const currentLanguage = computed(() => settings.value.general.language)
  const currentCurrency = computed(() => settings.value.general.currency)

  // 方法
  const loadSettings = () => {
    try {
      const saved = localStorage.getItem('app-settings')
      if (saved) {
        const parsed = JSON.parse(saved)
        settings.value = { ...defaultSettings, ...parsed }
        if (settings.value.general) {
          settings.value.general = {
            ...settings.value.general,
            language: lockedLanguage
          }
        } else {
          settings.value.general = { ...defaultSettings.general }
        }
        originalSettings.value = { ...settings.value }
      }
    } catch (error) {
      console.error('Failed to load settings:', error)
    }
  }

  const saveSettings = async () => {
    saving.value = true
    
    try {
      // 模拟保存延迟
      await new Promise(resolve => setTimeout(resolve, 500))
      
      // 保存到本地存储
      if (settings.value.general) {
        settings.value.general.language = lockedLanguage
      }
      localStorage.setItem('app-settings', JSON.stringify(settings.value))
      originalSettings.value = { ...settings.value }
      
      return true
    } catch (error) {
      console.error('Failed to save settings:', error)
      throw error
    } finally {
      saving.value = false
    }
  }

  const cancelChanges = () => {
    settings.value = { ...originalSettings.value }
  }

  const resetSettings = () => {
    settings.value = { ...defaultSettings }
  }

  const applyTheme = (theme) => {
    if (theme === 'auto') {
      // 检测系统主题
      const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      document.documentElement.classList.toggle('dark', isDark)
    } else if (theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  /**
   * 更新汇率数据
   * 从API获取最新汇率信息
   */
  const updateExchangeRates = async () => {
    try {
      // 模拟API调用 - 在实际项目中应该调用真实的汇率API
      // 例如：https://api.exchangerate-api.com/v4/latest/USD
      
      // 模拟汇率数据（基于USD）
      const mockRates = {
        USD: 1.0000,
        EUR: 0.8234 + (Math.random() - 0.5) * 0.01, // 添加小幅波动
        CNY: 7.2156 + (Math.random() - 0.5) * 0.1,
        JPY: 149.85 + (Math.random() - 0.5) * 2.0
      }
      
      // 更新汇率数据
      exchangeRates.value.USD = mockRates.USD
      exchangeRates.value.EUR = mockRates.EUR
      exchangeRates.value.CNY = mockRates.CNY
      exchangeRates.value.JPY = mockRates.JPY
      exchangeRates.value.lastUpdate = new Date().toISOString()
      exchangeRates.value.source = 'ExchangeRate-API'
      
      // 保存到本地存储
      localStorage.setItem('exchange-rates', JSON.stringify(exchangeRates.value))
      
      console.log('Exchange rates updated:', exchangeRates)
    } catch (error) {
      console.error('Failed to update exchange rates:', error)
      
      // 如果获取失败，使用默认汇率
      if (!exchangeRates.value.lastUpdate) {
        exchangeRates.value.USD = 1.0000
        exchangeRates.value.EUR = 0.8234
        exchangeRates.value.CNY = 7.2156
        exchangeRates.value.JPY = 149.85
        exchangeRates.value.lastUpdate = new Date().toISOString()
        exchangeRates.value.source = 'Default Rates'
      }
    }
  }
  
  /**
   * 货币转换
   * @param {number} amount - 金额
   * @param {string} fromCurrency - 源货币
   * @param {string} toCurrency - 目标货币
   * @returns {number} 转换后的金额
   */
  const convertCurrency = (amount, fromCurrency, toCurrency) => {
    if (fromCurrency === toCurrency) return amount
    
    // 先转换为USD，再转换为目标货币
    const usdAmount = amount / exchangeRates.value[fromCurrency]
    return usdAmount * exchangeRates.value[toCurrency]
  }
  
  /**
   * 格式化货币显示
   * @param {number} amount - 金额
   * @param {string} currency - 货币代码
   * @returns {string} 格式化后的货币字符串
   */
  const formatCurrency = (amount, currency = settings.value.general.currency) => {
    const symbols = {
      USD: '$',
      EUR: '€',
      CNY: '¥',
      JPY: '¥'
    }
    
    const symbol = symbols[currency] || currency
    const decimals = currency === 'JPY' ? 0 : 2
    
    return `${symbol}${amount.toLocaleString('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    })}`
  }
  
  /**
   * 初始化设置存储
   * 加载设置并应用主题
   */
  const initialize = async () => {
    loadSettings()
    
    // 确保settings已正确加载后再应用主题
    if (settings.value && settings.value.general && settings.value.general.theme) {
      applyTheme(settings.value.general.theme)
    } else {
      // 如果设置未正确加载，使用默认主题
      applyTheme('light')
    }
    
    // 加载汇率数据
    const savedRates = localStorage.getItem('exchange-rates')
    if (savedRates) {
      try {
        const rates = JSON.parse(savedRates)
        Object.assign(exchangeRates.value, rates)
      } catch (error) {
        console.error('Failed to load exchange rates:', error)
      }
    }
    
    // 检查汇率是否需要更新（超过1小时）
    const lastUpdate = new Date(exchangeRates.value.lastUpdate)
    const now = new Date()
    const hoursSinceUpdate = (now - lastUpdate) / (1000 * 60 * 60)
    
    if (hoursSinceUpdate > 1 || !exchangeRates.value.lastUpdate) {
      await updateExchangeRates()
    }
    
    // 设置定时更新汇率（每小时）
    setInterval(updateExchangeRates, 60 * 60 * 1000)
  }

  return {
    // 状态
    settings,
    originalSettings,
    saving,
    exchangeRates,
    
    // 计算属性
    hasChanges,
    currentTheme,
    currentLanguage,
    currentCurrency,
    
    // 方法
    loadSettings,
    saveSettings,
    cancelChanges,
    resetSettings,
    applyTheme,
    updateExchangeRates,
    convertCurrency,
    formatCurrency,
    initialize
  }
})
