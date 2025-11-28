# i18n 再启用指南

## 1. 当前单语言结构概览

- 运行时仅注册 `zh-CN` 语言包：`src/i18n/index.js` 中 `SUPPORTED_LOCALES` 与 `messages` 只包含简体中文。
- 语言资源集中在 `src/i18n/lang/zh-CN.json`；历史多语言包被移至 `src/i18n/_disabled/`，保留原始 key。
- 语言状态由 `useLanguageStore` 锁定为 `zh-CN`，`useSettingsStore` 在加载/保存时会强制写回该语言，避免遗留数据串改。
- Settings 页面禁用了语言选择下拉框；路由层移除了语言前缀与自动跳转逻辑，但保留注释说明恢复方式。

> 若需了解冻结点，可搜索代码里的 `多语言`、`仅提供简体中文` 注释。

## 2. 何时重启多语言

在以下任一条件满足时，应评估恢复 i18n：

- 产品进入多区域/多语运营阶段，需要面向非简体中文用户发布。
- 方案/需求文档明确要求提供 zh-TW 或 en 文案。
- 设计稿和翻译资源（通常来源于翻译平台或术语库）准备完毕。
- QA 已排期进行多语言测试。

若上述条件仍不成立，请保持单语言模式，避免无序扩展。

## 3. 恢复多语言操作步骤

1. **迁回语言包**
   - 将 `src/i18n/_disabled/` 中的目标语言 JSON（如 `zh-TW.json`、`en.json`）移动回 `src/i18n/lang/`。
   - 根据最新文案更新内容，保持 key 与 zh-CN 对齐。

2. **注册 locale**
   - 在 `src/i18n/index.js` 导入新增语言文件，并扩展 `messages`、`SUPPORTED_LOCALES`。
   - 调整 `DEFAULT_LOCALE` / 默认回退策略（通常保留 `zh-CN`）。

3. **解冻语言切换**
   - 修改 `src/stores/useLanguageStore.js` 的 `setLocale`，允许写入传入值并校验是否在 `SUPPORTED_LOCALES`。
   - 在 `src/stores/useSettingsStore.js` 移除强制覆盖语言的逻辑，确保本地存储可持久化用户选择。
   - 重新启用 `Settings.vue` 下拉框（移除 `disabled`），保留 `@change` 同步逻辑。

4. **路由前缀/守卫**
   - 如需基于语言的 URL 结构，可在 `src/router/index.js` 按注释指引恢复前缀与跳转策略（例如 `/en/...`）。
   - 更新导航/链接生成处，确保遵循新 URL 规则。

5. **构建与测试**
   - 运行 `npm run i18n:check` 确保缺失 key 全部补齐。
   - 执行 `npm run build` 并使用多语言环境逐页验证，无缺失翻译或布局溢出。
   - 可选：连接翻译平台或 i18n-ally 自动同步工具。

## 4. key 命名规范

```
domain.module.meaning
```

- **domain**：业务域，如 `dashboard`、`products`、`settings`。
- **module**：具体模块或子功能，如 `strategyAdvisor`、`notifications`。
- **meaning**：语义化描述，使用小写加驼峰，体现用途而非表面文案，例如 `emptyState.description`。
- 避免使用纯数字或无语义的简写；确保跨语言时仍能理解。

## 5. ICU 与占位符写法

- 推荐使用 ICU 语法管理变量、复数与选择：
  - 变量：`"compare.selectedCount": "已选择 {count} 款商品"` → `$t('compare.selectedCount', { count: 3 })`
  - 复数：`"{count, plural, =0 {没有商品} one {1 款商品} other {{count} 款商品}}"`。
  - 选择（select）：`"{gender, select, male {他} female {她} other {Ta}}"`。
- 组件内调用时始终传入命名参数，避免直接拼接字符串。

## 6. 新增文案流程

1. **需求评审**：确认文案用途、目标语言和上下文，决定 key 所属 domain/module。
2. **新增 key**：
   - 在 `zh-CN.json` 按字母序或模块分组插入新条目，遵守命名规范。
   - 同步更新其他语言 JSON（若暂时缺失，可使用占位并标注 TODO）。
3. **代码调用**：以 `$t('domain.module.meaning')` 使用；避免直接写死中文。
4. **校验**：执行 `npm run i18n:check`，确保没有漏翻 key。
5. **提交流程**：PR 描述中注明新增的 key，提醒翻译/产品审核。

---

> 日常开发：启用 VSCode i18n-ally 插件（仓库已提供 `.vscode/settings.json`），可高亮 key 与快速导航。发生缺失或格式错误时，优先修复 zh-CN，再同步其他语言。欢迎补充更多语言，记得更新本文档。
