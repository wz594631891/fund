# 基金数据获取工具

这是一个用于获取基金历史净值数据并保存到数据库的Python脚本项目。

## 功能
- 获取指定基金的历史净值数据
- 支持获取过去3年、1年、半年、1个月的数据
- 数据保存到MySQL数据库

## 安装依赖
```bash
pip install requests pymysql python-dateutil
```

## 使用方法
### 基本使用
```bash
# 获取指定基金的所有历史数据
python get_fund_data.py --fund-code 011062

# 获取指定日期的数据
python get_fund_data.py --fund-code 011062 --date 2024-01-01
```

### 时间范围参数
```bash
# 获取过去1个月的数据
python get_fund_data.py --fund-code 011062 --1m
# 或者
python get_fund_data.py --fund-code 011062 --1-month

# 获取过去6个月的数据
python get_fund_data.py --fund-code 011062 --6m
# 或者
python get_fund_data.py --fund-code 011062 --6-month

# 获取过去1年的数据
python get_fund_data.py --fund-code 011062 --1y
# 或者
python get_fund_data.py --fund-code 011062 --1-year

# 获取过去3年的数据
python get_fund_data.py --fund-code 011062 --3y
# 或者
python get_fund_data.py --fund-code 011062 --3-year
```

## 注意事项
- 需要配置MySQL数据库连接信息
- 同一日期的数据不会重复保存