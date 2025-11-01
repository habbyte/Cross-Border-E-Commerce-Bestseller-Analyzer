/**
 * v-img-fallback 指令
 * 为 <img> 标签提供资源失败回退，默认使用 /placeholder.png
 * 使用：<img v-img-fallback="optionalFallbackSrc" />
 */
export default {
  /**
   * 指令挂载时为元素绑定错误事件
   * @param {HTMLImageElement} el - 目标元素
   * @param {{ value?: string }} binding - 指令传入的绑定值
   */
  mounted(el, binding) {
    if (!(el instanceof HTMLImageElement)) return
    const fallback = typeof binding.value === 'string' && binding.value.length > 0
      ? binding.value
      : '/placeholder.png'
    const inlineSVG = 'data:image/svg+xml;utf8,' + encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><rect width="100%" height="100%" fill="#e5e7eb"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="#9ca3af" font-size="14">No Image</text></svg>`)

    // 如果初始 src 为空，直接使用回退
    if (!el.src || el.src.trim().length === 0) {
      el.src = fallback
    }

    // 错误回退
    let triedFallback = false
    const onError = () => {
      if (!triedFallback) {
        triedFallback = true
        el.src = fallback
        return
      }
      // 如果回退资源也失败，使用内联SVG兜底，彻底避免白屏
      if (el.src !== inlineSVG) {
        el.src = inlineSVG
      }
    }
    el.addEventListener('error', onError)
    // 存储引用以便解绑
    el.__imgFallbackCleanup__ = () => {
      el.removeEventListener('error', onError)
    }
  },
  /**
   * 指令卸载时移除事件监听，避免内存泄漏
   * @param {HTMLImageElement} el
   */
  unmounted(el) {
    if (el.__imgFallbackCleanup__) {
      el.__imgFallbackCleanup__()
      delete el.__imgFallbackCleanup__
    }
  }
}