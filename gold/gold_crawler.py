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
        
        # 初始化浏览器
        self.driver = webdriver.Chrome(
            executable_path=driver_path,
            options=self.options
        )
        
        # 隐藏 WebDriver 特征防止被屏蔽
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        
        self.db_path = "gold_reserve_data.db"
        self._create_database()

    def _create_database(self):
        """初始化数据库结构"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS gold_reserve (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER,
                month INTEGER,
                raw_text TEXT,
                ounces_numeric REAL,
                tons_numeric REAL,
                tons_diff REAL,
                current_datetime TEXT,
                UNIQUE(year, month)
            )
        """)
        conn.close()

    def _get_previous_month_tons(self, year, month):
        """从数据库查询上个月的吨数数值"""
        if month == 1:
            prev_year, prev_month = year - 1, 12
        else:
            prev_year, prev_month = year, month - 1
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT tons_numeric FROM gold_reserve WHERE year = ? AND month = ?", (prev_year, prev_month))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def _convert_to_tons(self, text):
        """精确换算：1万金衡盎司 = 0.311034768 吨"""
        try:
            match = re.search(r'([\d,.]+)', text)
            if match:
                clean_num = float(match.group(1).replace(',', ''))
                tons = clean_num * 0.311034768
                return clean_num, round(tons, 2)
            return None, None
        except Exception as e:
            print(f"转换失败: {e}")
            return None, None

    def get_page_data(self, url, year):
        """解析外汇局页面数据"""
        try:
            print(f"正在访问: {url}")
            self.driver.get(url)
            
            # 处理可能的 iframe
            try:
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
                self.driver.switch_to.frame(self.driver.find_element(By.TAG_NAME, "iframe"))
            except:
                pass

            WebDriverWait(self.driver, 15).until(EC.presence_of_all_elements_located((By.TAG_NAME, "tr")))
            time.sleep(2) 

            trs = self.driver.find_elements(By.TAG_NAME, "tr")
            if len(trs) < 10: 
                print("未找到目标行，请检查页面结构。")
                return []

            # 根据你的需求，定位 tr 下标 9
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
                    print(f"找到数据: {year}年{month_num}月 -> {raw_val} ({tons}吨)")
                    
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
            print(f"运行出错: {e}")
            return []

    def save_to_db(self, data):
        """保存数据并计算增减幅度"""
        if not data: return
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 第一步：入库/更新基础数据（先让数据库里有本月的吨数）
        print("正在写入基础数据...")
        for item in data:
            cursor.execute("""
                INSERT OR REPLACE INTO gold_reserve 
                (year, month, raw_text, ounces_numeric, tons_numeric, current_datetime)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (item['year'], item['month'], item['raw_text'], item['ounces'], item['tons'], item['time']))
        conn.commit()

        # 第二步：回溯计算增减值
        print("正在校准月度增减幅度 (tons_diff)...")
        for item in data:
            prev_tons = self._get_previous_month_tons(item['year'], item['month'])
            if prev_tons is not None:
                diff = round(item['tons'] - prev_tons, 2)
                cursor.execute("""
                    UPDATE gold_reserve SET tons_diff = ? 
                    WHERE year = ? AND month = ?
                """, (diff, item['year'], item['month']))
                print(f" - {item['year']}年{item['month']}月 增减值已更新: {diff:+} 吨")
            else:
                print(f" - {item['year']}年{item['month']}月 无法找到上月数据，保持 NULL")
        
        conn.commit()
        conn.close()
        print("数据库同步完成。")

if __name__ == "__main__":
    # 请确认以下路径正确
    USER_DATA = r'D:\Chrome\yzh\UserData'
    CHROME_EXE = r'C:\Users\Administrator\AppData\Local\Chromium\Application\chrome.exe'
    DRIVER = r'D:\chromedriver.exe'
    
    parser = argparse.ArgumentParser(description='外汇局黄金储备爬虫')
    parser.add_argument('-y', '--year', type=int, default=2025)
    parser.add_argument('-u', '--url', type=str, default='https://www.safe.gov.cn/safe/2025/0206/27115.html')
    args = parser.parse_args()

    crawler = GoldReserveCrawler(USER_DATA, CHROME_EXE, DRIVER)
    try:
        scraped_data = crawler.get_page_data(args.url, args.year)
        crawler.save_to_db(scraped_data)
    finally:
        # 如需保持浏览器开启可注释掉下行
        # crawler.driver.quit()
        pass