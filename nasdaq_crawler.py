import time
import smtplib
import pymysql
import datetime
import argparse
from email.mime.text import MIMEText
from email.header import Header
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class NasdaqCrawler:
    def __init__(self):
        # 数据库配置
        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'root',
            'charset': 'utf8mb4'
        }
        
        # 邮件配置
        self.mail_config = {
            'sender': '2460307574@qq.com',
            'smtp_server': 'smtp.qq.com',
            'smtp_port': 465,
            'smtp_ssl': True,
            'password': 'apmgpztdtxjaeaea',  # QQ邮箱授权码
            'receivers': ['2460307574@qq.com']
        }
        
        # 初始化浏览器
        self.options = Options()
        self.options.add_argument('--user-data-dir=D:\\Chrome\\yzh\\UserData')
        self.options.add_argument('--headless')  # 无头模式，可注释掉以便查看浏览器操作
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--no-sandbox')
        chrome_path = r"C:\Users\Administrator\AppData\Local\Google\Chrome\Application\chrome.exe"
        self.options.binary_location = chrome_path
        self.driver = webdriver.Chrome(
            executable_path=r"D:\Chrome\yzh\chromedriver.exe",
            options=self.options
        )
        # 绕过网站的WebDriver检测
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })
        
        # 创建数据库和表
        self._create_database_and_table()
    
    def _create_database_and_table(self):
        """创建数据库和数据表"""
        try:
            # 连接数据库
            conn = pymysql.connect(**self.db_config)
            cursor = conn.cursor()
            
            # 创建数据库（如果不存在）
            cursor.execute("CREATE DATABASE IF NOT EXISTS fnd CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            conn.select_db("fnd")
            
            # 创建数据表（如果不存在），只对date添加唯一索引
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nasdaq (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    pe DECIMAL(10, 2) DEFAULT NULL,
                    pe_percentile DECIMAL(10, 2) DEFAULT NULL,
                    evaluate VARCHAR(255) DEFAULT NULL,
                    roe DECIMAL(10, 2) DEFAULT NULL,
                    peg DECIMAL(10, 2) DEFAULT NULL,
                    date DATE DEFAULT NULL,
                    time TIME DEFAULT NULL,
                    UNIQUE KEY unique_date (date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            conn.commit()
        except Exception as e:
            print(f"数据库初始化错误: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def crawl_data(self):
        """爬取纳斯达克指数数据"""
        try:
            # 打开网页
            self.driver.get("https://danjuanfunds.com/dj-valuation-table-detail/NDX")
            # 等待页面加载
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".value-text"))
            )
            time.sleep(3)  # 额外等待页面渲染
            
            # 获取数据
            pe = self._get_element_text(".value-text", 1)
            pe_percentile = self._get_element_text(".value-text", 2)
            evaluate = self._get_element_text(".middle-name", 0)
            # roe = self._get_element_text("", 0)  # 暂时不需要
            peg = self._get_element_text(".bot-pencent", 4)
            date = self._get_element_text(".import", 1)
            # 数据处理
            pe = float(pe) if pe else None
            pe_percentile = float(pe_percentile.replace("%", "")) if pe_percentile else None
            evaluate = evaluate.strip() if evaluate else None
            peg = float(peg.replace("%", "")) if peg else None

            # 处理页面日期为 MM-DD，拼接本地年份
            if date:
                try:
                    # 页面日期如 06-28，拼接本地年份
                    if len(date) == 5 and '-' in date:
                        year = datetime.date.today().year
                        date_str = f"{year}-{date}"
                        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                    else:
                        # 兼容 YYYY-MM-DD 或 YYYY/MM/DD
                        date_obj = datetime.datetime.strptime(date.replace('/', '-'), "%Y-%m-%d").date()
                except Exception:
                    print(f"页面日期格式异常，未存入数据：{date}")
                    return
            else:
                print("未获取到页面日期，未存入数据")
                return
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 保存数据到数据库
            is_new_data = self._save_to_database(pe, pe_percentile, evaluate, None, peg, date_obj, current_time)
            
            # 根据PE百分位发送邮件（仅当数据是新数据时）
            if is_new_data and pe_percentile is not None:
                if pe_percentile > 80:
                    self._send_email("纳斯达克PE百分位过高", 
                                     f"当前纳斯达克PE百分位为{pe_percentile}%，超过80%，请注意市场风险！")
                elif pe_percentile < 50:
                    self._send_email("纳斯达克PE百分位过低", 
                                     f"当前纳斯达克PE百分位为{pe_percentile}%，低于50%，市场可能被低估。")
            
            return {
                'pe': pe,
                'pe_percentile': pe_percentile,
                'evaluate': evaluate,
                'peg': peg,
                'date': str(date_obj),  # 修正这里
                'time': str(current_time),
                'is_new_data': is_new_data
            }
            
        except TimeoutException:
            print("页面加载超时")
        except NoSuchElementException:
            print("找不到元素")
        except Exception as e:
            print(f"爬取数据出错: {e}")
        finally:
            # 关闭浏览器
            self.driver.quit()
    
    def _get_element_text(self, selector, index):
        """获取指定选择器的第index个元素的文本"""
        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
        if 0 <= index < len(elements):
            return elements[index].text.strip()
        return None
    
    def _save_to_database(self, pe, pe_percentile, evaluate, roe, peg, date, time):
        """保存数据到MySQL数据库，返回是否为新数据"""
        try:
            conn = pymysql.connect(**self.db_config, database="fnd")
            cursor = conn.cursor()
            
            # 先检查是否已存在相同date
            select_sql = "SELECT id FROM nasdaq WHERE date = %s"
            cursor.execute(select_sql, (date,))
            if cursor.fetchone():
                print("该日期数据已存在，未插入")
                return False

            # 插入数据
            sql = """
                INSERT INTO nasdaq (pe, pe_percentile, evaluate, roe, peg, date, time)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (pe, pe_percentile, evaluate, roe, peg, date, time))
            conn.commit()
            print("数据已成功保存到数据库")
            return True
                
        except Exception as e:
            print(f"保存数据到数据库出错: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    
    def _send_email(self, subject, content):
        """发送邮件"""
        try:
            message = MIMEText(content, 'plain', 'utf-8')
            message['From'] = Header(self.mail_config['sender'], 'utf-8')
            message['To'] = Header(", ".join(self.mail_config['receivers']), 'utf-8')
            message['Subject'] = Header(subject, 'utf-8')
            
            if self.mail_config['smtp_ssl']:
                smtp_obj = smtplib.SMTP_SSL(self.mail_config['smtp_server'], self.mail_config['smtp_port'])
            else:
                smtp_obj = smtplib.SMTP(self.mail_config['smtp_server'], self.mail_config['smtp_port'])
            
            smtp_obj.login(self.mail_config['sender'], self.mail_config['password'])
            smtp_obj.sendmail(
                self.mail_config['sender'], 
                self.mail_config['receivers'], 
                message.as_string()
            )
            smtp_obj.quit()
            print(f"邮件发送成功: {subject}")
            return True
        except Exception as e:
            print(f"邮件发送失败: {e}")
            return False

    def test_email(self):
        """测试邮件发送功能"""
        print("开始测试邮件发送功能...")
        result = self._send_email(
            "【测试】纳斯达克爬虫邮件功能", 
            "这是一封测试邮件，用于验证纳斯达克爬虫的邮件发送功能是否正常工作。\n\n"
            "如果您收到此邮件，说明配置正确。\n\n"
            "该邮件由程序自动发送，请勿回复。"
        )
        if result:
            print("邮件测试成功！")
        else:
            print("邮件测试失败，请检查配置。")
        return result

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='纳斯达克指数数据爬虫')
    parser.add_argument('--test', action='store_true', help='测试邮件发送功能')
    args = parser.parse_args()
    
    crawler = NasdaqCrawler()
    
    if args.test:
        # 测试邮件功能
        crawler.test_email()
    else:
        # 正常爬取数据
        data = crawler.crawl_data()
        if data:
            print("爬取结果:")
            for key, value in data.items():
                print(f"{key}: {value}")