# import sys
# import os
# import requests
# from bs4 import BeautifulSoup
# import pandas as pd
# import numpy as np
# import csv
# from datetime import datetime
# import time
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC

# # Mengamankan path import
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# # Import fungsi loader baru yang baca dari CSV lokal
# from utils.data_loader import fetch_forex_investing, combine_exog
# from utils.features import create_price_features
# from models.model_manager import ModelManager

# import warnings 
# warnings.filterwarnings("ignore")

# # =========================================================
# # SCRAPER INVESTING.COM (AMBIL 1 ROW TERBARU)
# # =========================================================
# def scrape_investing_daily(currency_pair):
#     print(f"🌐 Menghubungi Investing.com untuk {currency_pair.upper()}...")
    
#     # 1. SETUP BROWSER (Mengadopsi settingan dari script kamu yang berhasil)
#     options = Options()
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-dev-shm-usage")
#     options.page_load_strategy = "eager"
#     # Sengaja TIDAK pakai --headless agar tidak diblokir oleh sistem anti-bot.
#     # Browser akan muncul sebentar lalu menutup otomatis.

#     driver = webdriver.Chrome(options=options)
#     url = f"https://www.investing.com/currencies/{currency_pair.lower().replace('/', '-')}-historical-data"
#     file_path = f"data/{currency_pair.lower().replace('-', '_')}.csv"

#     try:
#         driver.get(url)
#         time.sleep(3) # Jeda dari kodemu yang terbukti manjur

#         wait = WebDriverWait(driver, 20)
#         wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
        
#         # Ambil semua baris di tabel
#         rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        
#         today_date = datetime.now().date()
#         target_data = None
#         formatted_date = None

#         # 2. LOGIKA PENCARIAN H-1 YANG CERDAS
#         for row in rows:
#             cols = row.find_elements(By.TAG_NAME, "td")
            
#             if len(cols) >= 7:
#                 raw_date = cols[0].text.strip()
                
#                 try:
#                     # Parse tanggal dari web (Contoh: "Apr 15, 2026")
#                     row_date_obj = pd.to_datetime(raw_date, format="%b %d, %Y").date()
#                 except:
#                     continue # Skip jika format tanggal aneh

#                 # CEK: Apakah tanggal baris ini SUDAH LEWAT dari hari ini?
#                 if row_date_obj < today_date:
#                     formatted_date = row_date_obj.strftime("%m/%d/%Y")
                    
#                     # 3. FORMATTING DATA (Mengadopsi pembersihan dari script kamu)
#                     # Mengubah ke float lalu dibalikin ke string dengan koma 1 desimal
#                     def format_price(val):
#                         clean_val = float(val.replace(',', ''))
#                         return f"{clean_val:,.1f}"

#                     target_data = [
#                         formatted_date,
#                         format_price(cols[1].text.strip()), # Price
#                         format_price(cols[2].text.strip()), # Open
#                         format_price(cols[3].text.strip()), # High
#                         format_price(cols[4].text.strip()), # Low
#                         cols[5].text.strip(),               # Vol (Biarkan as is)
#                         cols[6].text.strip().replace('+', '') # Change % (Hilangkan +)
#                     ]
#                     break # Berhenti mencari karena kita sudah dapat data H-1 terbaru!

#         # 4. PROSES PENYIMPANAN KE CSV
#         if target_data and formatted_date:
#             if not os.path.exists(file_path):
#                 print(f"⚠️ File {file_path} tidak ditemukan!")
#                 return False

#             df_local = pd.read_csv(file_path)
#             df_local['Date'] = df_local['Date'].astype(str).str.strip()

#             # Cek Duplikasi
#             if formatted_date in df_local['Date'].values:
#                 print(f"🛑 [SKIP] Data Closing untuk tanggal {formatted_date} sudah ada di CSV.")
#                 return False
            
#             # Insert ke CSV (Taruh di baris paling atas)
#             new_row_df = pd.DataFrame([target_data], columns=df_local.columns)
#             df_final = pd.concat([new_row_df, df_local], ignore_index=True)
            
#             df_final.to_csv(file_path, index=False, quoting=csv.QUOTE_ALL)
#             print(f"🚀 [SUCCESS] Data Closing {formatted_date} berhasil disimpan. Lanjut Train!")
#             return True
            
