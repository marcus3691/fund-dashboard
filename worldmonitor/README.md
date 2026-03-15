# World Monitor 本地版

一个简化但功能完整的本地情报态势感知仪表盘，基于 World Monitor 开源项目理念构建。

## 🚀 快速启动

```bash
./start.sh
```

或手动启动：

```bash
python3 -m http.server 3456
```

然后访问 http://localhost:3456

## 📊 功能特性

### 核心功能
- **3D 交互式地图** - 使用 MapLibre GL 渲染的暗色主题地球
- **多图层叠加** - 冲突区域、军事基地、核设施、海底电缆、数据中心等
- **实时情报流** - 模拟新闻聚合面板
- **不稳定指数 (CII)** - 国家风险评估可视化
- **三种模式** - 世界、科技、金融视角切换

### 数据图层
- 🔥 冲突区域
- 🎖️ 军事基地  
- ☢️ 核设施
- 🔌 海底电缆
- 🛢️ 油气管道
- 🖥️ 数据中心
- ⚓ 战略港口
- ✈️ 机场延误
- 🌋 地震监测
- 🔥 卫星火点
- 🛩️ 军机追踪
- 🚢 舰船监控

## 🏗️ 技术栈

- **React 18** - UI 框架
- **MapLibre GL** - 地图渲染引擎
- **deck.gl** - 3D 可视化（预留接口）
- **纯前端实现** - 无需后端，零配置运行

## 📝 说明

这是一个**演示版本**，用于展示 World Monitor 的核心交互理念。完整功能需要：

1. 接入真实数据源（RSS、ADS-B、AIS等）
2. 配置 AI 服务（Ollama/Groq/OpenRouter）
3. 部署后端服务进行数据聚合

## 🔗 相关链接

- 原版项目: https://github.com/koala73/worldmonitor
- 在线演示: https://worldmonitor.app

## 📄 许可证

MIT License - 仅供学习和研究使用
