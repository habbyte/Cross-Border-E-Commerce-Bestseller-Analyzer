<template>
  <section class="strategy-room">
    <header class="room-header">
      <div class="header-left">
        <span class="ai-avatar" aria-hidden="true">🤖</span>
        <h1 class="room-title">AI 选品策略师</h1>
      </div>
      <div class="header-right">
        <button class="btn btn-ghost" @click="handleReset">重置</button>
      </div>
    </header>

    <main class="chat-area" ref="chatArea">
      <div
        v-for="(msg, idx) in messages"
        :key="idx"
        class="chat-item"
        :class="msg.role === 'ai' ? 'from-ai' : 'from-user'"
      >
        <div class="bubble" :class="{ 'bubble--component': msg.type === 'component' || msg.type === 'product' }">
          <!-- 文本消息 -->
          <p v-if="msg.type === 'text'" class="bubble-text">{{ msg.text }}</p>

          <!-- 图片消息（如折线图占位） -->
          <figure v-if="msg.type === 'image'" class="bubble-image">
            <img :src="msg.url" alt="ai-chart" loading="lazy" />
            <figcaption v-if="msg.caption" class="image-caption">{{ msg.caption }}</figcaption>
          </figure>

          <!-- 正在输入（AI 思考中） -->
          <div v-if="msg.type === 'typing'" class="typing-dots" aria-label="AI is typing">
            <span></span><span></span><span></span>
          </div>

          <!-- 富媒体：产品卡片 -->
          <ProductCard
            v-if="(msg.type === 'component' || msg.type === 'product') && msg.product"
            :product="msg.product"
            :is-watched="isWatched(msg.product.id)"
            :is-in-compare="isInCompare(msg.product.id)"
            @view-details="handleViewProduct"
            @add-to-watch="handleToggleWatch"
            @add-to-compare="handleAddToCompare"
          />
        </div>
      </div>
    </main>

    <div class="quick-chips">
      <button class="chip" @click="handleSend('分析户外趋势')">📈 分析户外趋势</button>
      <button class="chip" @click="handleSend('推荐高利润耳机')">🔥 推荐高利润耳机</button>
      <button class="chip" @click="handleSend('竞品分析')">🆚 竞品分析</button>
    </div>

    <footer class="input-bar">
      <input
        v-model="input"
        class="input"
        type="text"
        :placeholder="placeholder"
        @keyup.enter="handleSend(input)"
        aria-label="StrategyRoom input"
      />
      <button class="btn btn-primary" @click="handleSend(input)">发送</button>
    </footer>
  </section>
</template>

<script>
import { ref, nextTick, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useProductStore } from '@/stores/useProductStore.js'
import ProductCard from '@/components/ProductCard.vue'

/**
 * StrategyRoom (AI 选品策略师)
 * 聊天室页面：提供基于关键词的「Wizard of Oz」模拟交互。
 * 函数职责：
 * - handleSend: 根据输入的中文关键词（趋势/推荐）生成 AI 回复，支持文本、图片、产品卡富媒体
 * - handleReset: 重置对话流为初始欢迎语
 * - scrollToBottom: 在新增消息后自动滚动到底部，避免用户错过回复
 * - handleViewProduct/handleToggleWatch/handleAddToCompare: 复用 ProductCard 的交互行为
 */