#         else:
#             print(f"❌ Gagal menemukan baris data histori yang valid (H-1) untuk {currency_pair}.")
#             return False

#     except Exception as e:
#         print(f"❌ Error saat scraping {currency_pair}: {e}")
#         return False
        
#     finally:
#         driver.quit()

# def get_latest_bi_rate():
#     url = "https://www.bi.go.id/id/statistik/indikator/bi-rate.aspx"
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
#         "Accept-Language": "en-US,en;q=0.9"
#     }
#     response = requests.get(url, headers=headers)
#     response.raise_for_status()
    
#     soup = BeautifulSoup(response.text, "lxml")
#     table = soup.find("table")
#     if table is None: raise ValueError("Tabel BI Rate tidak ditemukan")
    
#     rows = table.find_all("tr")
#     data = [[col.text.strip() for col in row.find_all(["td", "th"])] for row in rows if row.find_all(["td", "th"])]
    
#     df = pd.DataFrame(data)
#     df.columns = df.iloc[0]
#     df = df[1:].reset_index(drop=True)
    
#     latest_date = str(df.iloc[0]["Tanggal"]).strip()
#     latest_rate = float(df.iloc[0]["BI-Rate"].replace("%", "").strip())
#     return latest_date, latest_rate

# def get_latest_inflation():
#     url = "https://www.bi.go.id/id/statistik/indikator/data-inflasi.aspx"
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
#         "Accept-Language": "en-US,en;q=0.9"
#     }
#     response = requests.get(url, headers=headers)
#     response.raise_for_status()
    
#     soup = BeautifulSoup(response.text, "lxml")
#     table = soup.find("table")
#     if table is None: raise ValueError("Tabel Inflasi tidak ditemukan")
    
#     rows = table.find_all("tr")
#     data = [[col.text.strip() for col in row.find_all(["td", "th"])] for row in rows if row.find_all(["td", "th"])]
    
#     df = pd.DataFrame(data)
#     if "Tanggal" not in df.columns:
#         df.columns = df.iloc[0]
#         df = df[1:].reset_index(drop=True)

#     latest_date = str(df.iloc[0].iloc[0]).strip()    
#     latest_rate = float(df.iloc[0]["Data Inflasi"].replace("%", "").strip())
#     return latest_date, latest_rate

# def update_data_csv(file_path, new_date, new_rate, is_inflasi=False):
#     if not os.path.exists(file_path):
#         print(f"⚠️ File {file_path} tidak ditemukan, skip update CSV.")
#         return

#     # Baca semua baris CSV
#     with open(file_path, 'r', encoding='utf-8') as f:
#         lines = f.readlines()

#     # Ambil tanggal dari baris teratas (index 1 karena index 0 itu header)
#     top_row = lines[1]
#     top_date = top_row.split(',')[0].strip()

#     # Validasi ide lu: Kalau tanggal beda, masukin ke paling atas!
#     if new_date != top_date:
#         if is_inflasi:
#             # Format khusus CSV Inflasi lu yang ada koma di belakang
#             new_line = f"{new_date},{new_rate} %,, \n"
#         else:
#             # Format CSV BI Rate
#             new_line = f"{new_date},{new_rate}%\n"
        
#         lines.insert(1, new_line) # Selipin di bawah header
        
#         with open(file_path, 'w', encoding='utf-8') as f:
#             f.writelines(lines)
#         print(f"📁 [CSV UPDATE] Data baru '{new_date}' berhasil disisipkan ke {file_path}!")
#     else:
#         print(f"📁 [CSV UPDATE] data tanggal '{new_date}' sudah ada di {file_path}. Skip insert.")


# # =========================================================
# # MAIN DAILY RETRAINING PIPELINE
# # =========================================================
# def run_daily_retraining(currency_list=["USD/IDR", "EUR/IDR", "GBP/IDR"]):
#     print(f"🚀 Memulai Daily Pipeline: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
#     # 1. Update BI Rate & Inflasi
#     try:
#         bi_date, bi_rate = get_latest_bi_rate()
#         update_data_csv("data/BI-7Day-RR.csv", bi_date, bi_rate)
        
