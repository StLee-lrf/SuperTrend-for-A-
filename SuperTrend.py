import pandas as pd
import numpy as np
import plotly.graph_objects as go
import akshare as ak
from datetime import datetime

# --------------------------
# 1. 获取数据 (策略：改用 ETF 数据，稳定且极易获取)
# --------------------------
def get_satellite_etf_data(symbol='562590', limit=700):
    """
    获取 华夏中证卫星应用产业ETF (562590) 的历史数据
    作为 931065 指数的完美替代。
    """
    print(f"🔄 正在获取 卫星应用ETF ({symbol}) 数据...")
    
    try:
        # 使用 东方财富 ETF 历史数据接口 (极其稳定)
        df = ak.fund_etf_hist_em(symbol=symbol, period="daily", adjust="qfq")
        
        # 打印一下原始列名，确保万无一失
        # print(f"   接口返回列名: {df.columns.tolist()}")
        
        # 标准列名清洗
        rename_map = {
            '日期': 'Date',
            '开盘': 'Open',
            '收盘': 'Close',
            '最高': 'High',
            '最低': 'Low',
            '成交量': 'Volume'
        }
        df.rename(columns=rename_map, inplace=True)
        
        # 确保关键列存在
        required_cols = ['Date', 'Open', 'High', 'Low', 'Close']
        if not all(col in df.columns for col in required_cols):
             # 备用方案：防止列名微调
             df.columns = ['Date', 'Open', 'Close', 'High', 'Low', 'Volume', 'Turnover', 'Amplitude'] # 典型东财顺序
        
        # 格式转换
        df['Date'] = pd.to_datetime(df['Date'])
        for c in ['Open', 'High', 'Low', 'Close']:
            df[c] = pd.to_numeric(df[c], errors='coerce')
            
        # 排序
        df = df.sort_values('Date').reset_index(drop=True)
        
        # 截取最近数据
        if len(df) > limit:
            df = df.iloc[-limit:].reset_index(drop=True)
            
        return df[['Date', 'Open', 'High', 'Low', 'Close']]

    except Exception as e:
        print(f"❌ ETF 数据获取失败: {e}")
        # 如果 akshare 版本极老，可能没有 fund_etf_hist_em，尝试 stock_zh_a_hist
        try:
            print("⚠️ 尝试备用接口 (stock_zh_a_hist)...")
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
            df.rename(columns={'日期':'Date','开盘':'Open','收盘':'Close','最高':'High','最低':'Low'}, inplace=True)
            df['Date'] = pd.to_datetime(df['Date'])
            return df[['Date', 'Open', 'High', 'Low', 'Close']].tail(limit)
        except Exception as e2:
            raise Exception(f"所有接口均失败，请检查网络或 pip install --upgrade akshare. Error: {e2}")

# --------------------------
# 2. Supertrend 计算逻辑 (完全一致)
# --------------------------
def calculate_supertrend(df, period=10, multiplier=3):
    df = df.copy()
    # TR Calculation
    df['tr0'] = abs(df['High'] - df['Low'])
    df['tr1'] = abs(df['High'] - df['Close'].shift(1))
    df['tr2'] = abs(df['Low'] - df['Close'].shift(1))
    df['tr'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)
    
    # ATR (RMA)
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
        # Upper
        if df['basic_upper'][i] < final_upper[i-1] or df['Close'][i-1] > final_upper[i-1]:
            final_upper[i] = df['basic_upper'][i]
        else:
            final_upper[i] = final_upper[i-1]
        # Lower
        if df['basic_lower'][i] > final_lower[i-1] or df['Close'][i-1] < final_lower[i-1]:
            final_lower[i] = df['basic_lower'][i]
        else:
            final_lower[i] = final_lower[i-1]
            
        # Trend
        trend[i] = trend[i-1]
        if trend[i] == 1:
            if df['Close'][i] < final_lower[i]:
                trend[i] = -1
        else:
            if df['Close'][i] > final_upper[i]:
                trend[i] = 1
                
        if trend[i] == 1:
            supertrend[i] = final_lower[i]
        else:
            supertrend[i] = final_upper[i]
            
    df['Supertrend'] = supertrend
    df['Trend'] = trend
    df['st_green'] = df.apply(lambda x: x['Supertrend'] if x['Trend'] == 1 else np.nan, axis=1)
    df['st_red'] = df.apply(lambda x: x['Supertrend'] if x['Trend'] == -1 else np.nan, axis=1)
    
    return df

# --------------------------
# 3. 主程序
# --------------------------
try:
    # 使用 562590 (华夏卫星应用ETF) 代替指数
    df = get_satellite_etf_data(symbol='562590', limit=700)
    print(f"✅ 获取成功! 数据截止日期: {df['Date'].iloc[-1].strftime('%Y-%m-%d')}")
    print(f"   (使用 '卫星应用ETF-562590' 作为 '931065指数' 的趋势代理)")
    
    # 计算
    df = calculate_supertrend(df, period=10, multiplier=3)
    
    # 绘图
    fig = go.Figure()
    
    # K线
    fig.add_trace(go.Candlestick(
        x=df['Date'],
        open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        name='Satellite ETF (562590)',
        increasing_line_color='#26a69a',
        decreasing_line_color='#ef5350'
    ))
    
    # 趋势线
    fig.add_trace(go.Scatter(
        x=df['Date'], y=df['st_green'], mode='lines',
        line=dict(color='#00c853', width=2), name='Buy Zone'
    ))
    fig.add_trace(go.Scatter(
        x=df['Date'], y=df['st_red'], mode='lines',
        line=dict(color='#ff5252', width=2), name='Sell Zone'
    ))
    
    fig.update_layout(
        title='<b>Satellite App Industry ETF (562590) Supertrend</b><br><sup>Proxy for Index 931065</sup>',
        yaxis_title='Price',
        template='plotly_white',
        height=700,
        xaxis_rangeslider_visible=False
    )
    
    file_name = "satellite_etf_supertrend.html"
    fig.write_html(file_name)
    print(f"✅ 成功生成图表: {file_name}")

except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"❌ 依然报错: {e}")