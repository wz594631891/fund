import pymysql

# 数据库配置
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
    select_sql = "SELECT id, date, index_value, rise_rate FROM nasdaq WHERE index_value IS NULL OR index_value = ''"
    cursor.execute(select_sql)
    records = cursor.fetchall()
    
    print(f"发现 {len(records)} 条index_value为空的记录:")
    for record in records:
        print(f"  ID: {record[0]}, Date: {record[1]}, Index Value: {record[2]}, Rise Rate: {record[3]}")
        
except Exception as e:
    print(f"查询数据库时发生错误: {e}")
finally:
    if cursor:
        cursor.close()
    if conn:
        conn.close()