#         inf_date, inf_rate = get_latest_inflation()
#         update_data_csv("data/Data Inflasi.csv", inf_date, inf_rate, is_inflasi=True)
#     except Exception as e:
#         print(f"⚠️ Warning: Gagal update data ekonomi harian: {e}")
#         # Tetap lanjut karena kita bisa pakai data terakhir yang ada di CSV

#     # 2. Update Forex & Retrain
#     for currency in currency_list:
#         print(f"\n🔄 Memproses {currency}...")
        
#         pair_slug = currency.lower().replace('/', '-') # misal 'usd/idr' -> 'usd-idr'
#         base_curr = currency.split('/')[0]
        
#         # STEP A: Scraping Investing.com & Update CSV
#         success = scrape_investing_daily(pair_slug)
        
#         if not success:
#             print(f"⚠️ Skip retraining {currency} karena scraping gagal.")
#             continue

#         try:
#             df_full = fetch_forex_investing(base_curr)
            
#             df_features = create_price_features(df_full)
            
#             exog_all = combine_exog()
#             df_merged = df_features.join(exog_all, how="left").ffill().bfill()
            
#             # latest_point = df_merged.iloc[[-1]]
#             # target_1d = latest_point[['Close Price']]
#             # exog_1d = latest_point[['Open_lag1', 'High_lag1', 'Low_lag1', 'Close_lag1', 'Return', 'HL_Spread', 'Inflasi', 'BI Rate']]
            
#             # seq_point = df_merged.iloc[-30:] 
#             # target_seq = seq_point[['Close Price']]
#             # exog_seq = seq_point[['Open_lag1', 'High_lag1', 'Low_lag1', 'Close_lag1', 'Return', 'HL_Spread', 'Inflasi', 'BI Rate']]

#             target_seq = df_merged.iloc[-31:][['Close Price']]
#             exog_seq = df_merged.iloc[-31:][['Open_lag1', 'High_lag1', 'Low_lag1', 'Close_lag1', 'Return', 'HL_Spread', 'Inflasi', 'BI Rate']]

#             latest_point = df_merged.iloc[[-1]]
#             print(f"📅 Data Tanggal: {latest_point.index[0].date()}")
            
#             # STEP E: Incremental Retraining (Loop untuk Baseline & Tuned)
#             modes_to_train = ["baseline", "tuned"]
            
#             for mode in modes_to_train:
#                 print(f"\n   ⚙️ Memproses model mode: [{mode.upper()}]")
#                 manager = ModelManager(currency, mode=mode)
                
#                 if manager.load_all_models():
#                     print(f"   -> Updating ARIMA {mode}...")
#                     manager.arima.append_data(target_seq, exog_seq) # <-- Pakai data 1 hari
                    
#                     print(f"   -> Updating LSTM {mode} (1 Epoch)...")
#                     manager.lstm.incremental_train(target_seq, exog_seq) # <-- Pakai data 30 hari
                    
#                     print(f"   -> Updating Hybrid {mode}...")
#                     manager.hybrid.incremental_train(target_seq, exog_seq) # <-- Pakai data 30 hari
                    
#                     manager.save_all_models()
#                     print(f"   ✅ Model {currency} ({mode}) Berhasil Diperbarui!")
#                 else:
#                     print(f"   ⚠️ Model {currency} ({mode}) tidak ditemukan. Pastikan sudah di-train penuh sebelumnya.")
#         except Exception as e:
#             print(f"❌ Error training {currency}: {e}")

#     print("\n🎉 Proses Daily Training Selesai!")

# if __name__ == "__main__":
#     run_daily_retraining()

"""
Daily Forex Model Retraining Pipeline
=====================================
- Scrape Investing.com (USD/IDR, EUR/IDR, GBP/IDR) untuk close H-1
- Scrape BI Rate & Inflasi dari bi.go.id
- Incremental retraining ARIMA / LSTM / Hybrid (baseline & tuned)

Dirancang untuk jalan di dua tempat:
  - Lokal (Mac/Windows)  → Chrome muncul visible
  - GitHub Actions (CI)  → Chrome headless dengan anti-detection
"""

