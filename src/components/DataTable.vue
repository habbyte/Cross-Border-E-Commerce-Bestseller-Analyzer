<template>
  <div class="data-table">
    <div class="table-header" v-if="showHeader">
      <h3 class="table-title">{{ title || $t('common.table') }}</h3>
      <div class="table-actions">
        <slot name="actions"></slot>
      </div>
    </div>
    
    <div class="table-container">
      <table class="table">
        <thead>
          <tr>
            <th 
              v-for="column in columns" 
              :key="column.key"
              :class="column.className"
              @click="handleSort(column)"
            >
              {{ column.label }}
              <span v-if="column.sortable" class="sort-indicator">
                {{ getSortIcon(column.key) }}
              </span>
            </th>
          </tr>
        </thead>
        
        <tbody>
          <tr 
            v-for="item in sortedData" 
            :key="getItemKey(item)"
            class="table-row"
            @click="$emit('row-click', item)"
          >
            <td 
              v-for="column in columns" 
              :key="column.key"
              :class="column.className"
            >
              <slot 
                :name="`cell-${column.key}`" 
                :item="item" 
                :value="getColumnValue(item, column.key)"
              >
                {{ getColumnValue(item, column.key) }}
              </slot>
            </td>
          </tr>
        </tbody>
      </table>
      
      <div v-if="!data.length" class="table-empty">
        <div class="empty-icon">📭</div>
        <div class="empty-text">{{ emptyText || $t('common.empty') }}</div>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * DataTable component / 数据表格组件
 * 统一的表格展示组件，提供排序与插槽渲染，避免重复代码。
 */
export default {
  name: 'DataTable',
  
  props: {
    title: {
      type: String,
      default: ''
    },
    
    columns: {
      type: Array,
      required: true,
      validator: (columns) => {
        return columns.every(col => col.key && col.label)
      }
    },
    
    data: {
      type: Array,
      default: () => []
    },
    
    keyField: {
      type: String,
      default: 'id'
    },
    
    showHeader: {
      type: Boolean,
      default: true
    },
    
    // emptyText 支持传入覆盖，同时默认从 i18n 读取
    emptyText: {
      type: String,
      default: ''
    }
  },
  
  emits: ['row-click', 'sort-change'],
  
  data() {
    return {
      sortKey: '',
      sortOrder: 'asc' // 'asc' | 'desc'
    }
  },
  
  computed: {
    /**
     * sortedData / 排序后的数据
     * 统一排序逻辑，数字走数值比较，字符串走 localeCompare
     */
    sortedData() {
      if (!this.sortKey) {
        return this.data
      }
      
      const sorted = [...this.data].sort((a, b) => {
        const aVal = this.getColumnValue(a, this.sortKey)
        const bVal = this.getColumnValue(b, this.sortKey)
        
        // 数字比较 / numeric compare
        if (typeof aVal === 'number' && typeof bVal === 'number') {
          return this.sortOrder === 'asc' ? aVal - bVal : bVal - aVal
        }
        
        // 字符串比较 / string compare
        const aStr = String(aVal).toLowerCase()
        const bStr = String(bVal).toLowerCase()
        
        if (this.sortOrder === 'asc') {
          return aStr.localeCompare(bStr)
        } else {
          return bStr.localeCompare(aStr)
        }
      })
      
      return sorted
    }
  },
  
  methods: {
    /**
     * getColumnValue / 获取列值
     * 支持嵌套属性访问，如 'product.price'
     */
    getColumnValue(item, key) {
      return key.split('.').reduce((obj, prop) => obj?.[prop], item)
    },
    
    /**
     * getItemKey / 获取行键值
     */
    getItemKey(item) {
      return this.getColumnValue(item, this.keyField)
    },
    
    /**
     * handleSort / 处理排序
     * 点击表头切换排序列与方向，向外发出 sort-change 事件
     */
    handleSort(column) {
      if (!column.sortable) return
      
      if (this.sortKey === column.key) {
        // 切换排序方向 / toggle order
        this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc'
      } else {
        // 新的排序列 / new sort key
        this.sortKey = column.key
        this.sortOrder = 'asc'
      }
      
      this.$emit('sort-change', {
        key: this.sortKey,
        order: this.sortOrder
      })
    },
    
    /**
     * getSortIcon / 获取排序图标
     */
    getSortIcon(key) {
      if (this.sortKey !== key) return '↕'
      return this.sortOrder === 'asc' ? '↑' : '↓'
    }
  }
}
</script>

<style scoped>
.data-table {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}

.table-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.table-actions {
  display: flex;
  gap: 8px;
}

.table-container {
  overflow-x: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
}

.table th {
  background: #f9fafb;
  padding: 12px 16px;
  text-align: left;
  font-size: 12px;
  font-weight: 600;
  color: #374151;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid #e5e7eb;
  cursor: pointer;
  user-select: none;
  position: relative;
}

.table th:hover {
  background: #f3f4f6;
}

.sort-indicator {
  margin-left: 4px;
  font-size: 10px;
  opacity: 0.6;
}

.table td {
  padding: 12px 16px;
  border-bottom: 1px solid #f3f4f6;
  font-size: 14px;
  color: #1f2937;
}

.table-row {
  transition: background-color 0.2s ease;
  cursor: pointer;
}

.table-row:hover {
  background: #f9fafb;
}

.table-row:last-child td {
  border-bottom: none;
}

.table-empty {
  padding: 40px 20px;
  text-align: center;
  color: #6b7280;
}

.empty-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.empty-text {
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .table-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .table th,
  .table td {
    padding: 8px 12px;
    font-size: 12px;
  }
  
  .table-empty {
    padding: 30px 15px;
  }
}
</style>
