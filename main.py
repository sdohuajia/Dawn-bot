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

    def load_accounts(self, mode: str) -> List[Dict[str, str]]:
        if mode == "1":
            return self._get_single_account()
        else:
            return self._load_accounts_from_file()

    def _load_accounts_from_file(self) -> List[Dict[str, str]]:
        accounts = []
        try:
            with open("accounts.txt", "r") as f:
                lines = f.readlines()
                for line in lines:
                    if ":" in line:
                        email, token = line.strip().split(":")
                        accounts.append({"email": email, "token": token})
            if accounts:
                self.log_colored("SUCCESS", f"已从文件加载 {len(accounts)} 个账户", Colors.SUCCESS)
            else:
                self.log_colored("ERROR", "accounts.txt 为空", Colors.ERROR)
        except FileNotFoundError:
            self.log_colored("ERROR", "未找到 accounts.txt 文件", Colors.ERROR)
        return accounts

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

    def load_proxies(self) -> None:
        try:
            with open("proxies.txt", "r") as f:
                self.proxies = [line.strip() for line in f if line.strip()]
            if self.proxies:
                self.log_colored("SUCCESS", f"已加载 {len(self.proxies)} 个代理", Colors.SUCCESS)
            else:
                self.log_colored("WARNING", "proxies.txt 为空", Colors.WARNING)
        except FileNotFoundError:
            self.log_colored("WARNING", "未找到 proxies.txt 文件", Colors.WARNING)

    def get_random_proxy(self) -> Optional[Dict[str, str]]:
        if not self.proxies:
            return None
        proxy = random.choice(self.proxies)
        return {"http": f"http://{proxy}", "https": f"http://{proxy}"}

    async def process_account(self, account: Dict[str, str]) -> int:
        try:
            proxy = self.get_random_proxy()
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "origin": "chrome-extension://fpdkjdnhkakefebpekbdhillbhonfjjp",
                "user-agent": "Mozilla/5.0",
                "authorization": f"Bearer {account['token']}"
            }

            # 保持在线
            response = self.session.post(
                self.API_URLS["keepalive"],
                headers=headers,
                proxies=proxy,
                timeout=30
            )
            if response.status_code == 200:
                self.log_colored("SUCCESS", f"账户 {account['email']} 保持在线成功", Colors.SUCCESS)
            else:
                self.log_colored("ERROR", f"账户 {account['email']} 保持在线失败", Colors.ERROR)

            # 获取积分
            response = self.session.get(
                self.API_URLS["getPoints"],
                headers=headers,
                proxies=proxy,
                timeout=30
            )
            if response.status_code == 200:
                points_data = response.json()
                return points_data
            else:
                self.log_colored("ERROR", f"获取积分失败: {response.status_code}", Colors.ERROR)
                return 0

        except Exception as e:
            self.log_colored("ERROR", f"处理账户时出错: {str(e)}", Colors.ERROR)
            return 0

    def log_colored(self, level: str, message: str, color: str) -> None:
        message = (message.replace("Starting", "开始")
                  .replace("Completed", "完成")
                  .replace("Failed", "失败")
                  .replace("Error", "错误")
                  .replace("Success", "成功")
                  .replace("Loading", "加载中")
                  .replace("Processing", "处理中")
                  .replace("Waiting", "等待")
                  .replace("points", "积分")
                  .replace("accounts", "账户")
                  .replace("proxies", "代理"))
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {color}{level}: {message}{Colors.RESET}")

    @staticmethod
    async def countdown(seconds: int) -> None:
        for remaining in range(seconds, 0, -1):
            print(f"\r等待下一轮: {remaining}秒 ", end="")
            await asyncio.sleep(1)
        print("\r" + " " * 30 + "\r", end="")

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