import sys
import os
import csv
import time
import random
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# =========================================================
# KONFIGURASI GLOBAL
# =========================================================

# Pastikan path import konsisten regardless of cwd
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DATA_DIR = PROJECT_ROOT / "data"

# GitHub Actions otomatis set CI=true; ini cara aman deteksi server env
IS_CI = os.getenv("CI", "").lower() == "true"

# Bikin print() langsung muncul di log GitHub Actions (no buffer)
try:
    sys.stdout.reconfigure(line_buffering=True)
except AttributeError:
    pass

# Import internal modules (setelah sys.path setup)
from utils.data_loader import fetch_forex_investing, combine_exog  # noqa: E402
from utils.features import create_price_features  # noqa: E402
from models.model_manager import ModelManager  # noqa: E402

import warnings  # noqa: E402
warnings.filterwarnings("ignore")

# User-agent realistis Chrome 120 di tiga OS umum
USER_AGENTS = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

REQUEST_HEADERS = {
    "User-Agent": USER_AGENTS[0],
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


# =========================================================
# DRIVER FACTORY (dengan anti-detection)
# =========================================================
def create_driver():
    """
    Build Chrome WebDriver. Headless + anti-detection di CI,
    visible di lokal (untuk debugging).
    """
    options = Options()

    if IS_CI:
        # Mandatory di server tanpa display
        options.add_argument("--headless=new")  # new headless = lebih mirip browser asli
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

    # Anti-detection — supaya site ga gampang flag selenium
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")
    options.add_argument("--lang=en-US,en;q=0.9")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    options.page_load_strategy = "eager"

    driver = webdriver.Chrome(options=options)

    # Hide navigator.webdriver flag (cara paling efektif)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """
        },
    )

    return driver


# =========================================================
# SCRAPER INVESTING.COM (dengan retry)
# =========================================================
def scrape_investing_daily(currency_pair, max_retries=3):
    """
    Ambil 1 row data H-1 dari Investing.com untuk pasangan mata uang tertentu.
    Return True kalau berhasil simpan, False kalau gagal atau data sudah ada.
    """
    print(f"🌐 Menghubungi Investing.com untuk {currency_pair.upper()}...", flush=True)

    url = (
        f"https://www.investing.com/currencies/"
        f"{currency_pair.lower().replace('/', '-')}-historical-data"
    )
    file_path = DATA_DIR / f"{currency_pair.lower().replace('-', '_')}.csv"

    last_error = None

    for attempt in range(1, max_retries + 1):
        print(f"   🔁 Percobaan {attempt}/{max_retries}...", flush=True)
        driver = None
        try:
            driver = create_driver()
            driver.get(url)

            # Jeda random — biar lebih natural, ga keliatan bot
            time.sleep(random.uniform(3, 6))

            wait = WebDriverWait(driver, 30)
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
            )

            rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            if not rows:
                raise ValueError("Tabel ditemukan tapi kosong (mungkin Cloudflare)")

            today_date = datetime.now().date()
            target_data = None
            formatted_date = None

            # Cari row paling baru yang tanggalnya < today (H-1 atau lebih)
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) < 7:
                    continue

                raw_date = cols[0].text.strip()
                try:
                    row_date_obj = pd.to_datetime(raw_date, format="%b %d, %Y").date()
                except Exception:
                    continue  # skip baris dengan format tanggal aneh

                if row_date_obj < today_date:
                    formatted_date = row_date_obj.strftime("%m/%d/%Y")

                    def format_price(val):
                        clean_val = float(val.replace(",", ""))
                        return f"{clean_val:,.1f}"

                    target_data = [
                        formatted_date,
                        format_price(cols[1].text.strip()),  # Price
                        format_price(cols[2].text.strip()),  # Open
                        format_price(cols[3].text.strip()),  # High
                        format_price(cols[4].text.strip()),  # Low
                        cols[5].text.strip(),                # Vol (as-is)
                        cols[6].text.strip().replace("+", ""),  # Change %
                    ]
                    break

            if not (target_data and formatted_date):
                raise ValueError("Tidak menemukan baris H-1 yang valid di tabel")

            # === Simpan ke CSV ===
            if not file_path.exists():
                print(f"⚠️ File {file_path} tidak ditemukan!", flush=True)
                return False

            df_local = pd.read_csv(file_path)
            df_local["Date"] = df_local["Date"].astype(str).str.strip()

            if formatted_date in df_local["Date"].values:
                print(
                    f"🛑 [SKIP] Data tanggal {formatted_date} sudah ada di CSV.",
                    flush=True,
                )
                return False

            new_row_df = pd.DataFrame([target_data], columns=df_local.columns)
            df_final = pd.concat([new_row_df, df_local], ignore_index=True)
            df_final.to_csv(file_path, index=False, quoting=csv.QUOTE_ALL)

            print(
                f"🚀 [SUCCESS] Data {formatted_date} berhasil disimpan. Lanjut Train!",
                flush=True,
            )
            return True

        except TimeoutException as e:
            last_error = f"Timeout (kemungkinan kena Cloudflare challenge): {e}"
            print(f"   ⏱️  {last_error}", flush=True)
        except WebDriverException as e:
            last_error = f"WebDriver error: {e}"
            print(f"   🔧 {last_error}", flush=True)
        except Exception as e:
            last_error = f"{type(e).__name__}: {e}"
            print(f"   ❌ {last_error}", flush=True)
        finally:
            if driver is not None:
                try:
                    driver.quit()
                except Exception:
                    pass

        # Exponential backoff sebelum retry berikutnya
        if attempt < max_retries:
            wait_time = 10 * attempt
            print(f"   ⏳ Menunggu {wait_time}s sebelum retry...", flush=True)
            time.sleep(wait_time)

    print(
        f"❌ Gagal scraping {currency_pair} setelah {max_retries} percobaan. "
        f"Last error: {last_error}",
        flush=True,
    )
    return False


