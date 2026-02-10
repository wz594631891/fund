import requests
import re
import json
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

def test_api_improved(fund_code):
    """
    改进的API测试，尝试获取更多数据
    """
    # 天天基金网基金净值数据接口
    url = f"http://api.fund.eastmoney.com/f10/lsjz"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'http://fund.eastmoney.com/fund.html'
    }
    
    # 尝试获取更多数据
    page_index = 1
    page_size = 100  # 增大每页数据量
    all_data = []
    
    # 获取多页数据
    for i in range(5):  # 尝试获取5页数据
        params = {
            'callback': f'jQuery18307597625546540975_1616749406833',
            'fundCode': fund_code,
            'pageIndex': page_index,
            'pageSize': page_size,
            '_': '1616749406883'
        }
        
        print(f"请求第 {page_index} 页数据...")
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                # 解析返回的JSONP数据
                json_str = re.search(r'jQuery\d+_\d+\((.*)\)', response.text)
                if json_str:
                    data = json.loads(json_str.group(1))
                    if data.get('Data') and data['Data'].get('LSJZList'):
                        # 添加到所有数据中
                        all_data.extend(data['Data']['LSJZList'])
                        print(f"第 {page_index} 页返回 {len(data['Data']['LSJZList'])} 条数据")
                        
                        # 检查是否还有更多数据
                        total_count = data['Data'].get('TotalCount', 0)
                        print(f"总数据量: {total_count}")
                        
                        # 翻页
                        page_index += 1
                        # 添加延时，避免请求过于频繁
                        time.sleep(1)
                    else:
                        print("没有返回净值数据")
                        break
                else:
                    print("无法解析返回的数据")
                    break
            else:
                print(f"请求失败，状态码: {response.status_code}")
                break
        except Exception as e:
            print(f"请求API时出错: {e}")
            break
    
    print(f"\n总共获取到 {len(all_data)} 条数据")
    
    if all_data:
        # 显示前几条和后几条数据的日期
        print(f"第一条数据日期: {all_data[0].get('FSRQ', 'N/A')}")
        print(f"最后一条数据日期: {all_data[-1].get('FSRQ', 'N/A')}")
        
        # 显示所有数据的日期（只显示前10条和后10条）
        print("\n前10条数据的日期:")
        for i, item in enumerate(all_data[:10]):
            print(f"  {i+1}. {item.get('FSRQ', 'N/A')}")
        
        if len(all_data) > 10:
            print("\n后10条数据的日期:")
            for i, item in enumerate(all_data[-10:]):
                print(f"  {len(all_data)-10+i+1}. {item.get('FSRQ', 'N/A')}")

if __name__ == "__main__":
    # 测试获取基金011062的数据
    test_api_improved('011062')