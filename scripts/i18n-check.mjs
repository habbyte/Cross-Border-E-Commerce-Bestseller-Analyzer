import { promises as fs } from 'fs'
import path from 'path'

const projectRoot = path.resolve(process.cwd(), '.')
const sourceDir = path.join(projectRoot, 'src')
const localeFile = path.join(projectRoot, 'src/i18n/lang/zh-CN.json')

const FILE_EXTENSIONS = new Set(['.vue', '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs'])
const IGNORE_DIRS = new Set(['node_modules', 'dist', '.git'])

const keyUsage = new Set()

const usagePattern = /\b(?:\$t|t)\(\s*['"`]([^'"`]+)['"`]/g

async function walk(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true })
  for (const entry of entries) {
    if (IGNORE_DIRS.has(entry.name)) continue
    const fullPath = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      await walk(fullPath)
    } else if (FILE_EXTENSIONS.has(path.extname(entry.name))) {
      const content = await fs.readFile(fullPath, 'utf8')
      let match
      while ((match = usagePattern.exec(content)) !== null) {
        const key = match[1]
        if (key.includes('${')) continue
        keyUsage.add(key)
      }
    }
  }
}

function flattenMessages(obj, prefix = '') {
  const result = {}
  for (const [key, value] of Object.entries(obj)) {
    const nextKey = prefix ? `${prefix}.${key}` : key
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      Object.assign(result, flattenMessages(value, nextKey))
    } else {
      result[nextKey] = value
    }
  }
  return result
}

async function main() {
  await walk(sourceDir)

  const localeContent = await fs.readFile(localeFile, 'utf8')
  const localeData = JSON.parse(localeContent)
  const flattened = flattenMessages(localeData)

  const missingKeys = Array.from(keyUsage).filter((key) => !(key in flattened)).sort()

  if (missingKeys.length > 0) {
    console.error('[i18n-check] 以下 key 缺失于 zh-CN.json：')
    for (const key of missingKeys) {
      console.error(`  - ${key}`)
    }
    console.error('\n请补充以上 key 后再提交。')
    process.exitCode = 1
    return
  }

  console.log('[i18n-check] 所有 key 均存在，检查通过。')
}

main().catch((err) => {
  console.error('[i18n-check] 执行失败：', err)
  process.exitCode = 1
})
