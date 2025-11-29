# 多语言恢复说明

当前版本仅启用了 `zh-CN` 语言包。若要恢复多语言：

1. 将对应语言的 JSON 文件从此目录移回 `src/i18n/lang/`。
2. 在 `src/i18n/index.js` 中导入并注册语言包，同时将 `SUPPORTED_LOCALES` 改为包含目标语言。
3. 解除 `src/stores/useLanguageStore.js` 中的锁定逻辑，使 `setLocale` 可以根据参数切换。
4. 重新开启 UI 中的语言切换交互（例如 `Settings.vue` 的下拉框）。
5. 若需要路由前缀，更新 `src/router/index.js` 中的路由配置。

完成以上步骤后重新构建即可恢复多语言体验。
