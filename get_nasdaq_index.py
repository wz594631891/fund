import yfinance as yf
import pandas as pd
import argparse
import pymysql
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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
    # 处理可能的pandas Series数据类型
    current_close = latest_data['Close']
    prev_close = prev_data['Close']
    
    if hasattr(current_close, 'values'):
        current_close = current_close.values[0] if len(current_close.values) > 0 else current_close
        
    if hasattr(prev_close, 'values'):
        prev_close = prev_close.values[0] if len(prev_close.values) > 0 else prev_close
    
    price_change_percent = round((float(current_close) - float(prev_close)) / float(prev_close) * 100, 2)

    # 格式化日期（将Timestamp转换为字符串）
    date = latest_data.name.strftime('%Y-%m-%d')

    # 整理结果
    # 处理可能的pandas Series数据类型
    close_value = latest_data['Close']
    if hasattr(close_value, 'values'):
        close_value = close_value.values[0] if len(close_value.values) > 0 else close_value
    
    result = {
        '日期': date,
        '指数值（收盘价）': round(float(close_value), 2),
        '涨跌幅（%）': price_change_percent
    }

    return result


def get_nasdaq100_data_for_date(target_date):
    """
    获取指定日期的纳斯达克100指数数据
    
    Args:
        target_date (str): 目标日期，格式为 YYYY-MM-DD
        
    Returns:
        dict: 包含日期、指数值和涨跌幅的字典，如果获取失败则返回None
    """
    # 纳斯达克100指数的代码为 ^NDX
    ticker = "^NDX"
    
    # 将目标日期转换为datetime对象
    try:
        from datetime import datetime, timedelta
        target_dt = datetime.strptime(target_date, '%Y-%m-%d')
    except ValueError:
        print(f"日期格式错误: {target_date}，应为 YYYY-MM-DD 格式")
        return None
    
    # 设置日期范围，前后各扩展几天以确保能获取到数据
    start_date = target_dt - timedelta(days=5)
    end_date = target_dt + timedelta(days=5)
    
    # 获取指定日期范围的数据
    try:
        data = yf.download(ticker, start=start_date.strftime('%Y-%m-%d'), 
                          end=end_date.strftime('%Y-%m-%d'), interval='1d')
        
        if data.empty:
            print(f"未获取到 {target_date} 前后的数据，请检查网络或指数代码")
            return None
            
        # 查找最接近目标日期的数据
        # 由于股市不是每天都开盘，我们需要找到最接近目标日期的交易日数据
        closest_date = None
        min_diff = float('inf')
        
        for date_idx in data.index:
            date_str = date_idx.strftime('%Y-%m-%d')
            date_diff = abs((date_idx - target_dt).days)
            
            if date_diff < min_diff:
                min_diff = date_diff
                closest_date = date_idx
        
        if closest_date is None:
            print(f"未找到 {target_date} 附近的交易日数据")
            return None
            
        # 获取最接近日期的数据
        target_data = data.loc[closest_date]
        
        # 如果最接近的日期与目标日期相差太大，可能意味着那天没有交易
        if min_diff > 3:
            print(f"警告: {target_date} 可能是非交易日，使用最近的交易日 {closest_date.strftime('%Y-%m-%d')} 的数据")
        
        # 获取前一天的数据用于计算涨跌幅
        # 我们需要找到目标日期之前的交易日
        prev_dates = [d for d in data.index if d < closest_date]
        if not prev_dates:
            print(f"无法计算 {closest_date.strftime('%Y-%m-%d')} 的涨跌幅，缺少前一日数据")
            return None
            
        # 获取最近的前一个交易日
        prev_date = max(prev_dates)
        prev_data = data.loc[prev_date]
        
        # 计算涨跌幅（(当前收盘价 - 前一收盘价)/前一收盘价 * 100，保留2位小数）
        price_change_percent = round((target_data['Close'] - prev_data['Close']) / prev_data['Close'] * 100, 2)
        
        # 格式化日期
        date = closest_date.strftime('%Y-%m-%d')
        
        # 整理结果
        # 处理可能的pandas Series数据类型
        close_value = target_data['Close']
        if hasattr(close_value, 'values'):
            close_value = close_value.values[0] if len(close_value.values) > 0 else close_value
            
        prev_close_value = prev_data['Close']
        if hasattr(prev_close_value, 'values'):
            prev_close_value = prev_close_value.values[0] if len(prev_close_value.values) > 0 else prev_close_value
            
        # 重新计算涨跌幅以确保使用正确的数值
        price_change_percent = round((float(close_value) - float(prev_close_value)) / float(prev_close_value) * 100, 2)
        
        result = {
            '日期': date,
            '指数值（收盘价）': round(float(close_value), 2),
            '涨跌幅（%）': price_change_percent
        }
        
        return result
        
    except Exception as e:
        print(f"获取 {target_date} 的数据时出错: {e}")
        return None

