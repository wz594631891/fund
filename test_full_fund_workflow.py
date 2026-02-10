import subprocess
import sys
import os

def run_command(command):
    """运行命令并返回结果"""
    print(f"运行命令: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    print(f"退出码: {result.returncode}")
    if result.stdout:
        print(f"标准输出:\n{result.stdout}")
    if result.stderr:
        print(f"错误输出:\n{result.stderr}")
    print("-" * 50)
    return result

def main():
    """测试完整的基金数据获取流程"""
    print("=== 基金数据获取脚本完整测试 ===\n")
    
    # 1. 测试API接口
    print("1. 测试基金API接口...")
    result = run_command("python test_fund_api.py")
    
    # 2. 运行主脚本获取数据
    print("2. 运行主脚本获取基金数据...")
    result = run_command("python get_fund_data.py")
    
    # 3. 检查数据库中的数据
    print("3. 检查数据库中的基金数据...")
    result = run_command("python check_fund_db.py")
    
    print("=== 测试完成 ===")

if __name__ == "__main__":
    main()