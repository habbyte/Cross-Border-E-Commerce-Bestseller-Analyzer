/**
 * DemoData 服务用于在空状态时提供示例商品
 * 数据结构与 ProductStore 中的商品保持一致
 * @typedef {import('../types/index.js').Product} Product
 */

const SAMPLE_PRODUCTS = [
  {
    id: 'sample-001',
    title: '多功能智能手表',
    platform: 'amazon',
    price: 329,
    formattedPrice: '¥329.00',
    marginRate: 28,
    competitionScore: 32,
    category: 'Electronics',
    status: 'active',
    stock: 56,
    profit: 24,
    tags: ['智能', '运动', '健康'],
    imageUrl: 'https://via.placeholder.com/200x200?text=%E6%99%BA%E8%83%BD%E6%89%8B%E8%A1%A8'
  },
  {
    id: 'sample-002',
    title: '降噪蓝牙耳机',
    platform: 'shopee',
    price: 259,
    formattedPrice: '¥259.00',
    marginRate: 26,
    competitionScore: 28,
    category: 'Electronics',
    status: 'active',
    stock: 74,
    profit: 21,
    tags: ['蓝牙', '降噪', '续航'],
    imageUrl: 'https://via.placeholder.com/200x200?text=%E9%99%8D%E5%99%AA%E8%80%B3%E6%9C%BA'
  },
  {
    id: 'sample-003',
    title: '人体工学办公椅',
    platform: 'lazada',
    price: 499,
    formattedPrice: '¥499.00',
    marginRate: 32,
    competitionScore: 36,
    category: 'Home',
    status: 'active',
    stock: 38,
    profit: 27,
    tags: ['办公', '舒适', '支撑'],
    imageUrl: 'https://via.placeholder.com/200x200?text=%E5%8A%9E%E5%85%AC%E6%A4%85'
  },
  {
    id: 'sample-004',
    title: '户外运动水杯',
    platform: 'ebay',
    price: 129,
    formattedPrice: '¥129.00',
    marginRate: 22,
    competitionScore: 30,
    category: 'Sports',
    status: 'active',
    stock: 120,
    profit: 18,
    tags: ['运动', '保温', '便携'],
    imageUrl: 'https://via.placeholder.com/200x200?text=%E6%B0%B4%E6%9D%AF'
  },
  {
    id: 'sample-005',
    title: 'USB-C 多口扩展坞',
    platform: 'aliexpress',
    price: 219,
    formattedPrice: '¥219.00',
    marginRate: 24,
    competitionScore: 34,
    category: 'Electronics',
    status: 'active',
    stock: 64,
    profit: 19,
    tags: ['扩展坞', 'USB-C', '外设'],
    imageUrl: 'https://via.placeholder.com/200x200?text=USB-C%E6%89%A9%E5%B1%95%E5%9D%9E'
  }
]

/**
 * 生成示例数据副本，避免直接修改原数组
 * @returns {Array<Record<string, any>>}
 */
const cloneSampleProducts = () =>
  SAMPLE_PRODUCTS.map((item) => ({
    ...item,
    tags: Array.isArray(item.tags) ? [...item.tags] : []
  }))

export const DemoData = {
  /**
   * 获取示例商品列表
   * @returns {Array<Record<string, any>>}
   */
  getSample() {
    return cloneSampleProducts()
  }
}
