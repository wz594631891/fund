import time
import json
import random
import sqlite3
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class GuruFocusCrawler:
    def __init__(self):
        self.options = Options()
        self.options.add_argument('--user-data-dir=D:\\Chrome\\yzh\\UserData')
        # self.options.add_argument('--disable-gpu')
        self.options.add_argument('--no-sandbox')
        chrome_path = r"C:\Users\Administrator\AppData\Local\Chromium\Application\chrome.exe"
        self.options.binary_location = chrome_path
        self.driver = webdriver.Chrome(
            executable_path=r"D:/chromedriver.exe",
            options=self.options
        )
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })
        
        self.db_path = "gurufocus_data.db"
        self._create_database()
    
    def _create_database(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建表（如果不存在）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    value TEXT,
                    page INTEGER,
                    current_datetime TEXT
                )
            """)
            
            # 为已存在的表添加新字段
            new_columns = [
                ('one_std_dev_3y', 'TEXT'),
                ('mean_value_3y', 'TEXT'),
                ('minus_one_std_dev_3y', 'TEXT'),
                ('one_std_dev_5y', 'TEXT'),
                ('mean_value_5y', 'TEXT'),
                ('minus_one_std_dev_5y', 'TEXT'),
                ('one_std_dev_10y', 'TEXT'),
                ('mean_value_10y', 'TEXT'),
                ('minus_one_std_dev_10y', 'TEXT'),
                ('three_year_20pct', 'TEXT'),
                ('three_year_50pct', 'TEXT'),
                ('three_year_80pct', 'TEXT'),
                ('five_year_20pct', 'TEXT'),
                ('five_year_50pct', 'TEXT'),
                ('five_year_80pct', 'TEXT'),
                ('ten_year_20pct', 'TEXT'),
                ('ten_year_50pct', 'TEXT'),
                ('ten_year_80pct', 'TEXT'),
                ('current_percentile_3year', 'TEXT'),
                ('current_percentile_5year', 'TEXT'),
                ('current_percentile_10year', 'TEXT'),
            ]
            
            for column_name, column_type in new_columns:
                try:
                    cursor.execute(f"ALTER TABLE data ADD COLUMN {column_name} {column_type}")
                except Exception as e:
                    # 字段已存在，忽略错误
                    pass
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"数据库初始化错误：{e}")
    
    def save_to_database(self, data, page):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            current_datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            for item in data:
                cursor.execute("""
                    SELECT id FROM data WHERE date = ?
                """, (item['date'],))
                if cursor.fetchone():
                    print(f"日期 {item['date']} 已存在，跳过")
                    continue
                cursor.execute("""
                    INSERT INTO data (date, value, page, current_datetime)
                    VALUES (?, ?, ?, ?)
                """, (item['date'], item['value'], page, current_datetime))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"保存数据到数据库出错: {e}")
            return False
    
    def get_page_data(self):
        try:
            print("正在导入 jQuery...")
            self.driver.execute_script("""
                setTimeout(function() {
                    console.log("开始加载 jQuery 第1次...");
                    var jq1 = document.createElement('script');
                    jq1.src = "https://fastly.jsdelivr.net/gh/jquery/jquery@3.6.4/dist/jquery.min.js";
                    jq1.onload = function() { console.log("jQuery 第1次加载成功"); };
                    jq1.onerror = function() { console.log("jQuery 第1次加载失败"); };
                    document.head.appendChild(jq1);
                }, 1000);
                
                setTimeout(function() {
                    console.log("开始加载 jQuery 第2次...");
                    var jq2 = document.createElement('script');
                    jq2.src = "https://fastly.jsdelivr.net/gh/jquery/jquery@3.6.4/dist/jquery.min.js";
                    jq2.onload = function() { console.log("jQuery 第2次加载成功"); };
                    jq2.onerror = function() { console.log("jQuery 第2次加载失败"); };
                    document.head.appendChild(jq2);
                    console.log("jQuery 第2次加载完成");
                }, 2000);
                
                setTimeout(function() {
                    console.log("开始加载 jQuery 第3次...");
                    var jq3 = document.createElement('script');
                    jq3.src = "https://fastly.jsdelivr.net/gh/jquery/jquery@3.6.4/dist/jquery.min.js";
                    jq3.onload = function() { console.log("jQuery 第3次加载成功"); };
                    jq3.onerror = function() { console.log("jQuery 第3次加载失败"); };
                    document.head.appendChild(jq3);
                    console.log("jQuery 第3次加载完成");
                }, 3000);
            """)
            time.sleep(4)
            print("jQuery 导入完成，开始获取数据...")
            self.close_dialog()
            
            data = self.driver.execute_script("""
                var result = [];
                var tbody = document.querySelectorAll('tbody')[1];
                if (!tbody) return result;
                var rows = tbody.querySelectorAll('tr');
                rows.forEach(function(row) {
                    var tds = row.querySelectorAll('td');
                    if (tds.length >= 2) {
                        var date = tds[0].innerText.trim();
                        var value = tds[1].innerText.trim();
                        if (date && value) {
                            result.push({date: date, value: value});
                        }
                    }
                });
                return result;
            """)
            return data if data else []
        except Exception as e:
            print(f"获取页面数据出错: {e}")
            return []
    
    def close_dialog(self):
        try:
            dialog_closed = self.driver.execute_script("""
                var dialogBtn = document.querySelectorAll('body > div.el-dialog__wrapper.gf > div > div.el-dialog__header > button > i')[0];
                if (dialogBtn) {
                    dialogBtn.click();
                    console.log("已关闭弹窗");
                    return true;
                }
                return false;
            """)
            return dialog_closed
        except Exception:
            return False
    
    def get_current_page(self):
        try:
            active_page = self.driver.find_element(By.CSS_SELECTOR, "li.number.active")
            return int(active_page.text.strip())
        except Exception:
            return 1
    
    def click_page(self, page_num):
        try:
            self.close_dialog()
            page_elements = self.driver.find_elements(By.CSS_SELECTOR, "li.number")
            for page_elem in page_elements:
                if page_elem.text.strip() == str(page_num):
                    page_elem.click()
                    return True
            return False
        except Exception:
            return False
    
    def click_next_page(self, retry_count=0):
        try:
            self.close_dialog()
            next_btn = self.driver.find_element(By.CSS_SELECTOR, "i.el-icon.el-icon-arrow-right")
            if next_btn:
                next_btn.click()
                return True
            return False
        except Exception:
            if retry_count < 3:
                print(f"无法点击下一页 (尝试 {retry_count + 1}/4)，等待2秒后重试...")
                time.sleep(2)
                try:
                    self.close_dialog()
                    next_btn = self.driver.find_element(By.CSS_SELECTOR, "i.el-icon.el-icon-arrow-right")
                    if next_btn:
                        next_btn.click()
                        return True
                except Exception:
                    pass
                return self.click_next_page(retry_count + 1)
            else:
                # 第4次（最后一次）使用 execute_script 执行
                print("无法点击下一页，第4次尝试使用 JavaScript 执行点击...")
                try:
                    self.close_dialog()
                    result = self.driver.execute_script("""
                        var nextBtn = document.querySelector('i.el-icon.el-icon-arrow-right');
                        if (nextBtn) {
                            nextBtn.click();
                            return true;
                        }
                        return false;
                    """)
                    
                    if result:
                        time.sleep(1)
                        # 验证页码是否正确
                        current_page = self.get_current_page()
                        print(f"JavaScript 点击成功，当前页码: {current_page}")
                        return True
                    else:
                        print("JavaScript 执行：无法找到下一页按钮")
                        return False
                except Exception as e:
                    print(f"JavaScript 执行出错: {e}")
                    return False
    
    def has_next_page(self):
        try:
            self.close_dialog()
            next_btn = self.driver.find_element(By.CSS_SELECTOR, "i.el-icon.el-icon-arrow-right")
            parent = next_btn.find_element(By.XPATH, "..")
            if "disabled" in parent.get_attribute("class"):
                return False
            return True
        except Exception:
            return False
    
    def check_verification(self):
        try:
            body_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            verification_keywords = ["verification", "captcha", "validate", "human", "confirm", "安全验证", "验证码", "验证"]
            for keyword in verification_keywords:
                if keyword in body_text:
                    return True
            return False
        except Exception:
            return False
    
    def crawl_all_pages(self, start_url):
        all_data = []
        page = 1
        
        try:
            self.driver.get(start_url)
            if self.check_verification():
                print("检测到页面存在验证，请手动完成验证后按回车键继续...")
                input()
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "tbody"))
            )
            time.sleep(2)
            
            while True:
                print(f"正在爬取第 {page} 页...")
                self.close_dialog()
                page_data = self.get_page_data()
                if page_data:
                    self.save_to_database(page_data, page)
                    print(f"数据已保存到数据库")
                all_data.extend(page_data)
                print(f"第 {page} 页爬取完成，共 {len(page_data)} 条数据")
                
                if not self.has_next_page():
                    print("已到达最后一页")
                    break
                
                next_page_num = page + 1
                if self.click_next_page(0):
                    actual_page = self.get_current_page()
                    print(f"当前实际页码: {actual_page}")
                    if page % 10 == 0:
                        sleep_minutes = getattr(self, 'sleep_minutes', 10)
                        print(f"每10页休眠 {sleep_minutes} 分钟...")
                        time.sleep(sleep_minutes * 60)
                    wait_time = random.randint(5, 20)
                    print(f"等待 {wait_time} 秒后爬取第 {next_page_num} 页...")
                    time.sleep(wait_time)
                    page = actual_page
                else:
                    print("无法点击下一页")
                    break
            
            return all_data
        
        except TimeoutException:
            print("页面加载超时")
        except NoSuchElementException:
            print("找不到元素")
        except Exception as e:
            print(f"爬取数据出错: {e}")
        finally:
            self.driver.quit()
    
    def save_to_json(self, data, filename="gurufocus_data.json"):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"数据已保存到 {filename}")
            return True
        except Exception as e:
            print(f"保存JSON文件出错: {e}")
            return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='GuruFocus 爬虫')
    parser.add_argument('-p', '--page', type=int, help='跳过到指定页码')
    parser.add_argument('-l', '--latest', action='store_true', help='只收集第一页')
    parser.add_argument('-w', '--wait', action='store_true', help='页面打开后暂停等待')
    parser.add_argument('-s', '--sleep', type=int, default=10, help='每N页休眠时间(分钟)，默认10分钟')
    args = parser.parse_args()
    
    crawler = GuruFocusCrawler()
    crawler.sleep_minutes = args.sleep
    
    start_url = "https://www.gurufocus.com/economic_indicators/6778/nasdaq-100-pe-ratio"
    
    print(f"开始爬取: {start_url}")
    # 普通模式先加载页面，这样 -l 或 -p 都能操作已有内容
    if not args.wait:
        crawler.driver.get(start_url)
        if crawler.check_verification():
            print("检测到页面存在验证，请手动完成验证后按回车键继续...")
    
    if args.wait:
        # wait 模式将在加载后暂停，不重复调用 get 影响逻辑
        crawler.driver.get(start_url)
        if crawler.check_verification():
            print("检测到页面存在验证，请手动完成验证后按回车键继续...")
        else:
            print("页面已打开，请手动完成操作后按回车键继续...")
        input()
    
    if args.page and args.page > 1:
        print(f"跳过到第 {args.page} 页...")
        current_page = 1
        while current_page < args.page:
            print(f"正在跳过第 {current_page} 页...")
            crawler.close_dialog()
            if crawler.click_page(args.page):
                print(f"已跳转到第 {args.page} 页")
                break
            else:
                print(f"第 {current_page} 页没有显示目标页码，点击下一页...")
                if not crawler.has_next_page():
                    print("已到达最后一页")
                    break
                crawler.click_next_page(0)
                time.sleep(random.randint(5, 20))
                current_page += 1
    
    if args.latest:
        print("只收集第一页...")
        crawler.close_dialog()
        page_data = crawler.get_page_data()
        if page_data:
            crawler.save_to_database(page_data, 1)
            print(f"数据已保存到数据库")
        all_data = page_data
    else:
        all_data = crawler.crawl_all_pages(start_url)
    
    if all_data:
        print(f"总共爬取 {len(all_data)} 条数据")
    else:
        print("未获取到任何数据")
