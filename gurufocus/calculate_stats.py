import sqlite3
from datetime import datetime, timedelta
import numpy as np

def calculate_percentile(data, percentile):
    """计算分位值"""
    if not data or len(data) == 0:
        return None
    sorted_data = sorted(data)
    index = (len(sorted_data) - 1) * percentile / 100
    lower = int(index)
    upper = lower + 1
    if upper >= len(sorted_data):
        return sorted_data[-1]
    weight = index - lower
    return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight

def calculate_stats(db_path="gurufocus_data.db"):
    """计算统计数据并更新到数据库"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取所有 PE 数据，按日期排序
        cursor.execute("""
            SELECT id, date, value FROM data 
            WHERE value IS NOT NULL AND value != '' 
            ORDER BY date DESC
        """)
        rows = cursor.fetchall()
        
        if not rows:
            print("没有 PE 数据")
            conn.close()
            return
        
        # 转换为 datetime 并过滤无效数据
        data_with_dates = []
        for row in rows:
            try:
                pe_value = float(row[2].replace(',', ''))
                date_str = row[1]
                # 尝试解析日期
                try:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    data_with_dates.append((row[0], date_obj, pe_value))
                except:
                    try:
                        date_obj = datetime.strptime(date_str, "%Y/%m/%d")
                        data_with_dates.append((row[0], date_obj, pe_value))
                    except:
                        pass
            except:
                pass
        
        if not data_with_dates:
            print("没有有效的 PE 数据")
            conn.close()
            return
        
        # 按日期排序
        data_with_dates.sort(key=lambda x: x[1], reverse=True)
        
        print(f"共 {len(data_with_dates)} 条有效数据")
        
        # 计算每个数据点的统计值
        updated_count = 0
        for i, (id, current_date, current_pe) in enumerate(data_with_dates):
            # 3 年数据
            three_years_ago = current_date - timedelta(days=3*365)
            three_year_data = [
                item[2] for item in data_with_dates 
                if three_years_ago <= item[1] <= current_date
            ]
            
            # 5 年数据
            five_years_ago = current_date - timedelta(days=5*365)
            five_year_data = [
                item[2] for item in data_with_dates 
                if five_years_ago <= item[1] <= current_date
            ]
            
            # 10 年数据
            ten_years_ago = current_date - timedelta(days=10*365)
            ten_year_data = [
                item[2] for item in data_with_dates 
                if ten_years_ago <= item[1] <= current_date
            ]
            
            # 计算统计值
            stats = {}
            
            # 3 年统计
            if len(three_year_data) >= 2:
                stats['three_year_20pct'] = calculate_percentile(three_year_data, 20)
                stats['three_year_50pct'] = calculate_percentile(three_year_data, 50)
                stats['three_year_80pct'] = calculate_percentile(three_year_data, 80)
                stats['mean_value_3y'] = np.mean(three_year_data)
                stats['std_3y'] = np.std(three_year_data)
                stats['one_std_dev_3y'] = stats['mean_value_3y'] + stats['std_3y']
                stats['minus_one_std_dev_3y'] = stats['mean_value_3y'] - stats['std_3y']
                # 当前分位值
                stats['current_percentile_3year'] = (
                    sum(1 for x in three_year_data if x < current_pe) / len(three_year_data) * 100
                )
            
            # 5 年统计
            if len(five_year_data) >= 2:
                stats['five_year_20pct'] = calculate_percentile(five_year_data, 20)
                stats['five_year_50pct'] = calculate_percentile(five_year_data, 50)
                stats['five_year_80pct'] = calculate_percentile(five_year_data, 80)
                stats['mean_value_5y'] = np.mean(five_year_data)
                stats['std_5y'] = np.std(five_year_data)
                stats['one_std_dev_5y'] = stats['mean_value_5y'] + stats['std_5y']
                stats['minus_one_std_dev_5y'] = stats['mean_value_5y'] - stats['std_5y']
                # 当前分位值
                stats['current_percentile_5year'] = (
                    sum(1 for x in five_year_data if x < current_pe) / len(five_year_data) * 100
                )
            
            # 10 年统计
            if len(ten_year_data) >= 2:
                stats['ten_year_20pct'] = calculate_percentile(ten_year_data, 20)
                stats['ten_year_50pct'] = calculate_percentile(ten_year_data, 50)
                stats['ten_year_80pct'] = calculate_percentile(ten_year_data, 80)
                stats['mean_value_10y'] = np.mean(ten_year_data)
                stats['std_10y'] = np.std(ten_year_data)
                stats['one_std_dev_10y'] = stats['mean_value_10y'] + stats['std_10y']
                stats['minus_one_std_dev_10y'] = stats['mean_value_10y'] - stats['std_10y']
                # 当前分位值
                stats['current_percentile_10year'] = (
                    sum(1 for x in ten_year_data if x < current_pe) / len(ten_year_data) * 100
                )
            
            # 更新数据库
            if stats:
                cursor.execute("""
                    UPDATE data SET
                        one_std_dev_3y = ?,
                        mean_value_3y = ?,
                        minus_one_std_dev_3y = ?,
                        one_std_dev_5y = ?,
                        mean_value_5y = ?,
                        minus_one_std_dev_5y = ?,
                        one_std_dev_10y = ?,
                        mean_value_10y = ?,
                        minus_one_std_dev_10y = ?,
                        three_year_20pct = ?,
                        three_year_50pct = ?,
                        three_year_80pct = ?,
                        five_year_20pct = ?,
                        five_year_50pct = ?,
                        five_year_80pct = ?,
                        ten_year_20pct = ?,
                        ten_year_50pct = ?,
                        ten_year_80pct = ?,
                        current_percentile_3year = ?,
                        current_percentile_5year = ?,
                        current_percentile_10year = ?
                    WHERE id = ?
                """, (
                    stats.get('one_std_dev_3y'),
                    stats.get('mean_value_3y'),
                    stats.get('minus_one_std_dev_3y'),
                    stats.get('one_std_dev_5y'),
                    stats.get('mean_value_5y'),
                    stats.get('minus_one_std_dev_5y'),
                    stats.get('one_std_dev_10y'),
                    stats.get('mean_value_10y'),
                    stats.get('minus_one_std_dev_10y'),
                    stats.get('three_year_20pct'),
                    stats.get('three_year_50pct'),
                    stats.get('three_year_80pct'),
                    stats.get('five_year_20pct'),
                    stats.get('five_year_50pct'),
                    stats.get('five_year_80pct'),
                    stats.get('ten_year_20pct'),
                    stats.get('ten_year_50pct'),
                    stats.get('ten_year_80pct'),
                    stats.get('current_percentile_3year'),
                    stats.get('current_percentile_5year'),
                    stats.get('current_percentile_10year'),
                    id
                ))
                updated_count += 1
                
                if updated_count % 100 == 0:
                    print(f"已更新 {updated_count} 条记录...")
        
        conn.commit()
        print(f"计算完成，共更新 {updated_count} 条记录")
        conn.close()
        
    except Exception as e:
        print(f"计算出错：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    calculate_stats()
