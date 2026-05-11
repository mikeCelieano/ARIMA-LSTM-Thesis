import sys
import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import csv
from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Mengamankan path import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import fungsi loader baru yang baca dari CSV lokal
from utils.data_loader import fetch_forex_investing, combine_exog
from utils.features import create_price_features
from models.model_manager import ModelManager

import warnings 
warnings.filterwarnings("ignore")

# =========================================================
# SCRAPER INVESTING.COM (AMBIL 1 ROW TERBARU)
# =========================================================
def scrape_investing_daily(currency_pair):
    print(f"🌐 Menghubungi Investing.com untuk {currency_pair.upper()}...")
    
    # 1. SETUP BROWSER (Mengadopsi settingan dari script kamu yang berhasil)
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.page_load_strategy = "eager"
    # Sengaja TIDAK pakai --headless agar tidak diblokir oleh sistem anti-bot.
    # Browser akan muncul sebentar lalu menutup otomatis.

    driver = webdriver.Chrome(options=options)
    url = f"https://www.investing.com/currencies/{currency_pair.lower().replace('/', '-')}-historical-data"
    file_path = f"data/{currency_pair.lower().replace('-', '_')}.csv"

    try:
        driver.get(url)
        time.sleep(3) # Jeda dari kodemu yang terbukti manjur

        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
        
        # Ambil semua baris di tabel
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        
        today_date = datetime.now().date()
        target_data = None
        formatted_date = None

        # 2. LOGIKA PENCARIAN H-1 YANG CERDAS
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            
            if len(cols) >= 7:
                raw_date = cols[0].text.strip()
                
                try:
                    # Parse tanggal dari web (Contoh: "Apr 15, 2026")
                    row_date_obj = pd.to_datetime(raw_date, format="%b %d, %Y").date()
                except:
                    continue # Skip jika format tanggal aneh

                # CEK: Apakah tanggal baris ini SUDAH LEWAT dari hari ini?
                if row_date_obj < today_date:
                    formatted_date = row_date_obj.strftime("%m/%d/%Y")
                    
                    # 3. FORMATTING DATA (Mengadopsi pembersihan dari script kamu)
                    # Mengubah ke float lalu dibalikin ke string dengan koma 1 desimal
                    def format_price(val):
                        clean_val = float(val.replace(',', ''))
                        return f"{clean_val:,.1f}"

                    target_data = [
                        formatted_date,
                        format_price(cols[1].text.strip()), # Price
                        format_price(cols[2].text.strip()), # Open
                        format_price(cols[3].text.strip()), # High
                        format_price(cols[4].text.strip()), # Low
                        cols[5].text.strip(),               # Vol (Biarkan as is)
                        cols[6].text.strip().replace('+', '') # Change % (Hilangkan +)
                    ]
                    break # Berhenti mencari karena kita sudah dapat data H-1 terbaru!

        # 4. PROSES PENYIMPANAN KE CSV
        if target_data and formatted_date:
            if not os.path.exists(file_path):
                print(f"⚠️ File {file_path} tidak ditemukan!")
                return False

            df_local = pd.read_csv(file_path)
            df_local['Date'] = df_local['Date'].astype(str).str.strip()

            # Cek Duplikasi
            if formatted_date in df_local['Date'].values:
                print(f"🛑 [SKIP] Data Closing untuk tanggal {formatted_date} sudah ada di CSV.")
                return False
            
            # Insert ke CSV (Taruh di baris paling atas)
            new_row_df = pd.DataFrame([target_data], columns=df_local.columns)
            df_final = pd.concat([new_row_df, df_local], ignore_index=True)
            
            df_final.to_csv(file_path, index=False, quoting=csv.QUOTE_ALL)
            print(f"🚀 [SUCCESS] Data Closing {formatted_date} berhasil disimpan. Lanjut Train!")
            return True
            
        else:
            print(f"❌ Gagal menemukan baris data histori yang valid (H-1) untuk {currency_pair}.")
            return False

    except Exception as e:
        print(f"❌ Error saat scraping {currency_pair}: {e}")
        return False
        
    finally:
        driver.quit()

def get_latest_bi_rate():
    url = "https://www.bi.go.id/id/statistik/indikator/bi-rate.aspx"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, "lxml")
    table = soup.find("table")
    if table is None: raise ValueError("Tabel BI Rate tidak ditemukan")
    
    rows = table.find_all("tr")
    data = [[col.text.strip() for col in row.find_all(["td", "th"])] for row in rows if row.find_all(["td", "th"])]
    
    df = pd.DataFrame(data)
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)
    
    latest_date = str(df.iloc[0]["Tanggal"]).strip()
    latest_rate = float(df.iloc[0]["BI-Rate"].replace("%", "").strip())
    return latest_date, latest_rate

def get_latest_inflation():
    url = "https://www.bi.go.id/id/statistik/indikator/data-inflasi.aspx"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, "lxml")
    table = soup.find("table")
    if table is None: raise ValueError("Tabel Inflasi tidak ditemukan")
    
    rows = table.find_all("tr")
    data = [[col.text.strip() for col in row.find_all(["td", "th"])] for row in rows if row.find_all(["td", "th"])]
    
    df = pd.DataFrame(data)
    if "Tanggal" not in df.columns:
        df.columns = df.iloc[0]
        df = df[1:].reset_index(drop=True)

    latest_date = str(df.iloc[0].iloc[0]).strip()    
    latest_rate = float(df.iloc[0]["Data Inflasi"].replace("%", "").strip())
    return latest_date, latest_rate

