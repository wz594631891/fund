import requests
import pymysql
import argparse
import os
import sys
import re
import json
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def get_fund_data(fund_code, start_date=None):
    """
    从天天基金网获取基金净值数据
    
    Args:
        fund_code (str): 基金代码
        start_date (str, optional): 开始日期，格式为 YYYY-MM-DD。默认为None，表示获取所有历史数据
        
    Returns:
        list: 包含日期和净值的元组列表
    """
    # 天天基金网基金净值数据接口
    url = f"http://api.fund.eastmoney.com/f10/lsjz"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'http://fund.eastmoney.com/fund.html'
    }
    
    # 初始化参数
    page_index = 1
    page_size = 100  # 每页获取100条数据
    all_data = []
    
    # 最多获取10页数据（1000条记录）
    max_pages = 10
    
    while page_index <= max_pages:
        params = {
            'callback': f'jQuery18307597625546540975_1616749406833',
            'fundCode': fund_code,
            'pageIndex': page_index,
            'pageSize': page_size,
            '_': '1616749406883'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                # 解析返回的JSONP数据
                json_str = re.search(r'jQuery\d+_\d+\((.*)\)', response.text)
                if json_str:
                    data = json.loads(json_str.group(1))
                    if data.get('Data') and data['Data'].get('LSJZList'):
                        # 过滤掉净值为空的记录
                        valid_data = []
                        for item in data['Data']['LSJZList']:
                            if item.get('DWJZ') and item['DWJZ'] != 'None':
                                try:
                                    valid_data.append((item['FSRQ'], float(item['DWJZ'])))
                                except ValueError:
                                    # 跳过无法转换为浮点数的净值
                                    continue
                        
                        # 添加到所有数据中
                        all_data.extend(valid_data)
                        
                        # 如果指定了开始日期，检查获取到的数据是否已经超出了日期范围
                        if start_date:
                            # 检查最后一条数据的日期是否早于开始日期
                            last_date = valid_data[-1][0] if valid_data else None
                            if last_date:
                                # 将字符串日期转换为日期对象进行比较
                                last_date_obj = datetime.strptime(last_date, '%Y-%m-%d').date()
                                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                                if last_date_obj < start_date_obj:
                                    # 如果最后一条数据的日期早于开始日期，则停止获取更多数据
                                    break
                        
                        # 翻页
                        page_index += 1
                        # 添加延时，避免请求过于频繁
                        time.sleep(0.5)
                    else:
                        break
                else:
                    break
            else:
                print(f"请求失败，状态码: {response.status_code}")
                break
        except Exception as e:
            print(f"获取基金数据时出错: {e}")
            break
    
    # 如果指定了开始日期，过滤掉早于开始日期的数据
    if start_date:
        filtered_data = []
        for date_str, nav in all_data:
            # 将字符串日期转换为日期对象进行比较
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            if date_obj >= start_date_obj:
                filtered_data.append((date_str, nav))
        all_data = filtered_data
    
    return all_data

def create_gfzz_table():
    """
    创建gfzz表（如果不存在）
    """
    # 数据库配置 (与nasdaq_crawler.py保持一致)
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
        
        # 创建gfzz表（如果不存在）
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS gfzz (
                id INT AUTO_INCREMENT PRIMARY KEY,
                date DATE NOT NULL,
                nav DECIMAL(10, 4) DEFAULT NULL,
                UNIQUE KEY unique_date (date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        cursor.execute(create_table_sql)
        conn.commit()
        print("gfzz表已创建或已存在")
        
    except Exception as e:
        print(f"创建gfzz表时出错: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def save_fund_data_to_db(fund_data):
    """
    将基金数据保存到数据库
    
    Args:
        fund_data (list): 包含日期和净值的元组列表
    """
    # 数据库配置 (与nasdaq_crawler.py保持一致)
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
        
        # 插入或更新数据
        insert_sql = """
            INSERT INTO gfzz (date, nav) 
            VALUES (%s, %s) 
            ON DUPLICATE KEY UPDATE nav = VALUES(nav)
        """
        
        inserted_count = 0
        updated_count = 0
        
        for date, nav in fund_data:
            try:
                cursor.execute(insert_sql, (date, nav))
                if cursor.rowcount == 1:
                    inserted_count += 1
                elif cursor.rowcount == 2:
                    updated_count += 1
            except Exception as e:
                print(f"插入数据时出错 (日期: {date}): {e}")
        
        conn.commit()
        print(f"数据保存完成: 新增 {inserted_count} 条记录, 更新 {updated_count} 条记录")
        
    except Exception as e:
        print(f"保存基金数据到数据库时出错: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def calculate_date_range(period):
    """
    根据指定周期计算日期范围
    
    Args:
        period (str): 时间周期 ('3y', '1y', '6m', '1m')
        
    Returns:
        str: 开始日期，格式为 YYYY-MM-DD
    """
    today = datetime.now()
    
    if period == '3y':
        # 过去3年
        start_date = today - relativedelta(years=3)
    elif period == '1y':
        # 过去1年
        start_date = today - relativedelta(years=1)
    elif period == '6m':
        # 过去6个月
        start_date = today - relativedelta(months=6)
    elif period == '1m':
        # 过去1个月
        start_date = today - relativedelta(months=1)
    else:
        # 默认返回3年前
        start_date = today - relativedelta(years=3)
    
    return start_date.strftime('%Y-%m-%d')


def get_fund_data_by_date(fund_code, target_date):
    """
    获取指定日期的基金净值
    
    Args:
        fund_code (str): 基金代码
        target_date (str): 目标日期，格式为 YYYY-MM-DD
        
    Returns:
        tuple: (日期, 净值) 或 None
    """
    # 天天基金网基金净值数据接口
    url = f"http://api.fund.eastmoney.com/f10/lsjz"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'http://fund.eastmoney.com/fund.html'
    }
    
    params = {
        'callback': 'jQuery18307597625546540975_1616749406833',
        'fundCode': fund_code,
        'pageIndex': 1,
        'pageSize': 100,  # 获取最近100条数据
        'startDate': target_date,
        'endDate': target_date,
        '_': '1616749406883'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            # 解析返回的JSONP数据
            import re
            import json
            
            # 提取JSON部分
            json_str = re.search(r'jQuery\d+_\d+\((.*)\)', response.text)
            if json_str:
                data = json.loads(json_str.group(1))
                if data.get('Data') and data['Data'].get('LSJZList'):
                    for item in data['Data']['LSJZList']:
                        # 查找指定日期的数据
                        if item.get('FSRQ') == target_date and item.get('NAV'):
                            try:
                                # 转换日期格式
                                date = datetime.strptime(item['FSRQ'], '%Y-%m-%d').date()
                                # 转换净值为浮点数
                                nav = float(item['NAV'])
                                return (date, nav)
                            except ValueError:
                                continue
            else:
                print("无法解析返回的数据")
        else:
            print(f"请求失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"获取基金数据时出错: {e}")
    
    return None

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='基金净值数据获取工具')
    parser.add_argument('--fund-code', default='011062', help='基金代码，默认为011062')
    parser.add_argument('--date', help='指定日期获取净值数据（格式：YYYY-MM-DD）')
    
    # 创建互斥参数组，用于指定时间范围
    period_group = parser.add_mutually_exclusive_group()
    period_group.add_argument('--3y', '--3-year', action='store_true', help='获取过去3年的数据')
    period_group.add_argument('--1y', '--1-year', action='store_true', help='获取过去1年的数据')
    period_group.add_argument('--6m', '--6-month', action='store_true', help='获取过去6个月的数据')
    period_group.add_argument('--1m', '--1-month', action='store_true', help='获取过去1个月的数据')
    
    args = parser.parse_args()
    
    # 创建gfzz表
    create_gfzz_table()
    
    if args.date:
        # 获取指定日期的数据
        print(f"正在获取基金 {args.fund_code} 在 {args.date} 的净值数据...")
        fund_data = get_fund_data_by_date(args.fund_code, args.date)
        if fund_data:
            print(f"获取到数据: 日期={fund_data[0]}, 净值={fund_data[1]}")
            # 保存到数据库
            save_fund_data_to_db([fund_data])
        else:
            print(f"未能获取到 {args.date} 的净值数据")
    else:
        # 确定数据获取的时间范围
        period = None
        if getattr(args, '3y'):
            period = '3y'
        elif getattr(args, '1y'):
            period = '1y'
        elif getattr(args, '6m'):
            period = '6m'
        elif getattr(args, '1m'):
            period = '1m'
        
        # 如果指定了时间范围，则获取相应时间段的数据
        if period:
            start_date = calculate_date_range(period)
            print(f"正在获取基金 {args.fund_code} 从 {start_date} 到今天 的历史净值数据...")
            fund_data = get_fund_data(args.fund_code, start_date=start_date)
        else:
            # 默认获取所有历史数据
            print(f"正在获取基金 {args.fund_code} 的历史净值数据...")
            fund_data = get_fund_data(args.fund_code)
        
        if fund_data:
            print(f"获取到 {len(fund_data)} 条净值数据")
            # 保存到数据库
            save_fund_data_to_db(fund_data)
            print("数据已保存到数据库")
        else:
            print("未能获取到基金净值数据")