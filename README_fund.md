# 基金数据获取脚本

这是一个用于获取基金净值数据并存储到数据库的Python脚本。

## 功能

- 获取指定基金的历史净值数据
- 自动创建数据库表（如果不存在）
- 将数据保存到MySQL数据库
- 支持命令行参数指定基金代码

## 安装依赖

```bash
pip install requests pymysql
```

## 使用方法

### 基本使用

```bash
python get_fund_data.py
```

这将默认获取基金代码为`011062`的基金数据并存储到`gfzz`表中。

### 指定基金代码

```bash
python get_fund_data.py --fund 000001
```

这将获取基金代码为`000001`的基金数据。

## 数据库表结构

脚本会自动创建`gfzz`表，表结构如下：

```sql
CREATE TABLE IF NOT EXISTS gfzz (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    nav DECIMAL(10, 4),
    UNIQUE KEY unique_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

## 配置

数据库配置在脚本中定义，默认配置如下：

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'fnd',
    'charset': 'utf8mb4'
}
```

如果需要修改数据库配置，请编辑`get_fund_data.py`文件中的`DB_CONFIG`变量。

## 测试

可以运行以下脚本来测试整个流程：

```bash
python test_full_fund_workflow.py
```

该脚本会依次执行：
1. 测试基金API接口
2. 运行主脚本获取基金数据
3. 检查数据库中的数据

## 文件说明

- `get_fund_data.py`: 主脚本，用于获取基金数据并存储到数据库
- `test_fund_api.py`: 测试基金API接口的脚本
- `check_fund_db.py`: 检查数据库中基金数据的脚本
- `test_full_fund_workflow.py`: 完整流程测试脚本
- `check_db_config.py`: 检查数据库配置的脚本

## 注意事项

- 确保MySQL服务正在运行
- 确保数据库用户具有创建数据库和表的权限
- 脚本会自动处理重复数据，避免重复插入