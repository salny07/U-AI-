import random
import time
import sys
import os
import subprocess
import json
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime

# ================= 配置 =================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILE_DIR = os.path.join(SCRIPT_DIR, "chrome_profile")
DRIVER_CONFIG = os.path.join(SCRIPT_DIR, "driver_config.json")
URL="https://ucloud.unipus.cn/home?ticket=ST-164860-IndVyQ2XAJz2AhJrn1Ql-sso-api-8"
CHECK_INTERVAL=3

# 挂机计时器打印间隔（分钟）
PRINT_INTERVAL_MINUTES = 5
# =========================================

def kill_chrome():
    try:
        subprocess.run("taskkill /F /IM chrome.exe", shell=True, capture_output=True, check=False)
        print("已关闭所有 Chrome 进程")
        time.sleep(1)
    except:
        pass

def get_driver():
    """下载驱动并保存到脚本目录，带重试机制"""
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        print(f"正在下载 ChromeDriver (尝试 {attempt}/{max_retries})...")
        try:
            downloaded_path = ChromeDriverManager().install()
            target_path = os.path.join(SCRIPT_DIR, os.path.basename(downloaded_path))
            if not os.path.exists(target_path) or not os.path.samefile(downloaded_path, target_path):
                shutil.copy2(downloaded_path, target_path)
            with open(DRIVER_CONFIG, 'w') as f:
                json.dump({"path": target_path}, f)
            print(f"驱动下载成功，已保存至: {target_path}")
            print("请重新运行本脚本。（关掉梯子）")
            sys.exit(0)
        except Exception as e:
            print(f"下载失败: {e}")
            if attempt < max_retries:
                print("等待 3 秒后重试...")
                time.sleep(3)
            else:
                print("\n多次下载失败，请检查网络连接后重试。（更换梯子，建议美国）")
                print("或手动搜索下载对应版本的 ChromeDriver 并存放到本脚本所在目录，")
                print("然后在该目录下创建 driver_config.json 文件，内容为：")
                print('{"path": "chromedriver.exe"}')
                print("（如果文件名不是 chromedriver.exe，请相应修改）")
                sys.exit(1)

def copy_profile(username):
    """复制 Chrome Profile 到脚本目录"""
    source = rf"C:\Users\{username}\AppData\Local\Google\Chrome\User Data\Default"
    if not os.path.exists(source):
        print(f"找不到源 Profile 路径: {source}")
        return False
    if os.path.exists(PROFILE_DIR):
        print("Profile 已存在，跳过复制。")
        return True
    print("正在复制 Chrome Profile（请稍候）...")
    try:
        shutil.copytree(source, PROFILE_DIR, ignore=shutil.ignore_patterns('SingletonLock', 'SingletonSocket', 'SingletonCookie', 'Lockfile'))
        print("Profile 复制成功。")
        return True
    except Exception as e:
        print(f"复制失败: {e}")
        return False

def start_browser(driver_path):
    """启动浏览器"""
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=0")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument(f"--user-data-dir={PROFILE_DIR}")

    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def handle_popup(driver):
    """检测弹窗并点击确定按钮"""
    try:
        # 定位“确定”按钮，使用文本匹配更可靠
        confirm_button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='确定']"))
        )
        confirm_button.click()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] 检测到弹窗，已点击确定按钮")
        time.sleep(1)  # 等待弹窗消失
        return True
    except:
        return False
def main():
    #if sys.platform == "win32":
    #    kill_chrome()

    # 1. 检查 Profile
    if not os.path.exists(PROFILE_DIR):
        print("未找到本地 Profile，需要复制 Chrome 用户数据。")
        username = input("请输入 Windows 用户名（例如‘C:/Users/Administrator/AppData’中的Administrator即为用户名）： ").strip()
        if not username:
            print("用户名不能为空。")
            sys.exit(1)
        if not copy_profile(username):
            print("无法复制 Profile，请检查路径或手动复制。")
            sys.exit(1)
    else:
        print("Profile 已存在，跳过复制。")

    # 2. 检查驱动
    driver_path = None
    if os.path.exists(DRIVER_CONFIG):
        try:
            with open(DRIVER_CONFIG) as f:
                config = json.load(f)
                path = config.get("path")
                if path and os.path.exists(path):
                    driver_path = path
        except:
            pass

    if not driver_path:
        print("未找到 ChromeDriver，将自动下载。")
        get_driver()

    # 3. 启动浏览器
    print(f"使用驱动: {driver_path}")
    try:
        driver = start_browser(driver_path)
    except Exception as e:
        print(f"浏览器启动失败: {e}")
        sys.exit(1)

    try:
        driver.get(URL)
        print("请手动登录，并转到需要挂机的页面，然后输入 ok 继续...")
        if input().strip().lower() != "ok":
            return


        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] 开始挂机")
        start_time = time.time()
        last_print_minutes = 0
        while True:
                # 检测并关闭弹窗
            handle_popup(driver)

            # 等待固定间隔
            time.sleep(CHECK_INTERVAL)
            # 计时器：每隔 PRINT_INTERVAL_MINUTES 分钟打印一次
            elapsed_minutes = (time.time() - start_time) / 60
            current_minutes = int(elapsed_minutes // PRINT_INTERVAL_MINUTES)
            if current_minutes > last_print_minutes:
                last_print_minutes = current_minutes
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{current_time}] 已挂机 {int(elapsed_minutes)} 分钟")

    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"错误: {e}")
    finally:
        driver.quit()
        print("浏览器已关闭")

if __name__ == "__main__":
    main()