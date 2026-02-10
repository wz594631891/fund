import requests
import re
import json

def test_fund_api(fund_code):
    """
    测试基金API接口
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
        'pageSize': 20,  # 获取最近20条数据
        'startDate': '',
        'endDate': '',
        '_': '1616749406883'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"请求URL: {response.url}")
        print(f"状态码: {response.status_code}")
        
        # 尝试解析返回的JSONP数据
        if response.status_code == 200:
            json_str = re.search(r'jQuery\d+_\d+\((.*)\)', response.text)
            if json_str:
                print("成功提取JSON部分")
                data = json.loads(json_str.group(1))
                print(f"解析后的数据: {data}")
                if data.get('Data') and data['Data'].get('LSJZList'):
                    print(f"获取到 {len(data['Data']['LSJZList'])} 条记录")
                    
                    # 过滤掉净值为空的记录
                    valid_data = [item for item in data['Data']['LSJZList'] if item.get('DWJZ') and item['DWJZ'] != 'None']
                    print(f"其中有效记录 {len(valid_data)} 条")
                    
                    for item in valid_data[:5]:  # 显示前5条有效记录
                        print(f"  日期: {item.get('FSRQ')}, 净值: {item.get('DWJZ')}")
                else:
                    print("数据结构不符合预期")
            else:
                print("无法提取JSON部分")
        else:
            print(f"请求失败")
            
    except Exception as e:
        print(f"请求出错: {e}")

if __name__ == "__main__":
    # 测试基金代码011062
    test_fund_api("011062")