/**
 * 简易埋点上报模块
 * 后续可替换为真实埋点 SDK
 */
export const events = {
  /**
   * 记录事件
   * @param {string} name 事件名称
   * @param {Record<string, unknown>} [payload={}] 附带参数
   */
  track(name, payload = {}) {
    console.info('[track]', name, payload)
  }
}
