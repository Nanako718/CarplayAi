# iPhone 快捷指令配置指南

## 📱 概述

本指南将帮助你配置 iPhone 快捷指令，在 CarPlay 连接/断开时自动上传数据并播放 AI 播报。

## 🔐 用户认证机制（数据隔离）

### 为什么需要 Token？

每个用户都有独立的 Token（JWT），用于：
- **身份识别**：系统知道是哪个用户在上传数据
- **数据隔离**：用户只能访问自己的数据
- **安全保障**：防止他人篡改数据

### Token 工作流程

```
1. 用户注册/登录 → 获取 Token
2. 快捷指令携带 Token 调用 API
3. 服务器验证 Token → 识别用户 → 返回该用户的数据
```

### 数据隔离示例

```
用户A（Token-A）上传数据 → 存储到用户A的数据库记录
用户B（Token-B）上传数据 → 存储到用户B的数据库记录

用户A 查询 → 只能看到自己的数据
用户B 查询 → 只能看到自己的数据
```

---

## 🚀 快速开始

### 步骤 1：注册账号

1. 打开浏览器访问：`http://你的服务器IP:8000`
2. 点击"注册"标签
3. 填写用户名和密码
4. 注册成功后，复制显示的 Token

### 步骤 2：创建 CarPlay 连接触发器

#### 2.1 创建"CarPlay 连接"快捷指令

1. 打开 iPhone **快捷指令** App
2. 点击右上角 **+** 创建新快捷指令
3. 命名为 **"CarPlay 连接"**

#### 2.2 添加动作

**动作 1：获取当前位置**
- 搜索并添加 **"获取当前位置"** 动作
- 允许访问位置信息

**动作 2：获取天气**
- 搜索并添加 **"获取当前天气"** 动作

**动作 3：获取位置详细信息**
- 搜索并添加 **"获取地图"** 动作
- 输入：当前位置的详细地址

**动作 4：构建请求数据**
- 搜索并添加 **"文本"** 动作
- 输入以下 JSON 模板：

```json
{
  "event_type": "connect",
  "latitude": [当前位置的纬度],
  "longitude": [当前位置的经度],
  "address": "[当前位置的地址]",
  "weather": {
    "condition": "[天气状况]",
    "temp_high": [最高温],
    "temp_low": [最低温],
    "precipitation_prob": [降水概率]
  },
  "timestamp": "[当前时间]"
}
```

**动作 5：发送 HTTP 请求**
- 搜索并添加 **"获取 URL 内容"** 动作
- URL：`http://你的服务器IP:8000/api/v1/events?response_type=text`
- 方法：`POST`
- 请求头：
  - `Authorization`: `Bearer 你的Token`
  - `Content-Type`: `application/json`
- 请求体：上一步构建的 JSON

**动作 6：解析响应**
- 搜索并添加 **"获取字典值"** 动作
- 输入：上一步的响应
- 键：`data.broadcast_text`

**动作 7：播放语音**
- 搜索并添加 **"朗读文本"** 动作
- 输入：上一步获取的播报文本
- 选择语音：中文
- 语速：适中

#### 2.3 设置自动化触发器

1. 打开 iPhone **快捷指令** App
2. 点击底部 **自动化** 标签
3. 点击右上角 **+** 创建个人自动化
4. 选择 **"CarPlay"**
5. 选择 **"连接时"**
6. 选择刚才创建的 **"CarPlay 连接"** 快捷指令
7. 关闭 **"运行前询问"**

---

### 步骤 3：创建 CarPlay 断开触发器

重复步骤 2，但：
- 命名为 **"CarPlay 断开"**
- `event_type` 改为 `disconnect`
- 自动化触发器选择 **"断开时"**

---

## 📋 完整快捷指令示例

### CarPlay 连接快捷指令

```
1. 获取当前位置
   ↓
2. 获取当前天气
   ↓
3. 文本（构建JSON）：
   {
     "event_type": "connect",
     "latitude": [当前位置纬度],
     "longitude": [当前位置经度],
     "address": "[当前位置地址]",
     "weather": {
       "condition": "[天气状况]",
       "temp_high": [最高温],
       "temp_low": [最低温],
       "precipitation_prob": [降水概率]
     },
     "timestamp": "[当前时间 ISO格式]"
   }
   ↓
4. 获取 URL 内容
   URL: http://你的服务器IP:8000/api/v1/events?response_type=text
   方法: POST
   头: Authorization: Bearer 你的Token
   头: Content-Type: application/json
   body: [上一步的文本]
   ↓
5. 获取字典值
   输入: [URL内容]
   键: data.broadcast_text
   ↓
6. 朗读文本
   [播报内容]
```

---

## 🔧 高级配置

### 方案 A：直接播放音频（推荐）

如果你想让服务器直接返回音频（更自然的语音），修改请求：

```
URL: http://你的服务器IP:8000/api/v1/events?response_type=audio
方法: POST
头: Authorization: Bearer 你的Token
头: Content-Type: application/json
body: [JSON数据]

响应处理：
1. 获取 URL 内容（音频文件）
2. 播放声音
```

### 方案 B：使用 iPhone 本地 TTS

如果服务器 TTS 不可用，可以使用 iPhone 本地语音：

```
1. 获取 URL 内容（获取播报文本）
2. 朗读文本（使用 Siri 语音）
```

---

## 📊 快捷指令变量映射

| 快捷指令变量 | API 字段 | 说明 |
|--------------|----------|------|
| 当前位置纬度 | latitude | 纬度坐标 |
| 当前位置经度 | longitude | 经度坐标 |
| 当前位置地址 | address | 详细地址 |
| 天气状况 | weather.condition | 晴/多云/雨等 |
| 最高温 | weather.temp_high | 摄氏度 |
| 最低温 | weather.temp_low | 摄氏度 |
| 降水概率 | weather.precipitation_prob | 百分比 |
| 当前时间 | timestamp | ISO 8601 格式 |

---

## 🛡️ 安全注意事项

1. **保管好 Token**
   - Token 是你的身份凭证
   - 不要分享给他人
   - 泄露后立即重新登录获取新 Token

2. **服务器安全**
   - 生产环境请使用 HTTPS
   - 配置防火墙，只开放必要端口
   - 定期更新服务器密码

3. **数据隐私**
   - 位置数据仅用于智能播报
   - 不会分享给第三方
   - 可随时删除历史数据

---

## ❓ 常见问题

### Q1: 快捷指令无法运行？

检查：
- 服务器是否正常运行
- Token 是否正确
- 网络连接是否正常

### Q2: 播报内容不准确？

检查：
- 天气数据是否正确获取
- 位置信息是否准确
- AI 服务是否正常

### Q3: 如何获取新的 Token？

1. 访问 `http://你的服务器IP:8000`
2. 使用账号密码登录
3. 系统会显示新的 Token

### Q4: 多个设备可以共用一个账号吗？

可以，但建议每个设备使用独立账号，便于：
- 独立的学习模型
- 独立的位置识别
- 独立的播报偏好

---

## 📞 技术支持

如有问题，请查看：
- API 文档：`http://你的服务器IP:8000/docs`
- 服务器日志：`logs/app.log`
