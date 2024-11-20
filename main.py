import asyncio
import logging
import ssl
import warnings
import random
from datetime import datetime
from typing import Dict, List, Optional, Set

import requests
from colorama import Fore, Style, init
from requests.packages.urllib3.exceptions import InsecureRequestWarning

init(autoreset=True)
warnings.simplefilter('ignore', InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',
    level=logging.INFO
)

class Colors:
    SUCCESS = f"{Fore.GREEN}"
    ERROR = f"{Fore.RED}"
    INFO = f"{Fore.CYAN}"
    WARNING = f"{Fore.YELLOW}"
    RESET = f"{Style.RESET_ALL}"

class DawnValidatorBot:
    API_URLS = {
        "keepalive": "https://www.aeropres.in/chromeapi/dawn/v1/userreward/keepalive",
        "getPoints": "https://www.aeropres.in/api/atom/v1/userreferral/getpoint",
        "socialmedia": "https://www.aeropres.in/chromeapi/dawn/v1/profile/update"
    }

    EXTENSION_ID = "fpdkjdnhkakefebpekbdhillbhonfjjp"
    VERSION = "1.0.9"

    def __init__(self):
        self.verified_accounts: Set[str] = set()
        self.session = requests.Session()
        self.session.verify = False
        self.proxies: List[str] = []

    @staticmethod
    def display_welcome() -> None:
        print(f"""
{Colors.INFO}{Style.BRIGHT}╔══════════════════════════════════════════════╗
║            Dawn Validator                    ║
║     Github: https://github.com/sdohuajia     ║
║      X:@ferdie_jhovie                       ║
╚══════════════════════════════════════════════╝{Colors.RESET}
""")

    # ... [之前的其他方法保持不变] ...

    @staticmethod
    def _get_single_account() -> List[Dict[str, str]]:
        print(f"{Colors.INFO}请输入账户详情{Colors.RESET}")
        
        while True:
            email = input(f"{Colors.INFO}输入邮箱: {Colors.RESET}").strip()
            if not email:
                print(f"{Colors.ERROR}错误: 邮箱不能为空{Colors.RESET}")
                continue
            
            token = input(f"{Colors.INFO}输入令牌: {Colors.RESET}").strip()
            if not token:
                print(f"{Colors.ERROR}错误: 令牌不能为空{Colors.RESET}")
                continue
                
            print(f"{Colors.SUCCESS}成功: 已接收账户详情{Colors.RESET}")
            return [{'email': email, 'token': token}]

    def log_colored(self, level: str, message: str, color: str) -> None:
        message = message.replace("Starting", "开始")
                 .replace("Completed", "完成")
                 .replace("Failed", "失败")
                 .replace("Error", "错误")
                 .replace("Success", "成功")
                 .replace("Loading", "加载中")
                 .replace("Processing", "处理中")
                 .replace("Waiting", "等待")
                 .replace("points", "积分")
                 .replace("accounts", "账户")
                 .replace("proxies", "代理")
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {color}{level}: {message}{Colors.RESET}")

async def main():
    bot = DawnValidatorBot()
    bot.display_welcome()
    
    print(f"{Colors.INFO}选择模式:{Colors.RESET}")
    print("1. 单个账户")
    print("2. 多个账户 [从 accounts.txt 读取]")
    
    while True:
        mode = input(f"{Colors.WARNING}请选择 (1/2): {Colors.RESET}")
        if mode in ['1', '2']:
            break
        print(f"{Colors.ERROR}错误: 无效选择。请输入 1 或 2{Colors.RESET}")
    
    accounts = bot.load_accounts(mode)
    if not accounts:
        bot.log_colored("ERROR", "没有可用账户。退出中...", Colors.ERROR)
        return

    bot.load_proxies()

    try:
        while True:
            bot.log_colored("INFO", "开始新进程", Colors.INFO)
            
            account_tasks = []
            for account in accounts:
                account_tasks.append(bot.process_account(account))

            points_array = await asyncio.gather(*account_tasks)
            
            for i, points in enumerate(points_array):
                if isinstance(points, dict):
                    total_points = points.get('total', 0)
                else:
                    total_points = points
                    
                bot.log_colored("INFO", f"账户 {accounts[i]['email']} 累计: {total_points} 积分", Colors.WARNING)
            
            bot.log_colored("INFO", "进程完成", Colors.SUCCESS)
            bot.log_colored("INFO", f"处理账户总数: {len(accounts)}", Colors.INFO)
            
            await bot.countdown(250)

    except KeyboardInterrupt:
        bot.log_colored("WARNING", "用户中断进程。退出中...", Colors.WARNING)
    except Exception as e:
        bot.log_colored("ERROR", f"发生致命错误: {str(e)}", Colors.ERROR)

if __name__ == "__main__":
    asyncio.run(main())
