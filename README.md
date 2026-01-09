# SuperTrend 指标

## 项目概述
SuperTrend 是一个技术分析指标，用于识别股票、外汇和其他金融资产的趋势方向。该项目提供了 A股ETF SuperTrend 指标的实现和应用。

## 功能特性
- 📊 趋势识别：自动识别上升趋势和下降趋势
- 🎯 交易信号：生成买入和卖出信号
- 📈 多周期分析：支持多个时间周期的分析
- ⚙️ 可配置参数：灵活的参数设置以适应不同的市场条件

## 使用方法

### 安装
```bash
# 克隆仓库
git clone https://github.com/StLee-lrf/SuperTrend-for-A-.git

# 进入项目目录
cd SuperTrend-for-A-
```

### 基本用法
```python
# 示例代码
from supertrend import SuperTrend

# 创建 SuperTrend 指标实例
st = SuperTrend(period=10, multiplier=3.0)

# 计算指标值
result = st.calculate(price_data)
```

## 参数说明

| 参数名 | 说明 | 默认值 |
|--------|------|--------|
| period | 周期长度 | 10 |
| multiplier | 乘数 | 3.0 |

## 原理介绍

SuperTrend 指标基于平均真实波幅（ATR）计算：
1. 计算 ATR（平均真实波幅）
2. 计算基础线：(最高价 + 最低价) / 2
3. 计算上轨和下轨
4. 根据价格与轨道的关系判断趋势

## 常见问题

**Q: 如何选择最合适的周期？**
- A: 短期交易建议使用较小的周期（如 5-10），中长期交易可使用较大的周期（如 20-50）

**Q: 乘数有什么影响？**
- A: 乘数越大，轨道越宽，信号越少但准确度可能更高；乘数越小，轨道越窄，信号更频繁

**Q: 如何更换我想测试的对象？**
- A: 在Config中，修改symbol的值即可

## 贡献指南

欢迎提交 Issues 和 Pull Requests 来改进这个项目。

## 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

## 作者

StLee-lrf

---

*最后更新：2026-01-09*
