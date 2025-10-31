<template>
  <div class="settings">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">⚙️ {{ $t('settings.title') }}</h1>
      <p class="page-subtitle">{{ $t('settings.subtitle') }}</p>
    </div>
    
    <!-- 设置内容 -->
    <div class="settings-content">
      <!-- 通用设置 -->
      <div class="settings-section">
        <h2 class="section-title">🌐 {{ $t('settings.general.title') }}</h2>
        <div class="settings-grid">
          <div class="setting-item">
            <!-- 语言选择已冻结，恢复流程详见 docs/i18n-reenable.md -->
            <label class="setting-label">{{ $t('settings.general.language') }}</label>
            <select
              v-model="currentLanguage"
              class="form-select"
              aria-disabled="true"
              disabled
              @change="handleLanguageChange"
            >
              <option value="zh-CN">{{ $t('common.languages.zh-CN') }}</option>
              <option value="zh-TW" disabled>{{ $t('common.languages.zh-TW') }}</option>
              <option value="en" disabled>{{ $t('common.languages.en') }}</option>
            </select>
          </div>
          
          <div class="setting-item">
            <label class="setting-label">{{ $t('settings.general.theme') }}</label>
            <div class="theme-selector">
              <label class="radio-option">
                <input 
                  type="radio" 
                  v-model="settingsStore.settings.general.theme" 
                  value="light"
                  @change="handleThemeChange"
                />
                <span class="radio-label">{{ $t('settings.theme.light') }}</span>
              </label>
              <label class="radio-option">
                <input 
                  type="radio" 
                  v-model="settingsStore.settings.general.theme" 
                  value="dark"
                  @change="handleThemeChange"
                />
                <span class="radio-label">{{ $t('settings.theme.dark') }}</span>
              </label>
              <label class="radio-option">
                <input 
                  type="radio" 
                  v-model="settingsStore.settings.general.theme" 
                  value="auto"
                  @change="handleThemeChange"
                />
                <span class="radio-label">{{ $t('settings.theme.auto') }}</span>
              </label>
            </div>
          </div>
          
          <div class="setting-item">
            <label class="setting-label">{{ $t('settings.general.currency') }}</label>
            <select v-model="settingsStore.settings.general.currency" class="form-select" @change="handleCurrencyChange">
              <option value="USD">{{ $t('settings.currency.usd') }}</option>
              <option value="EUR">{{ $t('settings.currency.eur') }}</option>
              <option value="GBP">{{ $t('settings.currency.gbp') }}</option>
              <option value="JPY">{{ $t('settings.currency.jpy') }}</option>
              <option value="CNY">{{ $t('settings.currency.cny') }}</option>
            </select>
          </div>
        </div>
      </div>
      
      <!-- 数据设置 -->
      <div class="settings-section">
        <h2 class="section-title">📊 {{ $t('settings.data.title') }}</h2>
        <div class="settings-grid">
          <div class="setting-item">
            <label class="setting-label">{{ $t('settings.data.defaultPlatform') }}</label>
            <select v-model="settingsStore.settings.defaultPlatform" class="form-select">
              <option value="amazon">{{ $t('settings.platforms.amazon') }}</option>
              <option value="ebay">{{ $t('settings.platforms.ebay') }}</option>
              <option value="shopee">{{ $t('settings.platforms.shopee') }}</option>
              <option value="lazada">{{ $t('settings.platforms.lazada') }}</option>
              <option value="aliexpress">{{ $t('settings.platforms.aliexpress') }}</option>
            </select>
          </div>
          
          <div class="setting-item">
            <label class="setting-label">{{ $t('settings.data.pageSize') }}</label>
            <select v-model="settingsStore.settings.pageSize" class="form-select">
              <option value="10">10</option>
              <option value="20">20</option>
              <option value="50">50</option>
              <option value="100">100</option>
            </select>
          </div>
          
          <div class="setting-item">
            <label class="setting-label">{{ $t('settings.data.autoRefresh') }}</label>
            <div class="toggle-switch">
              <input 
                type="checkbox" 
                id="autoRefresh" 
                v-model="settingsStore.settings.autoRefresh"
              />
              <label for="autoRefresh" class="toggle-label"></label>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 通知设置 -->
      <div class="settings-section">
        <h2 class="section-title">🔔 {{ $t('settings.notifications.title') }}</h2>
        <div class="settings-grid">
          <div class="setting-item">
            <label class="setting-label">{{ $t('settings.notifications.priceChange') }}</label>
            <div class="input-group">
              <input 
                type="number" 
                v-model="settingsStore.settings.alerts.priceChangeThreshold"
                class="form-input"
                min="1"
                max="100"
              />
              <span class="input-suffix">%</span>
            </div>
          </div>
          
          <div class="setting-item">
            <label class="setting-label">{{ $t('settings.notifications.salesChange') }}</label>
            <div class="input-group">
              <input 
                type="number" 
                v-model="settingsStore.settings.alerts.salesChangeThreshold"
                class="form-input"
                min="1"
                max="1000"
              />
              <span class="input-suffix">%</span>
            </div>
          </div>
          
          <div class="setting-item">
            <label class="setting-label">{{ $t('settings.notifications.email') }}</label>
            <div class="toggle-switch">
              <input 
                type="checkbox" 
                id="emailNotification" 
                v-model="settingsStore.settings.alerts.emailNotification"
              />
              <label for="emailNotification" class="toggle-label"></label>
            </div>
          </div>
          
          <div class="setting-item" v-if="settingsStore.settings.alerts.emailNotification">
            <label class="setting-label">{{ $t('settings.notifications.emailAddress') }}</label>
            <input 
              type="email" 
              v-model="settingsStore.settings.alerts.email"
              class="form-input"
              :placeholder="$t('settings.notifications.emailPlaceholder')"
            />
          </div>
        </div>
      </div>
      
      <!-- 汇率信息 -->
      <div class="settings-section">
        <h2 class="section-title">💱 {{ $t('settings.exchangeRates.title') }}</h2>
        <div class="exchange-rates-info">
          <div class="rates-header">
            <p class="rates-description">{{ $t('settings.exchangeRates.description') }}</p>
            <div class="rates-meta">
              <span class="last-update">
                {{ $t('settings.exchangeRates.lastUpdate') }}: 
                {{ formatDate(settingsStore.exchangeRates.lastUpdate) }}
              </span>
              <span class="data-source">
                {{ $t('settings.exchangeRates.source') }}: {{ settingsStore.exchangeRates.source }}
              </span>
            </div>
          </div>
          
          <div class="rates-grid">
            <div 
              v-for="(rate, currency) in settingsStore.exchangeRates.rates" 
              :key="currency"
              class="rate-item"
            >
              <span class="currency-code">{{ currency }}</span>
              <span class="rate-value">{{ rate.toFixed(4) }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 操作按钮 -->
      <div class="settings-actions">
        <button 
          @click="saveSettings" 
          class="btn btn-primary"
          :disabled="settingsStore.saving || !settingsStore.hasChanges"
        >
          <span v-if="settingsStore.saving">{{ $t('settings.actions.saving') }}</span>
          <span v-else>{{ $t('settings.actions.save') }}</span>
        </button>
        
        <button 
          @click="cancelChanges" 
          class="btn btn-secondary"
          :disabled="settingsStore.saving || !settingsStore.hasChanges"
        >
          {{ $t('settings.actions.cancel') }}
        </button>
        
        <button @click="clearCache" class="btn btn-warning">
          {{ $t('settings.actions.clearCache') }}
        </button>
        
        <button @click="exportData" class="btn btn-info">
          {{ $t('settings.actions.export') }}
        </button>
        
        <button @click="resetSettings" class="btn btn-danger">
          {{ $t('settings.actions.reset') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { useSettingsStore } from '@/stores/useSettingsStore'
import { useI18n } from 'vue-i18n'
import { useLanguageStore } from '@/stores/useLanguageStore'
import { computed } from 'vue'

/**
 * Settings.vue - 应用设置页面组件
 * 
 * 功能�? * - 通用设置（语言、主题、货币）
 * - 数据设置（默认平台、分页大小、自动刷新）
 * - 通知设置（价格变化阈值、销量变化阈值、邮件通知�? * - 汇率信息显示
 * - 设置的保存、取消、重置、导出功�? * - 缓存清理功能
 */
export default {
  name: 'Settings',
  setup() {
    const settingsStore = useSettingsStore()
    const { t, locale } = useI18n()
    const langStore = useLanguageStore()
    
    const currentLanguage = computed({
      get: () => langStore.locale,
      set: () => {
        langStore.setLocale(langStore.locale)
      }
    })
    locale.value = langStore.locale
    if (settingsStore.settings?.general) {
      settingsStore.settings.general.language = langStore.locale
    }
    
    /**
     * 语言切换处理函数
     * 当前版本只同步锁定语言，保留结构以便未来恢�?     */
    const handleLanguageChange = () => {
      if (settingsStore.settings?.general) {
        settingsStore.settings.general.language = langStore.locale
      }
      console.info('[i18n] 多语言切换暂时禁用，当前仅提供简体中文。')
    }

    /**
     * 货币切换处理函数
     * 使用 settings.value 读取当前货币，避免未解包 ref 导致 undefined
     */
    const handleCurrencyChange = () => {
      const nextCurrency = settingsStore.settings.value.general.currency
      // 若有价格等需要联动更新的逻辑，可在此触发相关刷新
    }
    
    /**
     * 主题切换处理函数
     * 读取当前选择的主题并显式传给 applyTheme，避�?undefined 导致样式错乱
     */
    const handleThemeChange = () => {
      const theme = settingsStore.settings.value.general.theme
      settingsStore.applyTheme(theme)
    }
    
    /**
     * 保存设置
     */
    const saveSettings = async () => {
      try {
        await settingsStore.saveSettings()
        alert(t('settings.messages.saved'))
      } catch (error) {
        console.error('Failed to save settings:', error)
        alert(t('settings.messages.saveFailed'))
      }
    }
    
    /**
     * 取消更改
     */
    const cancelChanges = () => {
      settingsStore.cancelChanges()
    }
    
    /**
     * 清除缓存
     */
    const clearCache = async () => {
      if (confirm(t('settings.messages.clearCacheConfirm'))) {
        try {
          // 清除商品缓存
          localStorage.removeItem('product-cache')
          
          // 清除搜索历史
          localStorage.removeItem('search-history')
          
          // 清除用户偏好缓存
          localStorage.removeItem('user-preferences')
          
          alert(t('settings.messages.cacheCleared'))
        } catch (error) {
          console.error('Failed to clear cache:', error)
          alert(t('settings.messages.clearCacheFailed'))
        }
      }
    }
    
    /**
     * 导出数据
     */
    const exportData = () => {
      const data = {
        settings: settingsStore.settings,
        exportDate: new Date().toISOString(),
        version: '1.0'
      }
      
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `settings-${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }
    
    /**
     * 重置设置
     */
    const resetSettings = () => {
      if (confirm(t('settings.messages.resetConfirm'))) {
        settingsStore.resetToDefaults()
        alert(t('settings.messages.resetSuccess'))
      }
    }
    
    /**
     * 格式化日�?     */
    const formatDate = (dateString) => {
      // 始终使用当前全局 locale
      const currentLocale = langStore.locale
      return new Date(dateString).toLocaleString(currentLocale)
    }
    
    return {
      settingsStore,
      currentLanguage,
      handleLanguageChange,
      handleThemeChange,
      handleCurrencyChange,
      saveSettings,
      cancelChanges,
      clearCache,
      exportData,
      resetSettings,
      formatDate
    }
  }
}
</script>

<style scoped>
.settings {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.page-header {
  text-align: center;
  margin-bottom: 3rem;
}

.page-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.page-subtitle {
  font-size: 1.1rem;
  color: var(--text-secondary);
  margin: 0;
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
}

.settings-section {
  background: var(--bg-secondary);
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.setting-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.setting-label {
  font-weight: 500;
  color: var(--text-primary);
  font-size: 0.95rem;
}

.form-select,
.form-input {
  padding: 0.75rem;
  border: 2px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 0.95rem;
  transition: all 0.2s ease;
}

.form-select:focus,
.form-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.theme-selector {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.radio-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.5rem 1rem;
  border: 2px solid var(--border-color);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.radio-option:hover {
  border-color: var(--primary-color);
  background: rgba(59, 130, 246, 0.05);
}

.radio-option input[type="radio"] {
  margin: 0;
}

.radio-label {
  font-size: 0.9rem;
  color: var(--text-primary);
}

.toggle-switch {
  position: relative;
  display: inline-block;
}

.toggle-switch input[type="checkbox"] {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-label {
  display: block;
  width: 50px;
  height: 24px;
  background: var(--border-color);
  border-radius: 12px;
  cursor: pointer;
  position: relative;
  transition: background 0.2s ease;
}

.toggle-label::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  transition: transform 0.2s ease;
}

.toggle-switch input[type="checkbox"]:checked + .toggle-label {
  background: var(--primary-color);
}

.toggle-switch input[type="checkbox"]:checked + .toggle-label::after {
  transform: translateX(26px);
}

.input-group {
  display: flex;
  align-items: center;
}

.input-suffix {
  padding: 0.75rem;
  background: var(--bg-tertiary);
  border: 2px solid var(--border-color);
  border-left: none;
  border-radius: 0 8px 8px 0;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.input-group .form-input {
  border-radius: 8px 0 0 8px;
  border-right: none;
}

.exchange-rates-info {
  background: var(--bg-primary);
  border-radius: 8px;
  padding: 1.5rem;
  border: 1px solid var(--border-color);
}

.rates-header {
  margin-bottom: 1.5rem;
}

.rates-description {
  color: var(--text-secondary);
  margin-bottom: 1rem;
}

.rates-meta {
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;
  font-size: 0.85rem;
  color: var(--text-tertiary);
}

.rates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 1rem;
}

.rate-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: var(--bg-secondary);
  border-radius: 6px;
  border: 1px solid var(--border-color);
}

.currency-code {
  font-weight: 600;
  color: var(--text-primary);
}

.rate-value {
  font-family: 'Courier New', monospace;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.settings-actions {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  justify-content: center;
  padding-top: 2rem;
  border-top: 1px solid var(--border-color);
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.95rem;
  min-width: 120px;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--primary-color);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-hover);
  transform: translateY(-1px);
}

.btn-secondary {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--bg-quaternary);
}

.btn-warning {
  background: #f59e0b;
  color: white;
}

.btn-warning:hover {
  background: #d97706;
}

.btn-info {
  background: #06b6d4;
  color: white;
}

.btn-info:hover {
  background: #0891b2;
}

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-danger:hover {
  background: #dc2626;
}

@media (max-width: 768px) {
  .settings {
    padding: 1rem;
  }
  
  .settings-grid {
    grid-template-columns: 1fr;
  }
  
  .theme-selector {
    flex-direction: column;
  }
  
  .rates-meta {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .settings-actions {
    flex-direction: column;
  }
  
  .btn {
    width: 100%;
  }
}
</style>
