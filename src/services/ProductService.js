/**
 * 产品数据服务
 * 统一的数据管理层，消除原型中的全局变量和重复代码
 */

import { Product, PLATFORMS, CATEGORIES } from '../types/index.js'
import { z } from 'zod'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export class ProductService {
  constructor() {
    // 使用 Map 而不是 Array，提供 O(1) 查找性能
    this.products = new Map()
    this.watchlist = new Set()
    this._loading = false
    this._error = null
    
    // 嘗試從 API 加載數據，失敗則使用模擬數據
    this._loadFromAPI().catch((error) => {
      console.warn('Failed to load products from API, using mock data:', error)
      this._initMockData()
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
   * 如果 API 數據未加載，返回模擬數據
   */
  getAllProducts() {
    const raw = Array.from(this.products.values())
    console.log(`[ProductService] getAllProducts: ${raw.length} products in cache`)
    
    // 如果正在加載，返回空數組而不是模擬數據（讓調用者等待）
    if (this._loading) {
      console.log('[ProductService] Still loading, returning empty array')
      return []
    }
    
    if (raw.length === 0) {
      // 如果沒有數據且沒有錯誤，可能是 API 加載失敗，返回模擬數據
      if (this._error) {
        console.warn('[ProductService] No products and has error, returning mock data')
        return this._getMockProducts()
      }
      // 如果沒有錯誤但也沒有數據，可能是還在加載，返回空數組
      console.log('[ProductService] No products yet, returning empty array')
      return []
    }
    
    const parsed = ProductsSchema.safeParse(raw)
    if (!parsed.success) {
      console.warn('[ProductService] Invalid products payload, using mock data')
      return this._getMockProducts()
    }
    return parsed.data
  }
  
  /**
   * 獲取模擬產品數據（用於後備）
   */
  _getMockProducts() {
    const mock = Array.from(this.products.values())
    if (mock.length === 0) {
      this._initMockData()
      return Array.from(this.products.values())
    }
    return mock
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

  /**
   * 初始化模拟数据
   * 使用正确的数据结构，而不是原型中的数组索引映射
   */
  _initMockData() {
    const mockProducts = [
      {
        id: 'prod-001',
        title: '无线蓝牙耳机 Pro Max',
        platform: PLATFORMS.AMAZON,
        price: 29.99,
        marginRate: 24.5,
        competitionScore: 32,
        category: CATEGORIES.ELECTRONICS,
        description: '高品质无线耳机，支持主动降噪',
        tags: ['蓝牙', '降噪', '长续航'],
        imageUrl: 'https://via.placeholder.com/200x200?text=耳机'
      },
      {
        id: 'prod-002', 
        title: '智能手表运动版',
        platform: PLATFORMS.SHOPEE,
        price: 39.99,
        marginRate: 18.2,
        competitionScore: 48,
        category: CATEGORIES.ELECTRONICS,
        description: '多功能智能手表，健康监测',
        tags: ['智能', '运动', '健康'],
        imageUrl: 'https://via.placeholder.com/200x200?text=手表'
      },
      {
        id: 'prod-003',
        title: '便携式充电宝',
        platform: PLATFORMS.LAZADA,
        price: 24.50,
        marginRate: 29.1,
        competitionScore: 27,
        category: CATEGORIES.ELECTRONICS,
        description: '大容量快充移动电源',
        tags: ['充电', '便携', '快充'],
        imageUrl: 'https://via.placeholder.com/200x200?text=充电宝'
      },
      {
        id: 'prod-004',
        title: '无线充电器',
        platform: PLATFORMS.AMAZON,
        price: 33.00,
        marginRate: 21.8,
        competitionScore: 41,
        category: CATEGORIES.ELECTRONICS,
        description: '支持多设备同时充电',
        tags: ['无线', '充电', '多设备'],
        imageUrl: 'https://via.placeholder.com/200x200?text=充电器'
      },
      {
        id: 'prod-005',
        title: '蓝牙音箱迷你版',
        platform: PLATFORMS.EBAY,
        price: 27.90,
        marginRate: 26.3,
        competitionScore: 38,
        category: CATEGORIES.ELECTRONICS,
        description: '小巧便携，音质出色',
        tags: ['蓝牙', '音箱', '便携'],
        imageUrl: 'https://via.placeholder.com/200x200?text=音箱'
      },
      {
        id: 'prod-006',
        title: '手机支架桌面版',
        platform: PLATFORMS.SHOPEE,
        price: 31.90,
        marginRate: 22.7,
        competitionScore: 35,
        category: CATEGORIES.ELECTRONICS,
        description: '可调节角度，稳固耐用',
        tags: ['支架', '桌面', '可调节'],
        imageUrl: 'https://via.placeholder.com/200x200?text=支架'
      },
      {
        id: 'prod-007',
        title: '智能家居摄像头',
        platform: PLATFORMS.AMAZON,
        price: 45.99,
        marginRate: 32.1,
        competitionScore: 29,
        category: CATEGORIES.ELECTRONICS,
        description: '高清夜视，远程监控',
        tags: ['智能', '监控', '夜视'],
        imageUrl: 'https://via.placeholder.com/200x200?text=摄像头'
      },
      {
        id: 'prod-008',
        title: 'LED台灯护眼版',
        platform: PLATFORMS.LAZADA,
        price: 28.50,
        marginRate: 25.8,
        competitionScore: 33,
        category: CATEGORIES.HOME,
        description: '护眼光源，多档调节',
        tags: ['LED', '护眼', '台灯'],
        imageUrl: 'https://via.placeholder.com/200x200?text=台灯'
      }
    ]

    mockProducts.forEach(data => {
      this.addProduct(data)
    })
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