import time
import json
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
        
        # 隐藏自动化特征
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        
        self.db_path = "gold_reserve_data.db"
        self._create_database()

    def _create_database(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS gold_reserve (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER,
                month INTEGER,
                gold_ounces TEXT,
                current_datetime TEXT,
                UNIQUE(year, month)
            )
        """)
        conn.close()

    def get_page_data(self, url, year):
        try:
            print(f"正在访问: {url}")
            self.driver.get(url)
            
            # 1. 穿透 iframe 数据层
            try:
                WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
                self.driver.switch_to.frame(self.driver.find_element(By.TAG_NAME, "iframe"))
            except:
                print("未检测到 iframe，直接解析主页面")

            # 2. 等待 tr 加载
            WebDriverWait(self.driver, 15).until(EC.presence_of_all_elements_located((By.TAG_NAME, "tr")))
            time.sleep(2) # 缓冲渲染

            # 3. 按照你指定的逻辑获取：下标为9的tr行
            trs = self.driver.find_elements(By.TAG_NAME, "tr")
            if len(trs) < 10:
                print(f"页面行数不足，当前总行数: {len(trs)}")
                return []

            target_tr = trs[9] # 下标为9的tr
            # 获取该行内所有 class 为 xl75 的 td
            tds = target_tr.find_elements(By.CSS_SELECTOR, "td.xl75")
            
            monthly_results = []
            now_time = time.strftime("%Y-%m-%d %H:%M:%S")

            # 逻辑：下标 N 为双数 (0, 2, 4...)，对应 1, 2, 3... 月
            for i in range(0, len(tds), 2):
                month_num = (i // 2) + 1
                if month_num > 12: break # 超过12月停止
                
                val = tds[i].text.strip()
                
                # 判断内容是否为空，确定数据是否发布
                if val and val != "":
                    print(f"发现数据: {year}年{month_num}月 -> {val}")
                    monthly_results.append({
                        'year': year,
                        'month': month_num,
                        'value': val,
                        'time': now_time
                    })
                else:
                    print(f"{year}年{month_num}月 数据尚未发布，跳过")

            self.driver.switch_to.default_content()
            return monthly_results

        except Exception as e:
            print(f"解析出错: {e}")
            return []

    def save_to_db(self, data):
        if not data: return
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for item in data:
            cursor.execute("""
                INSERT OR REPLACE INTO gold_reserve (year, month, gold_ounces, current_datetime)
                VALUES (?, ?, ?, ?)
            """, (item['year'], item['month'], item['value'], item['time']))
        conn.commit()
        conn.close()
        print(f"成功存入数据库 {len(data)} 条数据")

if __name__ == "__main__":
    # 配置
    USER_DATA = r'D:\Chrome\yzh\UserData'
    CHROME_EXE = r'C:\Users\Administrator\AppData\Local\Chromium\Application\chrome.exe'
    DRIVER = r'D:\chromedriver.exe'
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-y', '--year', type=int, default=2026)
    parser.add_argument('-u', '--url', type=str, default='https://www.safe.gov.cn/safe/2026/0206/27116.html')
    args = parser.parse_args()

    crawler = GoldReserveCrawler(USER_DATA, CHROME_EXE, DRIVER)
    data = crawler.get_page_data(args.url, args.year)
    crawler.save_to_db(data)