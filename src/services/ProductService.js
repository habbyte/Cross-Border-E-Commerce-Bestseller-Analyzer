/**
 * 产品数据服务
 * 统一的数据管理层，消除原型中的全局变量和重复代码
 */

import { Product } from '../types/index.js'
import { z } from 'zod'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export class ProductService {
  constructor() {
    // 使用 Map 而不是 Array，提供 O(1) 查找性能
    this.products = new Map()
    this.watchlist = new Set()
    this._loading = false
    this._error = null
    
    // 初始化時直接從資料庫 API 加載數據
    this._loadFromAPI().catch((error) => {
      console.error('[ProductService] Failed to load products from database API:', error)
      this._error = error.message
      // 不再使用模擬數據，保持空狀態
    })
  }
  
  /**
   * 從 API 加載產品數據（支持分頁）
   */
  async _loadFromAPI() {
    if (this._loading) return
    this._loading = true
    this._error = null
    
    try {
      // 清空現有數據
      this.products.clear()
      
      // 後端 API limit 最大值為 100，需要分頁獲取
      const limit = 100
      let skip = 0
      let hasMore = true
      let totalLoaded = 0
      
      while (hasMore) {
        const url = `${API_BASE_URL}/api/products/?status=active&limit=${limit}&skip=${skip}`
        console.log(`[ProductService] Loading products from: ${url}`)
        
        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        })
        
        if (!response.ok) {
          const errorText = await response.text()
          console.error(`[ProductService] API error ${response.status}:`, errorText)
          throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`)
        }
        
        const data = await response.json()
        const batchSize = Array.isArray(data) ? data.length : 0
        console.log(`[ProductService] Received ${batchSize} products from API (skip=${skip})`)
        
        // 轉換 API 數據為內部格式
        if (Array.isArray(data) && data.length > 0) {
          data.forEach(product => {
            try {
              const normalized = this._normalizeApiProduct(product)
              this.products.set(normalized.id, normalized)
              totalLoaded++
            } catch (err) {
              console.warn(`[ProductService] Failed to normalize product:`, product, err)
            }
          })
          
          // 如果返回的數據少於 limit，說明已經是最後一頁
          hasMore = batchSize === limit
          skip += limit
        } else {
          hasMore = false
        }
        
        // 安全限制：最多加載 1000 個產品（10 頁）
        if (totalLoaded >= 1000) {
          console.warn(`[ProductService] Reached maximum load limit (1000 products)`)
          hasMore = false
        }
      }
      
      console.log(`[ProductService] Successfully loaded ${this.products.size} products from API`)
    } catch (error) {
      this._error = error.message
      console.error('[ProductService] Failed to load products from API:', error)
      throw error
    } finally {
      this._loading = false
    }
  }
  
  /**
   * 將 API 產品格式轉換為內部格式
   */
  _normalizeApiProduct(apiProduct) {
    return {
      id: apiProduct.id,
      // 同時提供 title 和 name，確保前端兼容性
      title: apiProduct.title || '',
      name: apiProduct.title || apiProduct.name || '',  // 前端使用 name
      platform: apiProduct.platform || 'amazon',
      price: apiProduct.price || 0,
      formattedPrice: apiProduct.formattedPrice || `$${apiProduct.price || 0}`,
      marginRate: apiProduct.marginRate || 0,
      competitionScore: apiProduct.competitionScore || 50,
      competitionLevel: apiProduct.competitionLevel || 'medium',
      competition: apiProduct.competitionLevel || 'medium',  // 兼容舊字段名
      category: apiProduct.category || 'Electronics',
      imageUrl: apiProduct.imageUrl,
      description: apiProduct.description,
      rating: apiProduct.rating,
      reviewCount: apiProduct.reviewCount,
      sales: apiProduct.reviewCount || 0,  // 使用 reviewCount 作為 sales 的近似值
      url: apiProduct.productUrl,
      tags: apiProduct.tags || [],
      productDetails: apiProduct.productDetails,
      aboutThisItem: apiProduct.aboutThisItem,
      colorOptions: apiProduct.colorOptions,
      sizeOptions: apiProduct.sizeOptions,
      status: 'active',
      stock: 0,
      profit: Math.round(apiProduct.marginRate || 0),
    }
  }

  /**
   * 添加商品
   * 统一的数据验证和存储逻辑
   */
  addProduct(productData) {
    try {
      const product = new Product(productData)
      this.products.set(product.id, product)
      return product
    } catch (error) {
      console.error('Failed to add product:', error.message)
      throw error
    }
  }

  /**
   * 從 API 獲取單個產品
   * 如果本地沒有，則從 API 獲取
   */
  async fetchProductFromAPI(id) {
    try {
      // 移除可能的 prod- 前綴
      const productId = id.startsWith('prod-') ? id : `prod-${id}`
      const url = `${API_BASE_URL}/api/products/${productId}`
      console.log(`[ProductService] Fetching product from API: ${url}`)
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error(`Product not found: ${id}`)
        }
        const errorText = await response.text()
        console.error(`[ProductService] API error ${response.status}:`, errorText)
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`)
      }
      
      const data = await response.json()
      console.log(`[ProductService] Received product from API:`, data)
      
      // 轉換並存儲到本地
      const normalized = this._normalizeApiProduct(data)
      this.products.set(normalized.id, normalized)
      
      return normalized
    } catch (error) {
      console.error(`[ProductService] Failed to fetch product ${id} from API:`, error)
      throw error
    }
  }

  /**
   * 获取商品
   * 先從本地查找，如果沒有則從 API 獲取
   */
  async getProduct(id) {
    // 先從本地查找
    const product = this.products.get(id)
    if (product) {
      const parsed = ProductSchema.safeParse(product)
      if (parsed.success) {
        return parsed.data
      }
    }
    
    // 本地沒有，從 API 獲取
    try {
      return await this.fetchProductFromAPI(id)
    } catch (error) {
      throw new Error(`Product not found: ${id}`)
    }
  }

  /**
   * 获取所有商品
   * 直接從資料庫 API 獲取，不返回模擬數據
   */
  getAllProducts() {
    const raw = Array.from(this.products.values())
    console.log(`[ProductService] getAllProducts: ${raw.length} products in cache`)
    
    // 如果正在加載，返回空數組（讓調用者等待）
    if (this._loading) {
      console.log('[ProductService] Still loading, returning empty array')
      return []
    }
    
    // 如果沒有數據，返回空數組（不再使用模擬數據）
    if (raw.length === 0) {
      if (this._error) {
        console.warn('[ProductService] No products loaded from database API:', this._error)
      } else {
        console.log('[ProductService] No products yet, returning empty array')
      }
      return []
    }
    
    // 驗證數據格式
    const parsed = ProductsSchema.safeParse(raw)
    if (!parsed.success) {
      console.error('[ProductService] Invalid products payload:', parsed.error)
      // 數據格式錯誤時返回空數組，而不是模擬數據
      return []
    }
    return parsed.data
  }

  /**
   * 搜索商品
   * 使用 SearchFilter 统一过滤逻辑
   */
  searchProducts(filter) {
    return this.getAllProducts().filter(product => filter.matches(product))
  }

  /**
   * 获取热门商品
   * 基于利润率和竞争度的综合评分
   */
  getTopProducts(limit = 6) {
    return this.getAllProducts()
      .sort((a, b) => {
        // 综合评分：利润率权重 0.6，竞争度权重 0.4（越低越好）
        const scoreA = a.marginRate * 0.6 + (100 - a.competitionScore) * 0.4
        const scoreB = b.marginRate * 0.6 + (100 - b.competitionScore) * 0.4
        return scoreB - scoreA
      })
      .slice(0, limit)
  }

  /**
   * 添加到监控列表
   */
  addToWatchlist(productId) {
    if (!this.products.has(productId)) {
      throw new Error(`Cannot watch non-existent product: ${productId}`)
    }
    this.watchlist.add(productId)
  }

  /**
   * 从监控列表移除
   */
  removeFromWatchlist(productId) {
    this.watchlist.delete(productId)
  }

  /**
   * 获取监控列表
   */
  getWatchlist() {
    return Array.from(this.watchlist)
      .map(id => this.products.get(id))
      .filter(Boolean) // 防御性编程：过滤掉可能的 undefined
  }

  /**
   * 获取统计数据
   * 替代原型中硬编码的 KPI 数据
   */
  getStatistics() {
    const products = this.getAllProducts()
    
    if (products.length === 0) {
      return {
        totalProducts: 0,
        averageMargin: 0,
        alertCount: 0,
        trendDirection: 'neutral'
      }
    }

    const totalMargin = products.reduce((sum, p) => sum + p.marginRate, 0)
    const averageMargin = totalMargin / products.length
    
    // 模拟告警数量（实际项目中应该基于真实的监控规则）
    const alertCount = products.filter(p => p.competitionScore > 50).length
    
    return {
      totalProducts: products.length,
      averageMargin: averageMargin.toFixed(1),
      alertCount,
      trendDirection: averageMargin > 20 ? 'up' : 'down'
    }
  }

}

/**
 * zod 运行时校验：产品数据结构
 * 不改变业务字段，仅用于防御性校验与默认值
 */
const ProductSchema = z.object({
  id: z.string(),
  title: z.string().default(''),
  platform: z.string().default(''),
  price: z.number().nonnegative().default(0),
  marginRate: z.number().nonnegative().default(0),
  competitionScore: z.number().min(0).max(100).default(0),
  category: z.string().default('Electronics'),
  imageUrl: z.string().nullable().optional(),
  description: z.string().default(''),
  tags: z.array(z.string()).default([]),
  createdAt: z.any().optional(),
  status: z.string().default('active'),
  stock: z.number().int().nonnegative().default(0),
  profit: z.number().default(0),
  formattedPrice: z.string().optional()
})

const ProductsSchema = z.array(ProductSchema)

// 单例模式 - 全局唯一的数据服务实例
export const productService = new ProductService()