def fill_missing_index_data():
    """
    填充数据库中index_value为空的记录
    """
    # 数据库配置（与nasdaq_crawler.py保持一致）
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'root',
        'charset': 'utf8mb4',
        'database': 'fnd'
    }
    
    try:
        # 连接数据库
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        
        # 查询index_value为空的所有记录
        select_sql = "SELECT id, date FROM nasdaq WHERE index_value IS NULL OR index_value = ''"
        cursor.execute(select_sql)
        records = cursor.fetchall()
        
        if not records:
            print("没有发现index_value为空的记录")
            return
            
        print(f"发现 {len(records)} 条index_value为空的记录，开始填充数据...")
        
        # 逐条处理每条记录
        for record in records:
            record_id, record_date = record
            date_str = record_date.strftime('%Y-%m-%d')
            
            print(f"正在处理日期: {date_str}")
            
            # 获取该日期的指数数据
            index_data = get_nasdaq100_data_for_date(date_str)
            
            if index_data:
                index_value = index_data['指数值（收盘价）']
                rise_rate = index_data['涨跌幅（%）']
                
                # 更新数据库记录
                update_sql = """
                    UPDATE nasdaq 
                    SET index_value = %s, rise_rate = %s 
                    WHERE id = %s
                """
                cursor.execute(update_sql, (index_value, rise_rate, record_id))
                conn.commit()
                
                print(f"  成功更新记录 (ID: {record_id}) - 指数值: {index_value}, 涨跌幅: {rise_rate}%")
            else:
                print(f"  未能获取到 {date_str} 的指数数据，跳过该记录")
                
        print("数据填充完成")
        
    except Exception as e:
        print(f"填充数据时发生错误: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='纳斯达克100指数数据获取工具')
    parser.add_argument('--fill', nargs='?', const='all', default=None, 
                       help='填充数据库中index_value为空的记录。如果不指定日期，则填充所有空记录；如果指定日期（格式：YYYY-MM-DD），则只填充该日期的记录')
    
    args = parser.parse_args()
    
    if args.fill:
        if args.fill == 'all':
            # 执行填充所有空记录的功能
            fill_missing_index_data()
        else:
            # 填充指定日期的记录
            # 首先验证日期格式
            try:
                from datetime import datetime
                target_date = datetime.strptime(args.fill, '%Y-%m-%d')
                
                # 获取该日期的数据
                print(f"正在获取 {args.fill} 的纳斯达克100指数数据...")
                index_data = get_nasdaq100_data_for_date(args.fill)
                
                if index_data:
                    print(f"获取到 {args.fill} 的数据：")
                    for key, value in index_data.items():
                        print(f"{key}: {value}")
                    
                    # 连接数据库并更新记录
                    db_config = {
                        'host': 'localhost',
                        'user': 'root',
                        'password': 'root',
                        'charset': 'utf8mb4',
                        'database': 'fnd'
                    }
                    
                    try:
                        conn = pymysql.connect(**db_config)
                        cursor = conn.cursor()
                        
                        # 查找该日期的记录
                        select_sql = "SELECT id FROM nasdaq WHERE date = %s"
                        cursor.execute(select_sql, (args.fill,))
                        record = cursor.fetchone()
                        
                        if record:
                            record_id = record[0]
                            index_value = index_data['指数值（收盘价）']
                            rise_rate = index_data['涨跌幅（%）']
                            
                            # 更新数据库记录
                            update_sql = """
                                UPDATE nasdaq 
                                SET index_value = %s, rise_rate = %s 
                                WHERE id = %s
                            """
                            cursor.execute(update_sql, (index_value, rise_rate, record_id))
                            conn.commit()
                            
                            print(f"成功更新数据库中 {args.fill} 的记录")
                        else:
                            print(f"数据库中未找到 {args.fill} 的记录")
                            
                    except Exception as e:
                        print(f"更新数据库时发生错误: {e}")
                        if conn:
                            conn.rollback()
                    finally:
                        if cursor:
                            cursor.close()
                        if conn:
                            conn.close()
                else:
                    print(f"无法获取 {args.fill} 的指数数据")
            except ValueError:
                print(f"日期格式错误: {args.fill}，应为 YYYY-MM-DD 格式")
    else:
        # 默认行为：获取最新的指数数据
        nasdaq_data = get_nasdaq100_latest_data()
        if nasdaq_data:
            print("纳斯达克100指数最近一天数据：")
            for key, value in nasdaq_data.items():
                print(f"{key}: {value}")
        else:
            print("无法获取有效的指数数据")
