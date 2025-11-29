/**
 * 核心数据模型定义
 * 遵循 Linus "好品味" 原则：清晰的数据结构，消除特殊情况
 */

// 平台枚举
export const PLATFORMS = {
  AMAZON: 'amazon',
  SHOPEE: 'shopee',
  LAZADA: 'lazada',
  EBAY: 'ebay',
  ALIEXPRESS: 'aliexpress'
}

// 商品类目枚举
export const CATEGORIES = {
  ELECTRONICS: 'electronics',
  HOME: 'home',
  BEAUTY: 'beauty',
  FASHION: 'fashion'
}

// 竞争度等级
export const COMPETITION_LEVELS = {
  LOW: 'low',      // < 30
  MEDIUM: 'medium', // 30-60
  HIGH: 'high'     // > 60
}

/**
 * 商品数据模型
 * 统一的数据结构，避免原型中的数组索引映射混乱
 */
export class Product {
  constructor({
    id,
    title,
    platform,
    price,
    marginRate,
    competitionScore,
    category = CATEGORIES.ELECTRONICS,
    imageUrl = null,
    description = '',
    tags = [],
    createdAt = new Date()
  }) {
    // 数据验证 - 不允许无效数据进入系统
    if (!id || !title || !platform || price < 0 || marginRate < 0) {
      throw new Error('Invalid product data: missing required fields')
    }
    
    this.id = id
    this.title = title
    this.platform = platform
    this.price = Number(price)
    this.marginRate = Number(marginRate)
    this.competitionScore = Number(competitionScore)
    this.category = category
    this.imageUrl = imageUrl
    this.description = description
    this.tags = [...tags]
    this.createdAt = createdAt
  }

  /**
   * 获取竞争度等级
   * 消除原型中的条件判断分支
   */
  get competitionLevel() {
    if (this.competitionScore < 30) return COMPETITION_LEVELS.LOW
    if (this.competitionScore < 60) return COMPETITION_LEVELS.MEDIUM
    return COMPETITION_LEVELS.HIGH
  }

  /**
   * 获取格式化价格
   * 根据当前设置的货币进行转换和格式化
   */
  get formattedPrice() {
    // 尝试获取设置store，如果不存在则使用默认USD格式
    try {
      // 检查是否在Vue应用上下文中
      if (typeof window !== 'undefined' && window.__VUE_APP__) {
        // 从全局状态获取设置
        const settingsData = localStorage.getItem('app-settings')
        if (settingsData) {
          const settings = JSON.parse(settingsData)
          const currency = settings.general?.currency || 'USD'
          
          // 获取汇率数据
          const exchangeRatesData = localStorage.getItem('exchange-rates')
          if (exchangeRatesData) {
            const exchangeRates = JSON.parse(exchangeRatesData)
            
            // 转换货币
            const usdAmount = this.price / (exchangeRates.USD || 1)
            const convertedAmount = usdAmount * (exchangeRates[currency] || 1)
            
            // 格式化显示
            const symbols = {
              USD: '$',
              EUR: '€',
              CNY: '¥',
              JPY: '¥'
            }
            
            const symbol = symbols[currency] || '$'
            const decimals = currency === 'JPY' ? 0 : 2
            
            return `${symbol}${convertedAmount.toFixed(decimals)}`
          }
        }
      }
      
      // 如果获取设置失败，使用默认USD格式
      return `$${this.price.toFixed(2)}`
    } catch (error) {
      // 如果获取设置失败，使用默认USD格式
      return `$${this.price.toFixed(2)}`
    }
  }

  /**
   * 获取格式化利润率
   */
  get formattedMarginRate() {
    return `${this.marginRate.toFixed(1)}%`
  }

  /**
   * 判断是否为优质商品
   * 统一的业务逻辑，避免散落各处的判断
   */
  get isHighQuality() {
    return this.marginRate > 20 && this.competitionScore < 40
  }
}

/**
 * 搜索过滤器
 * 替代原型中混乱的DOM查询
 */
export class SearchFilter {
  constructor({
    keyword = '',
    platform = 'all',
    category = 'all',
    minMargin = 0,
    maxCompetition = 100
  } = {}) {
    this.keyword = keyword.trim()
    this.platform = platform
    this.category = category
    this.minMargin = Number(minMargin)
    this.maxCompetition = Number(maxCompetition)
  }

  /**
   * 检查商品是否匹配过滤条件
   * 统一的过滤逻辑，消除特殊情况
   */
  matches(product) {
    // 支持 name 和 title 字段（確保兼容性）
    const productName = product.name || product.title || ''
    if (this.keyword && !productName.toLowerCase().includes(this.keyword.toLowerCase())) {
      return false
    }
    
    if (this.platform !== 'all' && product.platform !== this.platform) {
      return false
    }
    
    if (this.category !== 'all' && product.category !== this.category) {
      return false
    }
    
    if (product.marginRate < this.minMargin) {
      return false
    }
    
    if (product.competitionScore > this.maxCompetition) {
      return false
    }
    
    return true
  }
}

/**
 * 监控规则
 * 替代原型中硬编码的告警逻辑
 */
export class WatchRule {
  constructor({
    productId,
    priceBelow = null,
    competitionBelow = null,
    marginAbove = null
  }) {
    this.productId = productId
    this.priceBelow = priceBelow
    this.competitionBelow = competitionBelow
    this.marginAbove = marginAbove
  }

  /**
   * 检查是否触发告警
   */
  checkAlert(product) {
    const alerts = []
    
    if (this.priceBelow && product.price < this.priceBelow) {
      alerts.push(`价格低于 ${this.priceBelow}`)
    }
    
    if (this.competitionBelow && product.competitionScore < this.competitionBelow) {
      alerts.push(`竞争度降至 ${product.competitionScore}`)
    }
    
    if (this.marginAbove && product.marginRate > this.marginAbove) {
      alerts.push(`利润率超过 ${this.marginAbove}%`)
    }
    
    return alerts
  }
}
