import pymysql
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 数据库配置 (使用与nasdaq_crawler.py相同的配置)
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',  # 使用正确的密码
    'charset': 'utf8mb4'
}

def check_database_connection():
    """
    检查数据库连接
    """
    try:
        # 连接数据库
        connection = pymysql.connect(**DB_CONFIG)
        print("数据库连接成功!")
        
        with connection.cursor() as cursor:
            # 查看所有数据库
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            print("\n所有数据库:")
            for db in databases:
                print(f"  - {db[0]}")
                
            # 检查fnd数据库是否存在
            if ('fnd',) in databases:
                print("\nfnd数据库存在")
                # 使用fnd数据库
                cursor.execute("USE fnd")
                
                # 查看所有表
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                print("\nfnd数据库中的表:")
                for table in tables:
                    print(f"  - {table[0]}")
                    
                # 如果gfzz表存在，查看表结构
                if ('gfzz',) in tables:
                    print("\ngfzz表结构:")
                    cursor.execute("DESCRIBE gfzz")
                    columns = cursor.fetchall()
                    for column in columns:
                        print(f"  {column[0]} {column[1]} {column[2]} {column[3]} {column[4]} {column[5]}")
                else:
                    print("\ngfzz表不存在")
            else:
                print("\nfnd数据库不存在")
                
    except Exception as e:
        print(f"检查数据库时出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    check_database_connection()