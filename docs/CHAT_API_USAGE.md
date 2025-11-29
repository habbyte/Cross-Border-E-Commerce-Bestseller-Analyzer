# 对话 API 使用说明

本文档介绍如何使用新增的 DeepSeek 对话 API 和向量搜索功能。

## 功能概述

1. **DeepSeek 对话 API**：集成 DeepSeek API，提供智能对话回复功能
2. **向量搜索**：对 Amazon 类别数据进行向量化，支持语义搜索
3. **对话历史管理**：类似 chatbox 的实现，支持本地保存和管理多个对话会话

## 环境配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

新增依赖：
- `httpx==0.27.0` - HTTP 客户端
- `numpy==1.26.4` - 数值计算

### 2. 配置 DeepSeek API Key

在 `.env` 文件中添加：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

或在环境变量中设置：

```bash
export DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

## API 端点

### 对话相关

#### 1. 基础对话接口

**POST** `/api/chat/`

发送消息并获取回复。

**请求体：**
```json
{
  "messages": [
    {"role": "user", "content": "你好"}
  ],
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**查询参数：**
- `session_id` (可选): 会话 ID，不提供则创建新会话
- `save_history` (默认 true): 是否保存对话历史

**响应：**
```json
{
  "reply": "你好！有什么可以帮助你的吗？",
  "model": "deepseek-chat",
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  },
  "session_id": "uuid-here",
  "message_id": "message-uuid-here"
}
```

#### 2. 简化对话接口

**POST** `/api/chat/simple?message=你好`

**查询参数：**
- `message`: 用户消息
- `system_prompt` (可选): 系统提示词
- `session_id` (可选): 会话 ID
- `save_history` (默认 true): 是否保存历史

**响应：**
```json
{
  "reply": "你好！有什么可以帮助你的吗？",
  "session_id": "uuid-here"
}
```

### 对话历史管理

#### 3. 获取所有会话

**GET** `/api/chat/sessions`

**响应：**
```json
{
  "sessions": [
    {
      "id": "uuid-1",
      "title": "新对话 2025-01-15 10:30",
      "created_at": "2025-01-15T10:30:00",
      "updated_at": "2025-01-15T10:35:00",
      "message_count": 10
    }
  ],
  "total": 1
}
```

#### 4. 创建新会话

**POST** `/api/chat/sessions?title=我的对话`

**查询参数：**
- `title` (可选): 会话标题

**响应：**
```json
{
  "session_id": "uuid-here",
  "session": {
    "id": "uuid-here",
    "title": "我的对话",
    "created_at": "2025-01-15T10:30:00",
    "updated_at": "2025-01-15T10:30:00",
    "message_count": 0
  }
}
```

#### 5. 获取会话详情

**GET** `/api/chat/sessions/{session_id}`

**响应：**
```json
{
  "session": {
    "id": "uuid-here",
    "title": "我的对话",
    "created_at": "2025-01-15T10:30:00",
    "updated_at": "2025-01-15T10:35:00",
    "message_count": 10
  },
  "messages": [
    {
      "id": "msg-uuid-1",
      "role": "user",
      "content": "你好",
      "timestamp": "2025-01-15T10:30:00",
      "metadata": {}
    },
    {
      "id": "msg-uuid-2",
      "role": "assistant",
      "content": "你好！有什么可以帮助你的吗？",
      "timestamp": "2025-01-15T10:30:05",
      "metadata": {
        "model": "deepseek-chat",
        "usage": {...}
      }
    }
  ],
  "message_count": 10
}
```

#### 6. 更新会话标题

**PATCH** `/api/chat/sessions/{session_id}/title?title=新标题`

#### 7. 删除会话

**DELETE** `/api/chat/sessions/{session_id}`

#### 8. 清空会话消息

**DELETE** `/api/chat/sessions/{session_id}/messages`

### 向量搜索相关

#### 9. 向量搜索

**GET** `/api/search/vector?query=电子产品&top_k=5&min_similarity=0.5`

**查询参数：**
- `query`: 搜索查询文本（必需）
- `top_k`: 返回前 k 个结果（默认 5，最大 50）
- `min_similarity`: 最小相似度阈值（0-1，默认 0.0）

**响应：**
```json
{
  "query": "电子产品",
  "results": [
    {
      "id": "1",
      "name": "Electronics",
      "source_url": "https://www.amazon.com/...",
      "created_at": "2025-10-17 00:00:55.546706+08",
      "updated_at": "2025-10-17 00:00:55.546706+08",
      "similarity": 0.85
    }
  ],
  "total": 5
}
```

#### 10. 向量化类别数据

**POST** `/api/search/vectorize?csv_path=categories.csv&output_path=data/vectorized_categories.json`

**查询参数：**
- `csv_path` (可选): CSV 文件路径，默认为 `categories.csv`
- `output_path` (可选): 输出 JSON 文件路径，默认为 `data/vectorized_categories.json`

**响应：**
```json
{
  "message": "向量化完成",
  "total": 37,
  "output_path": "data/vectorized_categories.json"
}
```

## 使用示例

### Python 示例

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. 创建新会话并发送消息
response = requests.post(
    f"{BASE_URL}/api/chat/simple",
    params={
        "message": "你好，请介绍一下这个项目",
        "save_history": True
    }
)
print(response.json())

# 2. 获取所有会话
response = requests.get(f"{BASE_URL}/api/chat/sessions")
sessions = response.json()
print(f"共有 {sessions['total']} 个会话")

# 3. 获取特定会话的消息历史
session_id = sessions['sessions'][0]['id']
response = requests.get(f"{BASE_URL}/api/chat/sessions/{session_id}")
history = response.json()
print(f"会话包含 {history['message_count']} 条消息")

# 4. 向量搜索
response = requests.get(
    f"{BASE_URL}/api/search/vector",
    params={
        "query": "笔记本电脑",
        "top_k": 5
    }
)
results = response.json()
print(f"找到 {results['total']} 个相关结果")
```

### cURL 示例

```bash
# 发送消息
curl -X POST "http://localhost:8000/api/chat/simple?message=你好" \
  -H "Content-Type: application/json"

# 获取会话列表
curl -X GET "http://localhost:8000/api/chat/sessions"

# 向量搜索
curl -X GET "http://localhost:8000/api/search/vector?query=电子产品&top_k=5"
```

## 数据存储

### 对话历史存储位置

所有对话历史保存在 `data/chat_history/` 目录：

```
data/chat_history/
├── sessions.json              # 会话列表索引
├── session_<uuid-1>.json      # 会话 1 的消息历史
├── session_<uuid-2>.json      # 会话 2 的消息历史
└── ...
```

### 向量数据存储位置

向量化的类别数据保存在：
- `data/vectorized_categories.json`

## 初始化步骤

### 1. 向量化类别数据

首次使用向量搜索前，需要先向量化数据：

```bash
# 方式 1: 使用脚本
python scripts/vectorize_categories.py

# 方式 2: 使用 API
curl -X POST "http://localhost:8000/api/search/vectorize"
```

### 2. 启动 API 服务

```bash
python run_api.py
```

## 注意事项

1. **API Key 配置**：确保正确配置 `DEEPSEEK_API_KEY`，否则对话功能不可用
2. **向量化成本**：向量化过程会调用 DeepSeek API，会产生费用
3. **历史消息限制**：为避免 token 过多，对话时只加载最近 10 条历史消息作为上下文
4. **存储空间**：对话历史保存在本地文件，注意定期清理不需要的会话

## 故障排查

### 问题：DeepSeek API 请求失败

**解决方案：**
- 检查 API Key 是否正确配置
- 检查网络连接
- 查看日志文件了解详细错误信息

### 问题：向量搜索返回空结果

**解决方案：**
- 确保已运行向量化脚本
- 检查 `data/vectorized_categories.json` 文件是否存在
- 尝试降低 `min_similarity` 阈值

### 问题：对话历史未保存

**解决方案：**
- 检查 `data/chat_history/` 目录权限
- 确保 `save_history` 参数为 `true`
- 查看日志文件了解详细错误信息

