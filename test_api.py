import requests
import re
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

def test_api(fund_code, start_date=None):
    """
    测试API返回的数据
    """
    # 天天基金网基金净值数据接口
    url = f"http://api.fund.eastmoney.com/f10/lsjz"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'http://fund.eastmoney.com/fund.html'
    }
    
    # 计算一年前的日期
    if not start_date:
        today = datetime.now()
        start_date = (today - relativedelta(years=1)).strftime('%Y-%m-%d')
    
    params = {
        'callback': 'jQuery18307597625546540975_1616749406833',
        'fundCode': fund_code,
        'pageIndex': 1,
        'pageSize': 100,
        'startDate': start_date,
        'endDate': datetime.now().strftime('%Y-%m-%d'),
        '_': '1616749406883'
    }
    
    print(f"请求参数: {params}")
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            # 解析返回的JSONP数据
            json_str = re.search(r'jQuery\d+_\d+\((.*)\)', response.text)
            if json_str:
                data = json.loads(json_str.group(1))
                print(f"API返回的数据: TotalCount = {data.get('Data', {}).get('TotalCount', 0)}")
                print(f"实际返回的数据条数: {len(data.get('Data', {}).get('LSJZList', []))}")
                
                if data.get('Data') and data['Data'].get('LSJZList'):
                    # 显示前几条和后几条数据的日期
                    lsjz_list = data['Data']['LSJZList']
                    print(f"第一条数据日期: {lsjz_list[0].get('FSRQ', 'N/A')}")
                    print(f"最后一条数据日期: {lsjz_list[-1].get('FSRQ', 'N/A')}")
                    
                    # 显示所有数据的日期
                    print("所有数据的日期:")
                    for item in lsjz_list:
                        print(f"  {item.get('FSRQ', 'N/A')}")
                else:
                    print("没有返回净值数据")
            else:
                print("无法解析返回的数据")
        else:
            print(f"请求失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"请求API时出错: {e}")

if __name__ == "__main__":
    # 测试获取基金011062过去一年的数据
    test_api('011062')