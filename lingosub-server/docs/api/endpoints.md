# API 端点

本文档详细描述了 LingoSub API v1 的所有可用端点。

---

### 1. 创建翻译任务

此端点用于上传一个 SRT 字幕文件，并启动一个异步的翻译任务。

- **HTTP 方法：** `POST`
- **路径：** `/api/v1/tasks`
- **认证：** 需要 (Bearer Token)

#### 请求

请求体必须为 `multipart/form-data` 格式，包含以下两个部分：

| 字段名            | 类型   | 描述                                                       | 是否必须 |
| ----------------- | ------ | ---------------------------------------------------------- | -------- |
| `file`            | file   | 要翻译的 SRT 字幕文件。                                    | 是       |
| `target_language` | string | 目标翻译语言的 ISO 639-1 代码，例如 `en`, `zh`, `ja`, `ko`。 | 是       |

#### 响应

- **`202 Accepted`**: 任务已成功创建并加入处理队列。
  - **响应体：** `TaskCreationResponse` (参考 `schemas.md`)
  - **示例：**
    ```json
    {
      "task_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "status": "PENDING"
    }
    ```

- **`400 Bad Request`**: 请求体无效（例如，缺少文件或目标语言）。
  - **响应体：** `ErrorResponse` (参考 `schemas.md`)

- **`401 Unauthorized`**: API Key 无效或未提供。

- **`422 Unprocessable Entity`**: 请求格式正确，但内容无法处理（例如，上传的不是有效的 SRT 文件）。
  - **响应体：** `ErrorResponse` (参考 `schemas.md`)

---

### 2. 查询任务状态

此端点用于查询指定翻译任务的当前状态。

- **HTTP 方法：** `GET`
- **路径：** `/api/v1/tasks/{task_id}/status`
- **认证：** 需要 (Bearer Token)

#### 路径参数

| 参数名    | 类型   | 描述                  |
| --------- | ------ | --------------------- |
| `task_id` | string | 要查询的任务的唯一 ID。 |

#### 响应

- **`200 OK`**: 成功获取任务状态。
  - **响应体：** `TaskStatusResponse` (参考 `schemas.md`)
  - **示例：**
    ```json
    {
      "task_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "status": "PROCESSING",
      "progress": 0.75
    }
    ```

- **`404 Not Found`**: 提供的 `task_id` 不存在。
  - **响应体：** `ErrorResponse` (参考 `schemas.md`)
  - **示例：**
    ```json
    {
      "detail": "Task with id a1b2c3d4-e5f6-7890-1234-567890abcdef not found."
    }
    ```

- **`401 Unauthorized`**: API Key 无效或未提供。

---

### 3. 获取翻译结果

此端点用于下载已成功完成翻译的 SRT 字幕文件。

- **HTTP 方法：** `GET`
- **路径：** `/api/v1/tasks/{task_id}/result`
- **认证：** 需要 (Bearer Token)

#### 路径参数

| 参数名    | 类型   | 描述                  |
| --------- | ------ | --------------------- |
| `task_id` | string | 要查询的任务的唯一 ID。 |

#### 响应

- **`200 OK`**: 成功获取翻译结果。
  - **Content-Type:** `application/x-subrip`
  - **响应体：** 翻译后的 SRT 文件的原始内容。
  - **示例：**
    ```srt
    1
    00:00:01,000 --> 00:00:03,500
    This is the translated subtitle.

    2
    00:00:04,200 --> 00:00:06,800
    This is the second line.
    ```

- **`404 Not Found`**: 提供的 `task_id` 不存在，或任务尚未成功完成。
  - **响应体：** `ErrorResponse` (参考 `schemas.md`)
  - **示例：**
    ```json
    {
      "detail": "Result not available. Task status is: PROCESSING"
    }
    ```

- **`401 Unauthorized`**: API Key 无效或未提供。 