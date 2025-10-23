import yfinance as yf
import pandas as pd

def get_nasdaq100_latest_data():
    # 纳斯达克100指数的代码为 ^NDX
    ticker = "^NDX"

    # 获取最近2天的日线数据，用于计算涨跌幅（当前交易日和前一交易日）
    data = yf.download(ticker, period='2d', interval='1d')

    if data.empty or len(data) < 2:
        print("未获取到足够数据，请检查网络或指数代码")
        return None

    # 提取最新交易日数据（最后一条）
    latest_data = data.iloc[-1]
    # 提取前一交易日数据（倒数第二条）
    prev_data = data.iloc[-2]

    # 计算涨跌幅（(当前收盘价 - 前一收盘价)/前一收盘价 * 100，保留2位小数）
    price_change_percent = round((latest_data['Close'] - prev_data['Close']) / prev_data['Close'] * 100, 2)

    # 格式化日期（将Timestamp转换为字符串）
    date = latest_data.name.strftime('%Y-%m-%d')

    # 整理结果
    result = {
        '日期': date,
        '指数值（收盘价）': round(latest_data['Close'], 2),
        '涨跌幅（%）': price_change_percent
    }

    return result

if __name__ == "__main__":
    nasdaq_data = get_nasdaq100_latest_data()
    if nasdaq_data:
        print("纳斯达克100指数最近一天数据：")
        for key, value in nasdaq_data.items():
            print(f"{key}: {value}")
    else:
        print("无法获取有效的指数数据")