export default {
  name: 'StrategyRoom',
  components: { ProductCard },
  setup() {
    const router = useRouter()
    const store = useProductStore()

    const input = ref('')
    const placeholder = ref('试着问我：挖掘户外露营的趋势...')
    const chatArea = ref(null)

    const messages = ref([
      { role: 'ai', type: 'text', text: '你好，我是演示版 AI 选品策略师。试试下面的快捷芯片吧！' }
    ])

    /**
     * handleSend
     * 将用户消息入列后，先插入 AI 的 typing 指示器，1.5s 后移除并推送真实回复
     */
    function handleSend(text) {
      const content = (text || '').trim()
      if (!content) return
      messages.value.push({ role: 'user', type: 'text', text: content })
      scheduleAiReply(content)
      input.value = ''
    }

    /**
     * scheduleAiReply
     * 插入 typing 指示器（三个点动画），1.5 秒后移除并推送真实 AI 回复
     */
    function scheduleAiReply(content) {
      messages.value.push({ role: 'ai', type: 'typing' })
      setTimeout(() => {
        // 移除最后一个 typing（如果还存在）
        for (let i = messages.value.length - 1; i >= 0; i--) {
          if (messages.value[i].type === 'typing' && messages.value[i].role === 'ai') {
            messages.value.splice(i, 1)
            break
          }
        }

        if (content.includes('趋势')) {
          messages.value.push({
            role: 'ai',
            type: 'text',
            text: '户外露营在近三个月有持续升温趋势，建议关注中高利润周边。'
          })
          messages.value.push({
            role: 'ai',
            type: 'image',
            url: 'https://via.placeholder.com/600x300?text=%E8%B6%8B%E5%8A%BF%E6%8A%98%E7%BA%BF%E5%9B%BE',
            caption: '近12周搜索热度指数（示意图）'
          })
        } else if (content.includes('推荐')) {
          messages.value.push({ role: 'ai', type: 'text', text: '为你推荐一款高利润耳机，具备低竞争与稳定销量。' })
          messages.value.push({
            role: 'ai',
            type: 'component',
            product: {
              id: 'AI-MOCK-001',
              title: 'Pro+ 降噪蓝牙耳机',
              platform: 'Amazon',
              formattedPrice: '$89.99',
              imageUrl: 'https://via.placeholder.com/600x400?text=Pro%2B+%E8%80%B3%E6%9C%BA',
              marginRate: 32,
              stock: 120,
              competitionScore: 28,
              tags: ['高利润', '低竞争', '稳定复购']
            }
          })
        } else {
          messages.value.push({
            role: 'ai',
            type: 'text',
            text: '我是演示版 AI，请点击底部的快捷芯片试试看！'
          })
        }
      }, 1500)
    }

    /**
     * handleReset
     * 重置为开场欢迎消息
     */
    function handleReset() {
      messages.value = [
        { role: 'ai', type: 'text', text: '你好，我是演示版 AI 选品策略师。试试下面的快捷芯片吧！' }
      ]
      nextTick(scrollToBottom)
    }

    /**
     * scrollToBottom
     * 聊天窗口滚动到最底部
     */
    function scrollToBottom() {
      const el = chatArea.value
      if (!el) return
      el.scrollTop = el.scrollHeight
    }

    /**
     * handleViewProduct
     * 进入产品详情
     */
    function handleViewProduct(productId) {
      if (!productId) return
      router.push({ name: 'ProductDetail', params: { id: productId } })
    }

    /**
     * handleToggleWatch
     * 切换监控状态
     */
    function handleToggleWatch(productId) {
      try {
        store.toggleWatch(productId)
      } catch (e) {
        console.warn('[watch] toggle failed', e)
      }
    }

    /**
     * handleAddToCompare
     * 加入对比列表
     */
    function handleAddToCompare(productId) {
      try {
        store.addToCompare(productId)
      } catch (e) {
        console.warn('[compare] add failed', e)
      }
    }

    /**
     * isWatched
     * 是否已在监控列表
     */
    function isWatched(productId) {
      return store.isWatched?.(productId) ?? false
    }

    /**
     * isInCompare
     * 是否已加入对比
     */
    function isInCompare(productId) {
      return store.isInCompare?.(productId) ?? false
    }

    onMounted(async () => {
      if (typeof store.initialize === 'function' && !store.isInitialized) {
        await store.initialize()
      }
      nextTick(scrollToBottom)
    })

    // 自动滚动：监听 messages 的变化进行滚动
    watch(
      messages,
      () => {
        nextTick(scrollToBottom)
      },
      { deep: true }
    )

    return {
      input,
      placeholder,
      messages,
      chatArea,
      handleSend,
      handleReset,
      handleViewProduct,
      handleToggleWatch,
      handleAddToCompare,
      isWatched,
      isInCompare
    }
  }
}
</script>

<style scoped>
.strategy-room {
  position: relative;
  height: calc(100vh - 0px);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.room-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.header-left { display: flex; align-items: center; gap: 10px; }
.ai-avatar { font-size: 24px; }
.room-title { margin: 0; font-size: 1.2rem; }

.chat-area {
  flex: 1;
  overflow-y: auto;
  background: var(--bg-secondary, #f8fafc);
  border: 1px solid var(--border-color, #e5e7eb);
  border-radius: 12px;
  padding: 12px;
  scroll-behavior: smooth;
}
.chat-item { display: flex; margin-bottom: 10px; }
.chat-item.from-ai { justify-content: flex-start; }
.chat-item.from-user { justify-content: flex-end; }
.bubble {
  max-width: 680px;
  background: #fff;
  border: 1px solid #e5e7eb;
  box-shadow: 0 4px 12px rgba(0,0,0,0.04);
  border-radius: 12px;
  padding: 10px;
}
.bubble--component {
  background: transparent;
  border: none;
  box-shadow: none;
  padding: 0;
}
.bubble-text { margin: 0; line-height: 1.5; }
.bubble-image { margin: 6px 0 0; }
.bubble-image img { width: 100%; border-radius: 8px; box-shadow: 0 8px 16px rgba(0,0,0,0.06); }
.image-caption { font-size: 12px; color: #64748b; margin-top: 4px; }

.quick-chips { display: flex; gap: 8px; flex-wrap: wrap; }
.chip {
  border: none;
  border-radius: 999px;
  padding: 6px 12px;
  background: #eef2ff;
  color: #3730a3;
  cursor: pointer;
}

.input-bar {
  position: sticky;
  bottom: 0;
  display: flex;
  gap: 8px;
  background: rgba(255,255,255,0.85);
  padding: 8px;
  border-top: 1px solid #e5e7eb;
}

.input {
  flex: 1;
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  padding: 10px 14px;
}

.btn {
  border: none;
  border-radius: 999px;
  padding: 8px 16px;
  cursor: pointer;
}
.btn-ghost { background: #fff; border: 1px solid #e5e7eb; }
.btn-primary { background: #2563eb; color: #fff; }

/* AI 正在输入动画（三个点跳动） */
.typing-dots {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.typing-dots span {
  width: 6px;
  height: 6px;
  background: #9ca3af;
  border-radius: 50%;
  display: inline-block;
  animation: typingBounce 1s infinite ease-in-out;
}
.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typingBounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.6; }
  40% { transform: translateY(-4px); opacity: 1; }
}
</style>
