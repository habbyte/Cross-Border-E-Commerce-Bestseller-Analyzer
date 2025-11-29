import { useI18n } from 'vue-i18n'

/**
 * 推荐理由映射器
 * 根据商品属性生成具备可解释性的理由
 */
const MAX_REASONS = 3

/**
 * 生成推荐理由
 * @param {Record<string, any>} product
 * @returns {Array<{ key: string, values?: Record<string, any> }>}
 */
export function mapReasons(product) {
  const reasons = []
  if (!product || typeof product !== 'object') {
    return reasons
  }

  if (Array.isArray(product.reasons) && product.reasons.length > 0) {
    product.reasons.forEach((reason) => {
      reasons.push({
        key: 'recommendation.reasons.custom',
        values: { text: reason }
      })
    })
  }

  if (typeof product.marginRate === 'number' && product.marginRate >= 25) {
    reasons.push({
      key: 'recommendation.reasons.highMargin',
      values: { value: product.marginRate.toFixed(1) }
    })
  }

  if (typeof product.competitionScore === 'number' && product.competitionScore <= 35) {
    reasons.push({
      key: 'recommendation.reasons.lowCompetition',
      values: { value: product.competitionScore }
    })
  }

  if (typeof product.stock === 'number' && product.stock >= 50) {
    reasons.push({
      key: 'recommendation.reasons.sufficientStock',
      values: { value: product.stock }
    })
  }

  if (Array.isArray(product.tags) && product.tags.length > 0) {
    reasons.push({
      key: 'recommendation.reasons.tagHighlight',
      values: { tag: product.tags[0] }
    })
  }

  if (reasons.length === 0) {
    reasons.push({ key: 'recommendation.reasons.default' })
  }

  return reasons.slice(0, MAX_REASONS)
}

/**
 * 提供带翻译后的推荐理由
 * @param {Record<string, any>} product
 * @returns {Array<string>}
 */
export function useTranslatedReasons(product) {
  const { t } = useI18n()
  return mapReasons(product).map((reason) => t(reason.key, reason.values ?? {}))
}
