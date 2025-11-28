/**
 * 产品数据服务
 * 统一的数据管理层，消除原型中的全局变量和重复代码
 */

import { Product, PLATFORMS, CATEGORIES } from '../types/index.js'
import { z } from 'zod'

export class ProductService {
  constructor() {
    // 使用 Map 而不是 Array，提供 O(1) 查找性能
    this.products = new Map()
    this.watchlist = new Set()
    
    // 初始化模拟数据 - 但用正确的数据结构
    this._initMockData()
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
   * 获取商品
   * 明确的错误处理，不使用原型中的 "聪明" fallback
   */
  getProduct(id) {
    const product = this.products.get(id)
    if (!product) {
      throw new Error(`Product not found: ${id}`)
    }
    const parsed = ProductSchema.safeParse(product)
    if (!parsed.success) {
      throw new Error('Invalid product payload')
    }
    return parsed.data
  }

  /**
   * 获取所有商品
   */
  getAllProducts() {
    const raw = Array.from(this.products.values())
    const parsed = ProductsSchema.safeParse(raw)
    if (!parsed.success) {
      throw new Error('Invalid products payload')
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