def update_data_csv(file_path, new_date, new_rate, is_inflasi=False):
    if not os.path.exists(file_path):
        print(f"⚠️ File {file_path} tidak ditemukan, skip update CSV.")
        return

    # Baca semua baris CSV
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Ambil tanggal dari baris teratas (index 1 karena index 0 itu header)
    top_row = lines[1]
    top_date = top_row.split(',')[0].strip()

    # Validasi ide lu: Kalau tanggal beda, masukin ke paling atas!
    if new_date != top_date:
        if is_inflasi:
            # Format khusus CSV Inflasi lu yang ada koma di belakang
            new_line = f"{new_date},{new_rate} %,, \n"
        else:
            # Format CSV BI Rate
            new_line = f"{new_date},{new_rate}%\n"
        
        lines.insert(1, new_line) # Selipin di bawah header
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"📁 [CSV UPDATE] Data baru '{new_date}' berhasil disisipkan ke {file_path}!")
    else:
        print(f"📁 [CSV UPDATE] data tanggal '{new_date}' sudah ada di {file_path}. Skip insert.")


# =========================================================
# MAIN DAILY RETRAINING PIPELINE
# =========================================================
def run_daily_retraining(currency_list=["USD/IDR", "EUR/IDR", "GBP/IDR"]):
    print(f"🚀 Memulai Daily Pipeline: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Update BI Rate & Inflasi
    try:
        bi_date, bi_rate = get_latest_bi_rate()
        update_data_csv("data/BI-7Day-RR.csv", bi_date, bi_rate)
        
        inf_date, inf_rate = get_latest_inflation()
        update_data_csv("data/Data Inflasi.csv", inf_date, inf_rate, is_inflasi=True)
    except Exception as e:
        print(f"⚠️ Warning: Gagal update data ekonomi harian: {e}")
        # Tetap lanjut karena kita bisa pakai data terakhir yang ada di CSV

    # 2. Update Forex & Retrain
    for currency in currency_list:
        print(f"\n🔄 Memproses {currency}...")
        
        pair_slug = currency.lower().replace('/', '-') # misal 'usd/idr' -> 'usd-idr'
        base_curr = currency.split('/')[0]
        
        # STEP A: Scraping Investing.com & Update CSV
        success = scrape_investing_daily(pair_slug)
        
        if not success:
            print(f"⚠️ Skip retraining {currency} karena scraping gagal.")
            continue

        try:
            df_full = fetch_forex_investing(base_curr)
            
            df_features = create_price_features(df_full)
            
            exog_all = combine_exog()
            df_merged = df_features.join(exog_all, how="left").ffill().bfill()
            
            # latest_point = df_merged.iloc[[-1]]
            # target_1d = latest_point[['Close Price']]
            # exog_1d = latest_point[['Open_lag1', 'High_lag1', 'Low_lag1', 'Close_lag1', 'Return', 'HL_Spread', 'Inflasi', 'BI Rate']]
            
            # seq_point = df_merged.iloc[-30:] 
            # target_seq = seq_point[['Close Price']]
            # exog_seq = seq_point[['Open_lag1', 'High_lag1', 'Low_lag1', 'Close_lag1', 'Return', 'HL_Spread', 'Inflasi', 'BI Rate']]

            target_seq = df_merged.iloc[-31:][['Close Price']]
            exog_seq = df_merged.iloc[-31:][['Open_lag1', 'High_lag1', 'Low_lag1', 'Close_lag1', 'Return', 'HL_Spread', 'Inflasi', 'BI Rate']]

            latest_point = df_merged.iloc[[-1]]
            print(f"📅 Data Tanggal: {latest_point.index[0].date()}")
            
            # STEP E: Incremental Retraining (Loop untuk Baseline & Tuned)
            modes_to_train = ["baseline", "tuned"]
            
            for mode in modes_to_train:
                print(f"\n   ⚙️ Memproses model mode: [{mode.upper()}]")
                manager = ModelManager(currency, mode=mode)
                
                if manager.load_all_models():
                    print(f"   -> Updating ARIMA {mode}...")
                    manager.arima.append_data(target_seq, exog_seq) # <-- Pakai data 1 hari
                    
                    print(f"   -> Updating LSTM {mode} (1 Epoch)...")
                    manager.lstm.incremental_train(target_seq, exog_seq) # <-- Pakai data 30 hari
                    
                    print(f"   -> Updating Hybrid {mode}...")
                    manager.hybrid.incremental_train(target_seq, exog_seq) # <-- Pakai data 30 hari
                    
                    manager.save_all_models()
                    print(f"   ✅ Model {currency} ({mode}) Berhasil Diperbarui!")
                else:
                    print(f"   ⚠️ Model {currency} ({mode}) tidak ditemukan. Pastikan sudah di-train penuh sebelumnya.")
        except Exception as e:
            print(f"❌ Error training {currency}: {e}")

    print("\n🎉 Proses Daily Training Selesai!")

if __name__ == "__main__":
    run_daily_retraining()
