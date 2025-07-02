# API 认证

所有对 LingoSub API 的请求都必须经过认证。客户端必须在每个请求中提供有效的 API Key。

## 认证方案

API 采用 `Bearer Token` 认证方案。客户端需要将 API Key 放入 HTTP 请求的 `Authorization` 头信息中。

### 请求头格式

```
Authorization: Bearer <YOUR_API_KEY>
```

- `<YOUR_API_KEY>`: 您获取到的私有 API Key。

### 示例

以下是一个使用 `curl` 请求的示例：

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/tasks" \
     -H "Authorization: Bearer your_secret_api_key_here" \
     -F "file=@/path/to/your/subtitle.srt" \
     -F "target_language=en"
```

## 错误响应

如果 API Key 缺失、无效或格式不正确，服务器将返回 `401 Unauthorized` HTTP 状态码，响应正文将包含错误详情。

```json
{
  "detail": "Not authenticated"
}
``` 