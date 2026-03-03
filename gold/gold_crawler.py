import time
import sqlite3
import argparse
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class GoldReserveCrawler:
    def __init__(self, user_data_dir, chrome_binary, driver_path):
        self.options = Options()
        self.options.add_argument(f'--user-data-dir={user_data_dir}')
        self.options.add_argument('--no-sandbox')
        self.options.binary_location = chrome_binary
        
        self.driver = webdriver.Chrome(
            executable_path=driver_path,
            options=self.options
        )
        
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        
        self.db_path = "gold_reserve_data.db"
        self._create_database()

    def _create_database(self):
        """创建数据库，包含原始文本、万盎司数值和吨数值"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS gold_reserve (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER,
                month INTEGER,
                raw_text TEXT,          -- 原始采集内容 (如: 7419万盎司)
                ounces_numeric REAL,    -- 纯数字万盎司 (如: 7419.0)
                tons_numeric REAL,      -- 转换后的吨数 (如: 2307.57)
                current_datetime TEXT,
                UNIQUE(year, month)
            )
        """)
        conn.close()

    def _convert_to_tons(self, text):
        """将包含'万盎司'的字符串转为纯数字和吨"""
        try:
            # 使用正则提取数字部分，支持逗号分隔符和浮点数
            match = re.search(r'([\d,.]+)', text)
            if match:
                clean_num = float(match.group(1).replace(',', ''))
                # 转换公式: 1万盎司 = 0.311034768 吨
                tons = clean_num * 0.311034768
                return clean_num, round(tons, 2)
            return None, None
        except Exception as e:
            print(f"数据转换失败: {e}")
            return None, None

    def get_page_data(self, url, year):
        try:
            print(f"正在访问: {url}")
            self.driver.get(url)
            
            # 穿透 iframe 
            try:
                WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
                self.driver.switch_to.frame(self.driver.find_element(By.TAG_NAME, "iframe"))
            except:
                pass

            WebDriverWait(self.driver, 15).until(EC.presence_of_all_elements_located((By.TAG_NAME, "tr")))
            time.sleep(2) 

            trs = self.driver.find_elements(By.TAG_NAME, "tr")
            if len(trs) < 10: return []

            target_tr = trs[9] # 下标9
            tds = target_tr.find_elements(By.CSS_SELECTOR, "td.xl75")
            
            results = []
            now_time = time.strftime("%Y-%m-%d %H:%M:%S")

            for i in range(0, len(tds), 2):
                month_num = (i // 2) + 1
                if month_num > 12: break
                
                raw_val = tds[i].text.strip()
                
                if raw_val:
                    ounces, tons = self._convert_to_tons(raw_val)
                    print(f"解析: {month_num}月 | 原始: {raw_val} | 转换: {tons} 吨")
                    results.append({
                        'year': year,
                        'month': month_num,
                        'raw_text': raw_val,
                        'ounces': ounces,
                        'tons': tons,
                        'time': now_time
                    })
            return results
        except Exception as e:
            print(f"采集出错: {e}")
            return []

    def save_to_db(self, data):
        if not data: return
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for item in data:
            cursor.execute("""
                INSERT OR REPLACE INTO gold_reserve 
                (year, month, raw_text, ounces_numeric, tons_numeric, current_datetime)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (item['year'], item['month'], item['raw_text'], item['ounces'], item['tons'], item['time']))
        conn.commit()
        conn.close()
        print(f"成功更新数据库，共 {len(data)} 条记录。")

if __name__ == "__main__":
    # 配置信息
    USER_DATA = r'D:\Chrome\yzh\UserData'
    CHROME_EXE = r'C:\Users\Administrator\AppData\Local\Chromium\Application\chrome.exe'
    DRIVER = r'D:\chromedriver.exe'
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-y', '--year', type=int, default=2026)
    parser.add_argument('-u', '--url', type=str, default='https://www.safe.gov.cn/safe/2026/0206/27116.html')
    args = parser.parse_args()

    crawler = GoldReserveCrawler(USER_DATA, CHROME_EXE, DRIVER)
    try:
        data = crawler.get_page_data(args.url, args.year)
        crawler.save_to_db(data)
    finally:
        # crawler.driver.quit()
        pass