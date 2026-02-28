# 总体设计
py爬虫+数据库
# 页面
https://www.gurufocus.com/economic_indicators/6778/nasdaq-100-pe-ratio
# 数据项
id
date
value
current_datetime
# 爬虫
## 初次
打开页面,获取date,value,翻页,获取下一页date,value,直到最后一页(存入前验证是否存在重复date的记录)
## 定时
每天定时打开页面,获取date,value,存入数据库(存入前验证是否存在重复date的记录)
# 流程
获取元素:date,value
