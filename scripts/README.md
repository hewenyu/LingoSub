# 构建和部署脚本

LingoSub 项目的自动化构建、测试和部署脚本集合。

## 脚本列表

### 开发脚本
- `dev-setup.ps1` - 开发环境一键配置
- `dev-start.ps1` - 启动开发服务器
- `dev-test.ps1` - 运行完整测试套件

### 构建脚本  
- `build-release.ps1` - 构建生产版本
- `build-sidecar.ps1` - 打包 Python Sidecar
- `build-frontend.ps1` - 构建前端资源

### 部署脚本
- `package-dist.ps1` - 打包分发版本
- `sign-binaries.ps1` - 数字签名
- `create-installer.ps1` - 生成安装程序

### 工具脚本
- `clean.ps1` - 清理构建产物
- `check-deps.ps1` - 检查依赖版本
- `update-licenses.ps1` - 更新许可证信息

## 使用方法

### 开发环境设置
```powershell
# 初始化开发环境
.\scripts\dev-setup.ps1

# 启动开发服务器
.\scripts\dev-start.ps1
```

### 构建生产版本
```powershell
# 完整构建流程
.\scripts\build-release.ps1

# 创建安装包
.\scripts\create-installer.ps1
```

### 测试和验证
```powershell
# 运行所有测试
.\scripts\dev-test.ps1

# 检查依赖状态
.\scripts\check-deps.ps1
```

## 平台支持

- **Windows**：PowerShell 脚本 (.ps1)
- **Linux/macOS**：Bash 脚本 (.sh) [待添加]
- **跨平台**：Node.js 脚本 (.js) [部分功能]

## 环境要求

- PowerShell 5.1+
- Node.js 18+
- Rust 1.70+
- Python 3.9+
- Visual Studio Build Tools (Windows) 