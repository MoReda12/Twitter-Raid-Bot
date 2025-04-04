import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import threading
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Selenium driver setup
def create_driver():
    try:
        options = Options()
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        return driver
    except Exception as e:
        print(f"Error initializing driver: {e}")
        return None

# Function to log in to Twitter
def twitter_login(driver, username, password):
    try:
        driver.get("https://twitter.com/i/flow/login")
        wait = WebDriverWait(driver, 30)

        username_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]')))
        username_field.send_keys(username)
        driver.find_element(By.CSS_SELECTOR, '[role="button"].r-13qz1uu').click()

        password_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="password"]')))
        password_field.send_keys(password)
        driver.find_element(By.CSS_SELECTOR, '[data-testid="LoginForm_Login_Button"]').click()

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="AppTabBar_Home_Link"]')))
        return True
    except Exception as e:
        print(f"Login error: {e}")
        return False

# Function to interact with tweets
def like_retweet_comment(driver, tweet_urls, comments, perform_like, perform_retweet, perform_comment):
    wait = WebDriverWait(driver, 30)
    for tweet in tweet_urls:
        try:
            driver.get(tweet)
            time.sleep(3)

            # Like
            if perform_like:
                try:
                    like_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="like"]')))
                    like_button.click()
                    print(f"Liked tweet: {tweet}")
                except Exception as e:
                    print(f"Error liking tweet {tweet}: {e}")

            # Retweet
            if perform_retweet:
                try:
                    retweet_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="retweet"]')))
                    retweet_button.click()
                    retweet_confirm = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="retweetConfirm"]')))
                    retweet_confirm.click()
                    print(f"Retweeted tweet: {tweet}")
                except Exception as e:
                    print(f"Error retweeting tweet {tweet}: {e}")

            # Comment
            if perform_comment:
                try:
                    # Find and click the reply button
                    reply_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="reply"]')))
                    reply_button.click()
                    time.sleep(2)

                    # Find the comment text box and type the comment
                    comment_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[aria-label="Tweet your reply"]')))
                    comment_box.click()
                    time.sleep(1)  # Ensure focus is on the comment box
                    comment_box.send_keys(comments[0])  # Use the first comment as an example

                    # Click the reply button to post the comment
                    reply_submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="tweetButtonInline"]')))
                    reply_submit.click()
                    print(f"Commented on tweet: {tweet}")
                except Exception as e:
                    print(f"Error commenting on tweet {tweet}: {e}")
        except Exception as e:
            print(f"Error processing tweet {tweet}: {e}")

# Function to post tweets
def post_tweet(driver, tweet_content):
    try:
        driver.get("https://twitter.com/home")
        wait = WebDriverWait(driver, 30)

        tweet_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[aria-label="Tweet text"]')))
        tweet_box.send_keys(tweet_content)
        driver.find_element(By.CSS_SELECTOR, '[data-testid="tweetButtonInline"]').click()
        print(f"Tweeted: {tweet_content}")
    except Exception as e:
        print(f"Failed to post tweet: {e}")