# =========================================================
# SCRAPER BI RATE & INFLASI (requests, lebih ringan)
# =========================================================
def _fetch_bi_table(url, table_name, max_retries=3):
    """Helper umum untuk fetch tabel HTML dari bi.go.id dengan retry."""
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=REQUEST_HEADERS, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            table = soup.find("table")
            if table is None:
                raise ValueError(f"Tabel {table_name} tidak ditemukan")
            return table
        except Exception as e:
            print(
                f"   ⚠️  Gagal fetch {table_name} (percobaan {attempt}): {e}",
                flush=True,
            )
            if attempt < max_retries:
                time.sleep(5 * attempt)
            else:
                raise


def get_latest_bi_rate():
    url = "https://www.bi.go.id/id/statistik/indikator/bi-rate.aspx"
    table = _fetch_bi_table(url, "BI Rate")

    rows = table.find_all("tr")
    data = [
        [col.text.strip() for col in row.find_all(["td", "th"])]
        for row in rows
        if row.find_all(["td", "th"])
    ]

    df = pd.DataFrame(data)
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)

    latest_date = str(df.iloc[0]["Tanggal"]).strip()
    latest_rate = float(df.iloc[0]["BI-Rate"].replace("%", "").strip())
    return latest_date, latest_rate


def get_latest_inflation():
    url = "https://www.bi.go.id/id/statistik/indikator/data-inflasi.aspx"
    table = _fetch_bi_table(url, "Inflasi")

    rows = table.find_all("tr")
    data = [
        [col.text.strip() for col in row.find_all(["td", "th"])]
        for row in rows
        if row.find_all(["td", "th"])
    ]

    df = pd.DataFrame(data)
    if "Tanggal" not in df.columns:
        df.columns = df.iloc[0]
        df = df[1:].reset_index(drop=True)

    latest_date = str(df.iloc[0].iloc[0]).strip()
    latest_rate = float(df.iloc[0]["Data Inflasi"].replace("%", "").strip())
    return latest_date, latest_rate


