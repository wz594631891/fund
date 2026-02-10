import pymysql
import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 数据库配置(使用与nasdaq_crawler.py相同的配置)
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'fnd',
    'charset': 'utf8mb4'
}

def check_fund_data():
    """
    检查基金数据是否正确保存到数据库
    """
    try:
        # 连接数据库
        connection = pymysql.connect(**DB_CONFIG)
        with connection.cursor() as cursor:
            # 查询gfzz表中的数据
            sql = "SELECT date, nav FROM gfzz ORDER BY date DESC"      
            cursor.execute(sql)
            results = cursor.fetchall()

            if results:
                print("数据库中的基金数据:")
                print("日期\t\t净值")
                print("-" * 20)
                for row in results:
                    print(f"{row[0]}\t{row[1]}")
            else:
                print("数据库中没有找到基金数据")

            cursor.execute("SELECT COUNT(*) FROM gfzz")
            count = cursor.fetchone()[0]
            print(f"\n总记录数: {count}")
            
            # 检查数据的时间范围
            if results:
                earliest_date = results[-1][0]  # 最早的日期
                latest_date = results[0][0]     # 最晚的日期
                print(f"\n数据时间范围: {earliest_date} 到 {latest_date}")

    except Exception as e:
        print(f"检查数据库时出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    check_fund_data()