import tkinter as tk
from tkinter import messagebox, ttk
import threading
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from ttkthemes import ThemedTk
import json
import os
from datetime import datetime
import sqlite3
import re
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('twitter_raid_improved.log'),
        logging.StreamHandler()
    ]
)

class TwitterRaidBot:
    def __init__(self):
        self.driver = None
        self.is_running = False
        self.config = self.load_config()
        self.setup_database()
        self.setup_driver()

    def load_config(self):
        if os.path.exists('raid_config.json'):
            with open('raid_config.json', 'r') as f:
                return json.load(f)
        return {
            'delay_min': 3,
            'delay_max': 7,
            'max_actions_per_day': 500,
            'proxy_enabled': False,
            'proxies': [],
            'max_retries': 3,
            'action_delays': {
                'like': 2,
                'retweet': 3,
                'comment': 4
            }
        }

    def save_config(self):
        with open('raid_config.json', 'w') as f:
            json.dump(self.config, f, indent=4)

    def setup_database(self):
        self.conn = sqlite3.connect('twitter_raid.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                username TEXT PRIMARY KEY,
                password TEXT,
                proxy TEXT,
                actions_today INTEGER DEFAULT 0,
                last_action_date TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS actions (
                account_username TEXT,
                action_type TEXT,
                tweet_url TEXT,
                action_date TEXT,
                FOREIGN KEY (account_username) REFERENCES accounts(username)
            )
        ''')
        self.conn.commit()

    def setup_driver(self):
        options = Options()
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        
        if self.config['proxy_enabled'] and self.config['proxies']:
            proxy = random.choice(self.config['proxies'])
            options.add_argument(f'--proxy-server={proxy}')
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

    def login(self, username, password):
        try:
            self.driver.get("https://twitter.com/i/flow/login")
            wait = WebDriverWait(self.driver, 30)

            username_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]')))
            username_field.send_keys(username)
            time.sleep(random.uniform(1, 2))
            
            next_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[role="button"].r-13qz1uu')))
            next_button.click()
            time.sleep(random.uniform(1, 2))

            password_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="password"]')))
            password_field.send_keys(password)
            time.sleep(random.uniform(1, 2))
            
            login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="LoginForm_Login_Button"]')))
            login_button.click()

            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="AppTabBar_Home_Link"]')))
            logging.info(f"Successfully logged in as {username}")
            return True
        except Exception as e:
            logging.error(f"Login failed for {username}: {str(e)}")
            return False

    def can_perform_action(self, username):
        today = datetime.now().strftime('%Y-%m-%d')
        self.cursor.execute('''
            SELECT actions_today, last_action_date 
            FROM accounts 
            WHERE username = ?
        ''', (username,))
        result = self.cursor.fetchone()
        
        if result:
            actions_today, last_action_date = result
            if last_action_date != today:
                self.cursor.execute('''
                    UPDATE accounts 
                    SET actions_today = 0, last_action_date = ? 
                    WHERE username = ?
                ''', (today, username))
                self.conn.commit()
                return True
            return actions_today < self.config['max_actions_per_day']
        return True

    def update_action_count(self, username):
        today = datetime.now().strftime('%Y-%m-%d')
        self.cursor.execute('''
            UPDATE accounts 
            SET actions_today = actions_today + 1, last_action_date = ? 
            WHERE username = ?
        ''', (today, username))
        self.conn.commit()

    def like_tweet(self, username, tweet_url):
        try:
            if not self.can_perform_action(username):
                logging.warning(f"Account {username} has reached daily action limit")
                return False

            self.driver.get(tweet_url)
            wait = WebDriverWait(self.driver, 30)
            
            like_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="like"]')))
            like_button.click()
            time.sleep(random.uniform(self.config['action_delays']['like'], self.config['action_delays']['like'] + 1))

            self.update_action_count(username)
            self.cursor.execute('''
                INSERT INTO actions (account_username, action_type, tweet_url, action_date)
                VALUES (?, ?, ?, ?)
            ''', (username, 'like', tweet_url, datetime.now().strftime('%Y-%m-%d')))
            self.conn.commit()
            
            logging.info(f"Account {username} liked tweet: {tweet_url}")
            return True
        except Exception as e:
            logging.error(f"Failed to like tweet {tweet_url}: {str(e)}")
            return False

    def retweet(self, username, tweet_url):
        try:
            if not self.can_perform_action(username):
                logging.warning(f"Account {username} has reached daily action limit")
                return False

            self.driver.get(tweet_url)
            wait = WebDriverWait(self.driver, 30)
            
            retweet_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="retweet"]')))
            retweet_button.click()
            time.sleep(random.uniform(1, 2))
            
            confirm_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="retweetConfirm"]')))
            confirm_button.click()
            time.sleep(random.uniform(self.config['action_delays']['retweet'], self.config['action_delays']['retweet'] + 1))

            self.update_action_count(username)
            self.cursor.execute('''
                INSERT INTO actions (account_username, action_type, tweet_url, action_date)
                VALUES (?, ?, ?, ?)
            ''', (username, 'retweet', tweet_url, datetime.now().strftime('%Y-%m-%d')))
            self.conn.commit()
            
            logging.info(f"Account {username} retweeted: {tweet_url}")
            return True
        except Exception as e:
            logging.error(f"Failed to retweet {tweet_url}: {str(e)}")
            return False

    def comment(self, username, tweet_url, comment_text):
        try:
            if not self.can_perform_action(username):
                logging.warning(f"Account {username} has reached daily action limit")
                return False

            self.driver.get(tweet_url)
            wait = WebDriverWait(self.driver, 30)
            
            reply_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="reply"]')))
            reply_button.click()
            time.sleep(random.uniform(1, 2))
            
            comment_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[aria-label="Tweet your reply"]')))
            comment_box.click()
            time.sleep(1)
            comment_box.send_keys(comment_text)
            time.sleep(random.uniform(1, 2))
            
            submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="tweetButtonInline"]')))
            submit_button.click()
            time.sleep(random.uniform(self.config['action_delays']['comment'], self.config['action_delays']['comment'] + 1))

            self.update_action_count(username)
            self.cursor.execute('''
                INSERT INTO actions (account_username, action_type, tweet_url, action_date)
                VALUES (?, ?, ?, ?)
            ''', (username, 'comment', tweet_url, datetime.now().strftime('%Y-%m-%d')))
            self.conn.commit()
            
            logging.info(f"Account {username} commented on tweet: {tweet_url}")
            return True
        except Exception as e:
            logging.error(f"Failed to comment on tweet {tweet_url}: {str(e)}")
            return False

    def close(self):
        if self.driver:
            self.driver.quit()
        if self.conn:
            self.conn.close()

class TwitterRaidGUI(ThemedTk):
    def __init__(self):
        super().__init__()
        self.title("Twitter Raid Bot (Improved)")
        self.geometry("800x600")
        self.set_theme("arc")
        
        self.bot = TwitterRaidBot()
        self.create_widgets()
        self.load_config()

    def create_widgets(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.main_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        self.analytics_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.main_tab, text="Main")
        self.notebook.add(self.settings_tab, text="Settings")
        self.notebook.add(self.analytics_tab, text="Analytics")

        self.create_main_tab()
        self.create_settings_tab()
        self.create_analytics_tab()

    def create_main_tab(self):
        # Accounts section
        ttk.Label(self.main_tab, text="Accounts (username:password):").pack(pady=5)
        self.accounts_text = tk.Text(self.main_tab, height=5)
        self.accounts_text.pack(fill=tk.X, padx=5)

        # Tweet URLs section
        ttk.Label(self.main_tab, text="Tweet URLs:").pack(pady=5)
        self.tweets_text = tk.Text(self.main_tab, height=5)
        self.tweets_text.pack(fill=tk.X, padx=5)

        # Comments section
        ttk.Label(self.main_tab, text="Comments:").pack(pady=5)
        self.comments_text = tk.Text(self.main_tab, height=5)
        self.comments_text.pack(fill=tk.X, padx=5)

        # Action checkboxes
        self.like_var = tk.BooleanVar(value=True)
        self.retweet_var = tk.BooleanVar(value=True)
        self.comment_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(self.main_tab, text="Like", variable=self.like_var).pack()
        ttk.Checkbutton(self.main_tab, text="Retweet", variable=self.retweet_var).pack()
        ttk.Checkbutton(self.main_tab, text="Comment", variable=self.comment_var).pack()

        # Threads entry
        ttk.Label(self.main_tab, text="Number of Threads:").pack(pady=5)
        self.threads_entry = ttk.Entry(self.main_tab)
        self.threads_entry.pack()

        # Start button
        ttk.Button(self.main_tab, text="Start Raiding", command=self.start_raiding).pack(pady=10)

        # Status label
        self.status_label = ttk.Label(self.main_tab, text="Status: Ready")
        self.status_label.pack()

    def create_settings_tab(self):
        # Delay settings
        ttk.Label(self.settings_tab, text="Minimum Delay (seconds):").pack(pady=5)
        self.min_delay_entry = ttk.Entry(self.settings_tab)
        self.min_delay_entry.pack()
        self.min_delay_entry.insert(0, str(self.bot.config['delay_min']))

        ttk.Label(self.settings_tab, text="Maximum Delay (seconds):").pack(pady=5)
        self.max_delay_entry = ttk.Entry(self.settings_tab)
        self.max_delay_entry.pack()
        self.max_delay_entry.insert(0, str(self.bot.config['delay_max']))

        # Action limits
        ttk.Label(self.settings_tab, text="Max Actions Per Day:").pack(pady=5)
        self.max_actions_entry = ttk.Entry(self.settings_tab)
        self.max_actions_entry.pack()
        self.max_actions_entry.insert(0, str(self.bot.config['max_actions_per_day']))

        # Action delays
        ttk.Label(self.settings_tab, text="Action Delays:").pack(pady=5)
        self.like_delay_entry = ttk.Entry(self.settings_tab)
        self.like_delay_entry.pack()
        self.like_delay_entry.insert(0, str(self.bot.config['action_delays']['like']))

        self.retweet_delay_entry = ttk.Entry(self.settings_tab)
        self.retweet_delay_entry.pack()
        self.retweet_delay_entry.insert(0, str(self.bot.config['action_delays']['retweet']))

        self.comment_delay_entry = ttk.Entry(self.settings_tab)
        self.comment_delay_entry.pack()
        self.comment_delay_entry.insert(0, str(self.bot.config['action_delays']['comment']))

        # Proxy settings
        self.proxy_var = tk.BooleanVar(value=self.bot.config['proxy_enabled'])
        ttk.Checkbutton(self.settings_tab, text="Enable Proxies", variable=self.proxy_var).pack(pady=5)

        ttk.Label(self.settings_tab, text="Proxies (ip:port:username:password):").pack(pady=5)
        self.proxies_text = tk.Text(self.settings_tab, height=5)
        self.proxies_text.pack(fill=tk.X, padx=5)
        for proxy in self.bot.config['proxies']:
            self.proxies_text.insert(tk.END, proxy + "\n")

        # Save settings button
        ttk.Button(self.settings_tab, text="Save Settings", command=self.save_settings).pack(pady=10)

    def create_analytics_tab(self):
        # Action statistics
        ttk.Label(self.analytics_tab, text="Action Statistics:").pack(pady=5)
        self.stats_text = tk.Text(self.analytics_tab, height=10)
        self.stats_text.pack(fill=tk.X, padx=5)

        # Refresh button
        ttk.Button(self.analytics_tab, text="Refresh Statistics", command=self.refresh_stats).pack(pady=10)

    def load_config(self):
        self.min_delay_entry.delete(0, tk.END)
        self.min_delay_entry.insert(0, str(self.bot.config['delay_min']))
        self.max_delay_entry.delete(0, tk.END)
        self.max_delay_entry.insert(0, str(self.bot.config['delay_max']))
        self.max_actions_entry.delete(0, tk.END)
        self.max_actions_entry.insert(0, str(self.bot.config['max_actions_per_day']))
        self.like_delay_entry.delete(0, tk.END)
        self.like_delay_entry.insert(0, str(self.bot.config['action_delays']['like']))
        self.retweet_delay_entry.delete(0, tk.END)
        self.retweet_delay_entry.insert(0, str(self.bot.config['action_delays']['retweet']))
        self.comment_delay_entry.delete(0, tk.END)
        self.comment_delay_entry.insert(0, str(self.bot.config['action_delays']['comment']))
        self.proxy_var.set(self.bot.config['proxy_enabled'])
        self.proxies_text.delete(1.0, tk.END)
        for proxy in self.bot.config['proxies']:
            self.proxies_text.insert(tk.END, proxy + "\n")

    def save_settings(self):
        try:
            self.bot.config['delay_min'] = float(self.min_delay_entry.get())
            self.bot.config['delay_max'] = float(self.max_delay_entry.get())
            self.bot.config['max_actions_per_day'] = int(self.max_actions_entry.get())
            self.bot.config['action_delays']['like'] = float(self.like_delay_entry.get())
            self.bot.config['action_delays']['retweet'] = float(self.retweet_delay_entry.get())
            self.bot.config['action_delays']['comment'] = float(self.comment_delay_entry.get())
            self.bot.config['proxy_enabled'] = self.proxy_var.get()
            self.bot.config['proxies'] = [line.strip() for line in self.proxies_text.get(1.0, tk.END).split('\n') if line.strip()]
            self.bot.save_config()
            messagebox.showinfo("Success", "Settings saved successfully")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers")

    def refresh_stats(self):
        self.bot.cursor.execute('''
            SELECT account_username, action_type, COUNT(*) as action_count, MAX(action_date) as last_action
            FROM actions
            GROUP BY account_username, action_type
        ''')
        stats = self.bot.cursor.fetchall()
        
        self.stats_text.delete(1.0, tk.END)
        current_account = None
        for stat in stats:
            if current_account != stat[0]:
                current_account = stat[0]
                self.stats_text.insert(tk.END, f"\nAccount: {stat[0]}\n")
            self.stats_text.insert(tk.END, f"  {stat[1]}: {stat[2]} (Last: {stat[3]})\n")

    def start_raiding(self):
        if self.bot.is_running:
            messagebox.showwarning("Warning", "Bot is already running")
            return

        accounts = [line.strip().split(":") for line in self.accounts_text.get(1.0, tk.END).split('\n') if ":" in line]
        tweets = [line.strip() for line in self.tweets_text.get(1.0, tk.END).split('\n') if line.strip()]
        comments = [line.strip() for line in self.comments_text.get(1.0, tk.END).split('\n') if line.strip()]
        threads = int(self.threads_entry.get() or 1)

        if not accounts or not tweets or not comments:
            messagebox.showerror("Error", "Please fill all required fields")
            return

        self.bot.is_running = True
        self.status_label.config(text="Status: Running")
        
        threading.Thread(target=self.run_raiding, args=(accounts, tweets, comments, threads)).start()

    def run_raiding(self, accounts, tweets, comments, threads):
        def worker(account):
            bot = TwitterRaidBot()
            try:
                if bot.login(account[0], account[1]):
                    for tweet in tweets:
                        if not self.bot.is_running:
                            break
                        
                        if self.like_var.get():
                            bot.like_tweet(account[0], tweet)
                        if self.retweet_var.get():
                            bot.retweet(account[0], tweet)
                        if self.comment_var.get():
                            comment = random.choice(comments)
                            bot.comment(account[0], tweet, comment)
            finally:
                bot.close()

        active_threads = []
        for account in accounts:
            if not self.bot.is_running:
                break
                
            if len(active_threads) >= threads:
                for t in active_threads:
                    t.join()
                active_threads = []

            t = threading.Thread(target=worker, args=(account,))
            t.start()
            active_threads.append(t)

        for t in active_threads:
            t.join()

        self.bot.is_running = False
        self.status_label.config(text="Status: Completed")
        messagebox.showinfo("Info", "Raiding completed")
        self.refresh_stats()

if __name__ == "__main__":
    app = TwitterRaidGUI()
    app.mainloop() 