def update_data_csv(file_path, new_date, new_rate, is_inflasi=False):
    """Sisipkan baris baru di posisi paling atas CSV (di bawah header)."""
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"⚠️ File {file_path} tidak ditemukan, skip update CSV.", flush=True)
        return

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if len(lines) < 2:
        print(f"⚠️ File {file_path} kosong / tidak punya data, skip.", flush=True)
        return

    top_row = lines[1]
    top_date = top_row.split(",")[0].strip()

    if new_date != top_date:
        if is_inflasi:
            new_line = f"{new_date},{new_rate} %,, \n"
        else:
            new_line = f"{new_date},{new_rate}%\n"
        lines.insert(1, new_line)

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(
            f"📁 [CSV UPDATE] Data baru '{new_date}' berhasil disisipkan ke "
            f"{file_path.name}",
            flush=True,
        )
    else:
        print(
            f"📁 [CSV UPDATE] Data tanggal '{new_date}' sudah ada di "
            f"{file_path.name}. Skip.",
            flush=True,
        )


# =========================================================
# MAIN PIPELINE
# =========================================================
def run_daily_retraining(currency_list=("USD/IDR", "EUR/IDR", "GBP/IDR")):
    print(
        f"🚀 Memulai Daily Pipeline: "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} "
        f"(CI={IS_CI})",
        flush=True,
    )

    # === 1. Update BI Rate & Inflasi ===
    try:
        bi_date, bi_rate = get_latest_bi_rate()
        update_data_csv(DATA_DIR / "BI-7Day-RR.csv", bi_date, bi_rate)
    except Exception as e:
        print(f"⚠️ Warning: Gagal update BI Rate: {e}", flush=True)

    try:
        inf_date, inf_rate = get_latest_inflation()
        update_data_csv(
            DATA_DIR / "Data Inflasi.csv", inf_date, inf_rate, is_inflasi=True
        )
    except Exception as e:
        print(f"⚠️ Warning: Gagal update Inflasi: {e}", flush=True)

    # === 2. Update Forex + Retrain per currency ===
    for currency in currency_list:
        print(f"\n🔄 Memproses {currency}...", flush=True)

        pair_slug = currency.lower().replace("/", "-")
        base_curr = currency.split("/")[0]

        # STEP A: Scrape Investing.com
        success = scrape_investing_daily(pair_slug)

        if not success:
            print(
                f"⚠️ Skip retraining {currency} karena scraping gagal atau "
                f"data sudah up-to-date.",
                flush=True,
            )
            continue

        try:
            # STEP B: Load full dataset (sudah ter-update) + features + exog
            df_full = fetch_forex_investing(base_curr)
            df_features = create_price_features(df_full)
            exog_all = combine_exog()
            df_merged = df_features.join(exog_all, how="left").ffill().bfill()

            # 31 hari terakhir untuk sequence training (LSTM butuh window 30)
            target_seq = df_merged.iloc[-31:][["Close Price"]]
            exog_seq = df_merged.iloc[-31:][[
                "Open_lag1", "High_lag1", "Low_lag1", "Close_lag1",
                "Return", "HL_Spread", "Inflasi", "BI Rate",
            ]]

            latest_point = df_merged.iloc[[-1]]
            print(f"📅 Data Tanggal: {latest_point.index[0].date()}", flush=True)

            # STEP C: Incremental retrain — baseline & tuned
            for mode in ("baseline", "tuned"):
                print(f"\n   ⚙️  Memproses model mode: [{mode.upper()}]", flush=True)
                manager = ModelManager(currency, mode=mode)

                if not manager.load_all_models():
                    print(
                        f"   ⚠️ Model {currency} ({mode}) tidak ditemukan. "
                        f"Pastikan sudah di-train penuh sebelumnya.",
                        flush=True,
                    )
                    continue

                print(f"   -> Updating ARIMA {mode}...", flush=True)
                manager.arima.append_data(target_seq, exog_seq)

                print(f"   -> Updating LSTM {mode} (1 epoch)...", flush=True)
                manager.lstm.incremental_train(target_seq, exog_seq)

                print(f"   -> Updating Hybrid {mode}...", flush=True)
                manager.hybrid.incremental_train(target_seq, exog_seq)

                manager.save_all_models()
                print(
                    f"   ✅ Model {currency} ({mode}) berhasil diperbarui!",
                    flush=True,
                )

        except Exception as e:
            print(f"❌ Error training {currency}: {type(e).__name__}: {e}", flush=True)
            # Lanjut ke currency berikutnya, jangan stop seluruh pipeline
            continue

    print("\n🎉 Proses Daily Training Selesai!", flush=True)


if __name__ == "__main__":
    run_daily_retraining()