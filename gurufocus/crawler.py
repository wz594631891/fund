import time
import json
import random
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
            
            data = self.driver.execute_script("""
                var result = [];
                var rows = $("tbody").eq(1).find("tr");
                rows.each(function() {
                    var date = $(this).find("td").eq(0).text().trim();
                    var value = $(this).find("td").eq(1).text().trim();
                    if (date && value) {
                        result.push({date: date, value: value});
                    }
                });
                return result;
            """)
            return data if data else []
        except Exception as e:
            print(f"获取页面数据出错: {e}")
            return []
    
    def get_current_page(self):
        try:
            active_page = self.driver.find_element(By.CSS_SELECTOR, "li.number.active")
            return int(active_page.text.strip())
        except Exception:
            return 1
    
    def click_next_page(self):
        try:
            next_btn = self.driver.find_element(By.CSS_SELECTOR, "i.el-icon.el-icon-arrow-right")
            if next_btn:
                next_btn.click()
                return True
            return False
        except Exception:
            return False
    
    def has_next_page(self):
        try:
            next_btn = self.driver.find_element(By.CSS_SELECTOR, "i.el-icon.el-icon-arrow-right")
            parent = next_btn.find_element(By.XPATH, "..")
            if "disabled" in parent.get_attribute("class"):
                return False
            return True
        except Exception:
            return False
    
    def crawl_all_pages(self, start_url):
        all_data = []
        page = 1
        
        try:
            self.driver.get(start_url)
            print("如果页面存在验证，请手动完成验证后按回车键继续...")
            input()
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "tbody"))
            )
            time.sleep(2)
            
            while True:
                print(f"正在爬取第 {page} 页...")
                page_data = self.get_page_data()
                all_data.extend(page_data)
                print(f"第 {page} 页爬取完成，共 {len(page_data)} 条数据")
                
                if not self.has_next_page():
                    print("已到达最后一页")
                    break
                
                next_page_num = page + 1
                if self.click_next_page():
                    wait_time = random.randint(5, 20)
                    print(f"等待 {wait_time} 秒后爬取第 {next_page_num} 页...")
                    time.sleep(wait_time)
                    page = next_page_num
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
    crawler = GuruFocusCrawler()
    
    start_url = "https://www.gurufocus.com/economic_indicators/6778/nasdaq-100-pe-ratio"
    
    print(f"开始爬取: {start_url}")
    data = crawler.crawl_all_pages(start_url)
    
    if data:
        filename = f"gurufocus_data_{int(time.time())}.json"
        crawler.save_to_json(data, filename)
        print(f"总共爬取 {len(data)} 条数据")
    else:
        print("未获取到任何数据")
