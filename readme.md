# 平台详情

## 接口支持
- 通义千问
- Kimi
- 字节-火山引擎(有问题)
- 腾讯-元宝
-其余为自动化实现
## 所有平台调用优先级
**一级（逆向）**：
- 元宝
- 火山引擎(有问题)
- 通义千问
- Kimi(inf,有问题)

**二级(快速dp)**：
- 智谱清言
- DeepSeek()
- Kimi（dp，有bug）

**三级**：
- 阶跃
- 百度搜索
- 当贝
- 华为小艺
- 问小白（有bug）
- 豆包
- 纳米

**未实现**：
- 文心一言

# 调用说明

**请求方式**：POST `http://127.0.0.1:6666/chat`

**请求示例**：
```json
{
  "platform": "stepfun",
  "agent": "stepfun",
  "invoke_method": "dp",
  "use_skil": "get_from_llm",
  "input_params": {
    "prompt": "你好",
    "mode": {
      "online_search": true,
      "long_think": true
    }
  }
}