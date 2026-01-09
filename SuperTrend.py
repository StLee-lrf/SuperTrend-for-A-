import pandas as pd
import numpy as np
import plotly.graph_objects as go
import akshare as ak
from datetime import datetime
import traceback

# ==========================================
# ⚙️ 【配置区域】 修改这里即可控制整个脚本
# ==========================================
CONFIG = {
    # 1. 标的代码 (例如: '562590' 为卫星ETF, '600519' 为茅台, '510300' 为沪深300ETF)
    'symbol': '562590',  
    
    # 2. Supertrend 参数
    'period': 10,        # ATR 周期 (默认 10)
    'multiplier': 3.0,   # ATR 倍数 (默认 3.0, 想要更灵敏可改为 2.0)
    
    # 3. 数据范围
    'limit': 700,        # 获取最近多少天的数据
    
    # 4. 图表设置
    'html_name': 'supertrend_analysis.html', # 保存的文件名
    'chart_title': 'Supertrend Strategy Analysis' # 图表主标题
}
# ==========================================

# --------------------------
# 1. 通用数据获取 (自动适配 ETF 或 股票)
# --------------------------
def get_market_data(symbol, limit=700):
    """
    尝试获取历史数据，优先尝试 ETF 接口，失败则尝试 股票 接口
    """
    print(f"🔄 正在获取标的 ({symbol}) 数据...")
    
    # 内部清洗函数
    def clean_data(df_raw):
        # 标准列名清洗
        rename_map = {'日期': 'Date', '开盘': 'Open', '收盘': 'Close', '最高': 'High', '最低': 'Low', '成交量': 'Volume'}
        df_raw.rename(columns=rename_map, inplace=True)
        
        # 确保日期格式
        df_raw['Date'] = pd.to_datetime(df_raw['Date'])
        # 确保数值格式
        for c in ['Open', 'High', 'Low', 'Close']:
            df_raw[c] = pd.to_numeric(df_raw[c], errors='coerce')
            
        df_raw = df_raw.sort_values('Date').reset_index(drop=True)
        if len(df_raw) > limit:
            df_raw = df_raw.iloc[-limit:].reset_index(drop=True)
        return df_raw[['Date', 'Open', 'High', 'Low', 'Close']]

    # --- 尝试 1: ETF 接口 ---
    try:
        # 东方财富 ETF 历史
        df = ak.fund_etf_hist_em(symbol=symbol, period="daily", adjust="qfq")
        if df is None or df.empty:
            raise ValueError("ETF接口返回为空")
        print("✅ 检测为 ETF 数据")
        return clean_data(df)
    except:
        pass # 继续尝试下一个接口

    # --- 尝试 2: 股票接口 ---
    try:
        # 东方财富 A股 历史
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
        if df is None or df.empty:
            raise ValueError("股票接口返回为空")
        print("✅ 检测为 股票 数据")
        return clean_data(df)
    except Exception as e:
        print(f"❌ 所有接口均无法获取 ({symbol}) 数据。")
        print("   建议检查：1. 代码是否正确 2. 网络连接 3. akshare版本")
        raise e

# --------------------------
# 2. Supertrend 计算逻辑
# --------------------------
def calculate_supertrend(df, period=10, multiplier=3):
    df = df.copy()
    # TR Calculation
    df['tr0'] = abs(df['High'] - df['Low'])
    df['tr1'] = abs(df['High'] - df['Close'].shift(1))
    df['tr2'] = abs(df['Low'] - df['Close'].shift(1))
    df['tr'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)
    
    # ATR (RMA - Wilder's Smoothing)
    df['atr'] = df['tr'].ewm(alpha=1/period, adjust=False).mean()
    
    # Bands
    hl2 = (df['High'] + df['Low']) / 2
    df['basic_upper'] = hl2 + (multiplier * df['atr'])
    df['basic_lower'] = hl2 - (multiplier * df['atr'])
    
    # Initialization
    final_upper = [0.0] * len(df)
    final_lower = [0.0] * len(df)
    supertrend = [0.0] * len(df)
    trend = [1] * len(df)
    
    # Loop
    for i in range(1, len(df)):
        # Upper Band Logic
        if df['basic_upper'][i] < final_upper[i-1] or df['Close'][i-1] > final_upper[i-1]:
            final_upper[i] = df['basic_upper'][i]
        else:
            final_upper[i] = final_upper[i-1]
            
        # Lower Band Logic
        if df['basic_lower'][i] > final_lower[i-1] or df['Close'][i-1] < final_lower[i-1]:
            final_lower[i] = df['basic_lower'][i]
        else:
            final_lower[i] = final_lower[i-1]
            
        # Trend Switch Logic
        trend[i] = trend[i-1]
        if trend[i] == 1:
            if df['Close'][i] < final_lower[i]:
                trend[i] = -1
        else:
            if df['Close'][i] > final_upper[i]:
                trend[i] = 1
                
        # Supertrend Assignment
        if trend[i] == 1:
            supertrend[i] = final_lower[i]
        else:
            supertrend[i] = final_upper[i]
            
    df['Supertrend'] = supertrend
    df['Trend'] = trend
    
    # 辅助绘图列
    df['st_green'] = df.apply(lambda x: x['Supertrend'] if x['Trend'] == 1 else np.nan, axis=1)
    df['st_red'] = df.apply(lambda x: x['Supertrend'] if x['Trend'] == -1 else np.nan, axis=1)
    
    return df

# --------------------------
# 3. 主程序执行
# --------------------------
if __name__ == "__main__":
    try:
        # 1. 获取配置参数
        symbol = CONFIG['symbol']
        period = CONFIG['period']
        mult = CONFIG['multiplier']
        limit = CONFIG['limit']
        
        # 2. 获取数据
        df = get_market_data(symbol, limit=limit)
        print(f"📊 数据范围: {df['Date'].iloc[0].strftime('%Y-%m-%d')} 至 {df['Date'].iloc[-1].strftime('%Y-%m-%d')}")
        
        # 3. 计算指标
        df = calculate_supertrend(df, period=period, multiplier=mult)
        
        # 4. 绘图
        fig = go.Figure()
        
        # K线
        fig.add_trace(go.Candlestick(
            x=df['Date'],
            open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'],
            name=f'{symbol} K-Line',
            increasing_line_color='#26a69a',
            decreasing_line_color='#ef5350'
        ))
        
        # 趋势线 (绿色做多)
        fig.add_trace(go.Scatter(
            x=df['Date'], y=df['st_green'], mode='lines',
            line=dict(color='#00c853', width=2), 
            name=f'Supertrend (Buy) P={period}/M={mult}'
        ))
        
        # 趋势线 (红色做空)
        fig.add_trace(go.Scatter(
            x=df['Date'], y=df['st_red'], mode='lines',
            line=dict(color='#ff5252', width=2), 
            name=f'Supertrend (Sell) P={period}/M={mult}'
        ))
        
        # 动态标题
        layout_title = f"<b>{CONFIG['chart_title']}</b><br><sup>Symbol: {symbol} | ATR Period: {period} | Multiplier: {mult}</sup>"
        
        fig.update_layout(
            title=layout_title,
            yaxis_title='Price',
            template='plotly_white',
            height=700,
            xaxis_rangeslider_visible=False,
            hovermode='x unified'
        )
        
        # 保存
        out_file = CONFIG['html_name']
        fig.write_html(out_file)
        print(f"✅ 图表已生成: {out_file}")
        
        # 如果在 Jupyter 中，去掉下面注释可直接显示
        # fig.show()

    except Exception as e:
        traceback.print_exc()
        print(f"❌ 程序运行出错: {e}")
