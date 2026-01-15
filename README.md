# A 股 RSI 监控 Telegram Bot

使用 akshare 接口，监控 A 股个股和 ETF 的 RSI 指标，当达到超买/超卖阈值时自动推送 Telegram 通知。

## 功能特点

- 📈 支持 A 股个股和 ETF 监控
- ⏰ 仅在交易时段运行（自动识别节假日）
- 📊 支持 30 分钟、60 分钟、日线 三种周期
- 🔔 RSI 超买/超卖自动提醒
- 📱 Telegram Bot 交互

## 快速开始

### 1. 环境配置

```bash
cp .env.example .env
# 编辑 .env 填入你的 Telegram Bot Token
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动

```bash
python main.py
```

### 4. Docker 部署

```bash
docker-compose up -d --build
```

## 使用方法

在 Telegram 中与 Bot 对话：

- `/start` - 显示主菜单
- `/add <股票代码>` - 添加监控 (如: `/add 600519`)
- `/list` - 查看监控列表
- `/manage` - 管理已有监控

## 支持的股票代码格式

| 类型     | 格式示例 | 说明        |
| -------- | -------- | ----------- |
| 沪市主板 | 600519   | 贵州茅台    |
| 深市主板 | 000001   | 平安银行    |
| 创业板   | 300750   | 宁德时代    |
| 科创板   | 688981   | 中芯国际    |
| ETF      | 510300   | 沪深 300ETF |
| ETF      | 159915   | 创业板 ETF  |
