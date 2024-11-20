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

    def get_base_headers(self, token: str) -> Dict[str, str]:
        return {
            "Accept": "*/*",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Origin": f"chrome-extension://{self.EXTENSION_ID}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        }

    @staticmethod
    def log_colored(level: str, message: str, color: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {color}{level}: {message}{Colors.RESET}")

    def get_random_proxy(self) -> Optional[str]:
        return random.choice(self.proxies) if self.proxies else None

    async def fetch_points(self, headers: Dict[str, str]) -> int:
        try:
            response = self.session.get(
                f"{self.API_URLS['getPoints']}?appid=undefined",
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get('status'):
                raise ValueError(data.get('message', 'Unknown error'))

            points_data = data.get('data', {})
            reward = points_data.get('rewardPoint', {})
            referral = points_data.get('referralPoint', {})
            
            total = sum([
                reward.get('points', 0),
                reward.get('registerpoints', 0),
                reward.get('signinpoints', 0),
                reward.get('twitter_x_id_points', 0),
                reward.get('discordid_points', 0),
                reward.get('telegramid_points', 0),
                reward.get('bonus_points', 0),
                referral.get('commission', 0)
            ])
            return total

        except Exception as e:
            self.log_colored("ERROR", f"Failed to fetch points: {str(e)}", Colors.ERROR)
            return 0

    async def keep_alive_request(self, headers: Dict[str, str], email: str) -> bool:
        payload = {
            "username": email,
            "extensionid": self.EXTENSION_ID,
            "numberoftabs": 0,
            "_v": self.VERSION
        }
        
        try:
            response = self.session.post(
                f"{self.API_URLS['keepalive']}?appid=undefined",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return True
        except Exception as e:
            self.log_colored("ERROR", f"Keep-alive failed for {email}: {str(e)}", Colors.ERROR)
            return False

    async def verify_social_media(self, account: Dict[str, str], proxy: Optional[str] = None) -> None:
        email = account['email']
        
        if email in self.verified_accounts:
            return
            
        headers = self.get_base_headers(account['token'])
        if proxy:
            headers['Proxy'] = proxy

        social_types = ["twitter_x_id", "discordid", "telegramid"]
        
        self.log_colored("INFO", f"Starting social media verification for {email}", Colors.INFO)
        
        for social_type in social_types:
            try:
                response = self.session.post(
                    f"{self.API_URLS['socialmedia']}?appid=undefined",
                    json={social_type: social_type},
                    headers=headers,
                    timeout=60
                )
                response.raise_for_status()
                
                result = response.json()
                if result.get('success'):
                    self.log_colored("SUCCESS", f"Verified {social_type} for {email}", Colors.SUCCESS)
                else:
                    self.log_colored("ERROR", f"Failed to verify {social_type} for {email}: {result.get('message')}", Colors.ERROR)
                
            except Exception as e:
                self.log_colored("ERROR", f"Error verifying {social_type} for {email}: {str(e)}", Colors.ERROR)
            
            await asyncio.sleep(90)
        
        self.log_colored("INFO", f"Completed social media verification for {email}", Colors.INFO)
        self.verified_accounts.add(email)

    @staticmethod
    def load_accounts(mode: str) -> List[Dict[str, str]]:
        if mode == "1":
            return DawnValidatorBot._get_single_account()
        return DawnValidatorBot._load_accounts_from_file()

    @staticmethod
    def _get_single_account() -> List[Dict[str, str]]:
        print(f"{Colors.INFO}Please enter account details{Colors.RESET}")
        
        while True:
            email = input(f"{Colors.INFO}Enter email: {Colors.RESET}").strip()
            if not email:
                print(f"{Colors.ERROR}ERROR: Email cannot be empty{Colors.RESET}")
                continue
            
            token = input(f"{Colors.INFO}Enter token: {Colors.RESET}").strip()
            if not token:
                print(f"{Colors.ERROR}ERROR: Token cannot be empty{Colors.RESET}")
                continue
                
            print(f"{Colors.SUCCESS}SUCCESS: Account details received{Colors.RESET}")
            return [{'email': email, 'token': token}]

    @staticmethod
    def _load_accounts_from_file() -> List[Dict[str, str]]:
        try:
            accounts = []
            with open('accounts.txt', 'r') as f:
                for line in f:
                    if ':' not in line:
                        continue
                
                    email, token = line.strip().split(':')
                    if email and token:
                        accounts.append({
                            'email': email.strip(),
                            'token': token.strip()
                        })
        
            if not accounts:
                raise ValueError("No valid accounts found in accounts.txt")
        
            DawnValidatorBot.log_colored("SUCCESS", f"Loaded {len(accounts)} accounts from accounts.txt", Colors.SUCCESS)
            return accounts
        
        except FileNotFoundError:
            DawnValidatorBot.log_colored("WARNING", "accounts.txt not found", Colors.WARNING)
            return []
        except Exception as e:
            DawnValidatorBot.log_colored("ERROR", f"Error loading accounts from accounts.txt: {str(e)}", Colors.ERROR)
            return []

    def load_proxies(self) -> None:
        try:
            with open('proxies.txt', 'r') as f:
                self.proxies = [line.strip() for line in f if line.strip()]
                
            if self.proxies:
                self.log_colored("SUCCESS", f"Loaded {len(self.proxies)} proxies", Colors.SUCCESS)
            else:
                self.log_colored("WARNING", "No proxies found in proxies.txt", Colors.WARNING)
                
        except FileNotFoundError:
            self.log_colored("WARNING", "proxies.txt not found. Running without proxies.", Colors.WARNING)

    @staticmethod
    def display_welcome() -> None:
        print(f"""
{Colors.INFO}{Style.BRIGHT}╔══════════════════════════════════════════════╗
║               Dawn Validator                 ║
║     Github: https://github.com/sdohuajia     ║
║               X:@ferdie_jhovie               ║
╚══════════════════════════════════════════════╝{Colors.RESET}
""")

    async def process_account(self, account: Dict[str, str]) -> int:
        
        email = account['email']
        proxy = self.get_random_proxy() 
        headers = self.get_base_headers(account['token'])
        
        if proxy:
            headers['Proxy'] = proxy

        self.log_colored("INFO", f"Processing account: {email}", Colors.INFO)
        self.log_colored("INFO", f"Using proxy: {proxy or 'No Proxy'}", Colors.INFO)

        points = await self.fetch_points(headers)
        self.log_colored("INFO", f"Current points: {points}", Colors.WARNING)

        await self.verify_social_media(account, proxy)
        await self.keep_alive_request(headers, email)

        return points

    @staticmethod
    async def countdown(seconds: int) -> None:
        for remaining in range(seconds, 0, -1):
            print(f"\r[{datetime.now().strftime('%H:%M:%S')}] {Colors.WARNING}Waiting: {remaining}s{Colors.RESET}", end='')
            await asyncio.sleep(1)
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {Colors.SUCCESS}Restarting process{Colors.RESET}\n")

async def main():
    bot = DawnValidatorBot()
    bot.display_welcome()
    
    print(f"{Colors.INFO}Select mode:{Colors.RESET}")
    print("1. Single Account")
    print("2. Multiple Accounts [from accounts.txt]")
    
    while True:
        mode = input(f"{Colors.WARNING}Enter choice (1/2): {Colors.RESET}")
        if mode in ['1', '2']:
            break
        print(f"{Colors.ERROR}ERROR: Invalid choice. Please enter 1 or 2.{Colors.RESET}")
    
    accounts = bot.load_accounts(mode)
    if not accounts:
        bot.log_colored("ERROR", "No accounts available. Exiting...", Colors.ERROR)
        return

    bot.load_proxies()

    try:
        while True:
            bot.log_colored("INFO", "Starting new process", Colors.INFO)
            
            account_tasks = []
            for account in accounts:
                account_tasks.append(bot.process_account(account))

            points_array = await asyncio.gather(*account_tasks)
            
            for i, points in enumerate(points_array):
                if isinstance(points, dict):
                    total_points = points.get('total', 0)
                else:
                    total_points = points
                    
                bot.log_colored("INFO", f"Account {accounts[i]['email']} accumulated: {total_points} points", Colors.WARNING)
            
            bot.log_colored("INFO", "Process completed", Colors.SUCCESS)
            bot.log_colored("INFO", f"Total accounts processed: {len(accounts)}", Colors.INFO)
            
            await bot.countdown(250)

    except KeyboardInterrupt:
        bot.log_colored("WARNING", "Process interrupted by user. Exiting...", Colors.WARNING)
    except Exception as e:
        bot.log_colored("ERROR", f"Fatal error occurred: {str(e)}", Colors.ERROR)

if __name__ == "__main__":
    asyncio.run(main())