# GUI Class
class TwitterBotApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Twitter Bot")
        self.geometry("600x500")

        # Tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.main_tab = ttk.Frame(self.notebook)
        self.tweet_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.main_tab, text="Main Raiding")
        self.notebook.add(self.tweet_tab, text="Make Tweet")

        self.create_main_tab()
        self.create_tweet_tab()

        self.driver = None

    def create_main_tab(self):
        tk.Label(self.main_tab, text="Accounts (username:password):").pack()
        self.accounts_text = tk.Text(self.main_tab, height=5)
        self.accounts_text.pack()

        tk.Label(self.main_tab, text="Tweet URLs:").pack()
        self.tweets_text = tk.Text(self.main_tab, height=5)
        self.tweets_text.pack()

        tk.Label(self.main_tab, text="Comments:").pack()
        self.comments_text = tk.Text(self.main_tab, height=5)
        self.comments_text.pack()

        tk.Label(self.main_tab, text="Number of Threads:").pack()
        self.threads_entry = tk.Entry(self.main_tab)
        self.threads_entry.pack()

        # Perform actions checkboxes
        self.perform_like = tk.BooleanVar(value=True)
        self.perform_retweet = tk.BooleanVar(value=True)
        self.perform_comment = tk.BooleanVar(value=True)

        tk.Checkbutton(self.main_tab, text="Like", variable=self.perform_like).pack()
        tk.Checkbutton(self.main_tab, text="Retweet", variable=self.perform_retweet).pack()
        tk.Checkbutton(self.main_tab, text="Comment", variable=self.perform_comment).pack()

        tk.Button(self.main_tab, text="Start", command=self.start_raiding).pack(pady=10)

    def create_tweet_tab(self):
        tk.Label(self.tweet_tab, text="Accounts (username:password):").pack()
        self.accounts_text_tweet = tk.Text(self.tweet_tab, height=5)
        self.accounts_text_tweet.pack()

        tk.Label(self.tweet_tab, text="Tweet Content:").pack()
        self.tweet_content_text = tk.Text(self.tweet_tab, height=5)
        self.tweet_content_text.pack()

        tk.Label(self.tweet_tab, text="Number of Threads:").pack()
        self.threads_entry_tweet = tk.Entry(self.tweet_tab)
        self.threads_entry_tweet.pack()

        tk.Button(self.tweet_tab, text="Post Tweet", command=self.start_tweeting).pack(pady=10)

    def start_raiding(self):
        accounts = [line.strip().split(":") for line in self.accounts_text.get("1.0", tk.END).strip().split("\n") if ":" in line]
        tweets = self.tweets_text.get("1.0", tk.END).strip().split("\n")
        comments = self.comments_text.get("1.0", tk.END).strip().split("\n")
        threads = int(self.threads_entry.get() or 1)

        if not accounts or not tweets or not comments:
            messagebox.showerror("Error", "Please fill all fields.")
            return

        threading.Thread(target=self.run_raiding, args=(accounts, tweets, comments, threads)).start()

    def run_raiding(self, accounts, tweets, comments, threads):
        def worker(account):
            driver = create_driver()
            if driver and twitter_login(driver, account[0], account[1]):
                like_retweet_comment(driver, tweets, comments, self.perform_like.get(), self.perform_retweet.get(), self.perform_comment.get())
            if driver:
                driver.quit()

        active_threads = []
        for account in accounts:
            if len(active_threads) >= threads:
                for t in active_threads:
                    t.join()
                active_threads = []

            t = threading.Thread(target=worker, args=(account,))
            t.start()
            active_threads.append(t)

        for t in active_threads:
            t.join()

    def start_tweeting(self):
        accounts = [line.strip().split(":") for line in self.accounts_text_tweet.get("1.0", tk.END).strip().split("\n") if ":" in line]
        tweet_content = self.tweet_content_text.get("1.0", tk.END).strip()
        threads = int(self.threads_entry_tweet.get() or 1)

        if not accounts or not tweet_content:
            messagebox.showerror("Error", "Please fill all fields.")
            return

        threading.Thread(target=self.run_tweeting, args=(accounts, tweet_content, threads)).start()

    def run_tweeting(self, accounts, tweet_content, threads):
        def worker(account):
            driver = create_driver()
            if driver and twitter_login(driver, account[0], account[1]):
                post_tweet(driver, tweet_content)
            if driver:
                driver.quit()

        active_threads = []
        for account in accounts:
            if len(active_threads) >= threads:
                for t in active_threads:
                    t.join()
                active_threads = []

            t = threading.Thread(target=worker, args=(account,))
            t.start()
            active_threads.append(t)

        for t in active_threads:
            t.join()

if __name__ == "__main__":
    app = TwitterBotApp()
    app.mainloop()
