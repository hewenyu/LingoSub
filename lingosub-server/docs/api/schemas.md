# API 数据模型 (Schemas)

本文档定义了 LingoSub API 在请求和响应中使用的核心数据结构。这些模型将使用 Pydantic 进行实现，以确保数据的类型安全和验证。

---

## 任务相关模型

### 1. `TaskCreationResponse`

**用途：** 在成功创建一个翻译任务后，服务端返回此模型。

**字段：**

| 字段名    | 类型   | 描述                                     |
| --------- | ------ | ---------------------------------------- |
| `task_id` | string | 唯一标识此翻译任务的 ID。                |
| `status`  | string | 任务创建后的初始状态，通常为 `PENDING`。 |

**JSON 示例：**

```json
{
  "task_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "status": "PENDING"
}
```

---

### 2. `TaskStatusResponse`

**用途：** 用于查询特定任务的当前状态。

**字段：**

| 字段名          | 类型   | 描述                                                                          |
| --------------- | ------ | ----------------------------------------------------------------------------- |
| `task_id`       | string | 任务的唯一 ID。                                                               |
| `status`        | string | 任务的当前状态，可能的值为 `PENDING`, `PROCESSING`, `SUCCESS`, `FAILURE`。    |
| `progress`      | float  | (可选) 任务处理的进度，范围 0.0 到 1.0。                                      |
| `error_message` | string | (可选) 如果任务失败 (`FAILURE`)，此字段将包含错误信息。                       |

**JSON 示例 (处理中)：**

```json
{
  "task_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "status": "PROCESSING",
  "progress": 0.45
}
```

**JSON 示例 (失败)：**

```json
{
  "task_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "status": "FAILURE",
  "error_message": "Translation model returned an error: 'Invalid API key'."
}
```

---

## 通用模型

### 3. `ErrorResponse`

**用途：** 在发生非认证类错误时（如请求验证失败、服务器内部错误等）返回的通用错误模型。

**字段：**

| 字段名   | 类型                   | 描述                                                         |
| -------- | ---------------------- | ------------------------------------------------------------ |
| `detail` | string / array[object] | 描述错误的字符串，或在验证错误时提供更详细错误信息的对象数组。 |

**JSON 示例 (简单错误)：**

```json
{
  "detail": "SRT file is corrupted or empty."
}
```

**JSON 示例 (验证错误)：**

```json
{
  "detail": [
    {
      "loc": [
        "body",
        "target_language"
      ],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
``` 