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
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS gold_reserve (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER,
                month INTEGER,
                raw_text TEXT,
                ounces_numeric REAL,
                tons_numeric REAL,
                tons_diff REAL,         -- 增加/减少吨数，若无上月数据则为 NULL
                current_datetime TEXT,
                UNIQUE(year, month)
            )
        """)
        conn.close()

    def _get_previous_month_tons(self, year, month):
        """查找上个月的吨数数值"""
        if month == 1:
            prev_year, prev_month = year - 1, 12
        else:
            prev_year, prev_month = year, month - 1
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT tons_numeric FROM gold_reserve WHERE year = ? AND month = ?", (prev_year, prev_month))
        result = cursor.fetchone()
        conn.close()
        # 如果没有找到记录，直接返回 None (即 NULL)
        return result[0] if result else None

    def _convert_to_tons(self, text):
        try:
            match = re.search(r'([\d,.]+)', text)
            if match:
                clean_num = float(match.group(1).replace(',', ''))
                # 转换系数：1万金衡盎司 = 0.311034768 吨
                tons = clean_num * 0.311034768
                return clean_num, round(tons, 2)
            return None, None
        except Exception as e:
            print(f"转换失败: {e}")
            return None, None

    def get_page_data(self, url, year):
        try:
            print(f"正在访问: {url}")
            self.driver.get(url)
            
            try:
                WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
                self.driver.switch_to.frame(self.driver.find_element(By.TAG_NAME, "iframe"))
            except:
                pass

            WebDriverWait(self.driver, 15).until(EC.presence_of_all_elements_located((By.TAG_NAME, "tr")))
            time.sleep(2) 

            trs = self.driver.find_elements(By.TAG_NAME, "tr")
            if len(trs) < 10: return []

            # 定位到你指定的 tr 下标 9
            target_tr = trs[9]
            tds = target_tr.find_elements(By.CSS_SELECTOR, "td.xl75")
            
            results = []
            now_time = time.strftime("%Y-%m-%d %H:%M:%S")

            for i in range(0, len(tds), 2):
                month_num = (i // 2) + 1
                if month_num > 12: break
                
                raw_val = tds[i].text.strip()
                if raw_val:
                    ounces, tons = self._convert_to_tons(raw_val)
                    
                    # 核心逻辑：获取上月吨数
                    prev_tons = self._get_previous_month_tons(year, month_num)
                    
                    # 如果有上月数据则计算差值，否则设为 None (NULL)
                    diff = round(tons - prev_tons, 2) if prev_tons is not None else None
                    
                    diff_display = f"{diff:+}吨" if diff is not None else "NULL (无基准数据)"
                    print(f"解析: {month_num}月 | 吨数: {tons} | 增减: {diff_display}")
                    
                    results.append({
                        'year': year,
                        'month': month_num,
                        'raw_text': raw_val,
                        'ounces': ounces,
                        'tons': tons,
                        'diff': diff,
                        'time': now_time
                    })
            return results
        except Exception as e:
            print(f"运行出错: {e}")
            return []

    def save_to_db(self, data):
        if not data: return
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for item in data:
            cursor.execute("""
                INSERT OR REPLACE INTO gold_reserve 
                (year, month, raw_text, ounces_numeric, tons_numeric, tons_diff, current_datetime)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (item['year'], item['month'], item['raw_text'], item['ounces'], item['tons'], item['diff'], item['time']))
        conn.commit()
        conn.close()
        print("数据库入库操作完成。")

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
    try:
        data = crawler.get_page_data(args.url, args.year)
        crawler.save_to_db(data)
    finally:
        pass