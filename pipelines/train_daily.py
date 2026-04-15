# import sys
# import os
# import requests
# from bs4 import BeautifulSoup
# import pandas as pd
# from datetime import datetime

# # Mengamankan path import
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# from utils.data_loader import fetch_forex_alpha
# from utils.features import create_price_features
# from models.model_manager import ModelManager

# import warnings 
# warnings.filterwarnings("ignore")

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

# def append_forex_csv(base_curr, df_raw):
#     # Pemetaan file sesuai dengan data_loader.py
#     file_map = {"USD": "data/usd_idr.csv", "EUR": "data/eur_idr.csv", "GBP": "data/gbp_idr.csv"}
#     file_path = file_map.get(base_curr)
    
#     if not file_path or not os.path.exists(file_path):
#         print(f"⚠️ File {file_path} tidak ditemukan, skip append CSV.")
#         return

#     # Ambil baris data paling terakhir (terbaru) dari hasil tarikan API
#     latest_date = df_raw.index[-1].strftime('%Y-%m-%d')
#     close_p = df_raw['Close Price'].iloc[-1]
#     open_p = df_raw['Open'].iloc[-1]
#     high_p = df_raw['High'].iloc[-1]
#     low_p = df_raw['Low'].iloc[-1]
    
#     # Buka CSV untuk membaca baris paling bawah
#     with open(file_path, 'r', encoding='utf-8') as f:
#         lines = f.readlines()
        
#     last_line = lines[-1]
#     last_date_csv = last_line.split(',')[0].strip()
    
#     # Validasi: Masukkan hanya jika tanggal terbaru belum ada di ujung CSV
#     if latest_date not in last_date_csv:
#         # Pengecekan agar data baru tidak menempel di baris yang sama jika tidak ada enter
#         prefix = "" if last_line.endswith('\n') else "\n"
        
#         # Susunan wajib sama dengan CSV lama: Date, Close Price, Open, High, Low
#         new_line = f"{prefix}{latest_date},{close_p},{open_p},{high_p},{low_p}\n"
        
#         # Mode 'a' (append) untuk men   empelkan di akhir file
#         with open(file_path, 'a', encoding='utf-8') as f:
#             f.write(new_line)
#         print(f"📁 [CSV UPDATE] Data baru '{latest_date}' berhasil di-append ke ujung {file_path}!")
#     else:
#         print(f"📁 [CSV UPDATE] Data '{latest_date}' sudah ada di ujung {file_path}. Skip append.")

# def run_daily_retraining(currency_list=["USD/IDR", "EUR/IDR", "GBP/IDR"]):
#     print(f"🚀 Memulai Daily Retraining Pipeline: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
#     print("📥 Melakukan Web Scraping BI Rate terbaru...")
#     latest_bi_date, latest_bi = get_latest_bi_rate()
#     print(f"✅ Berhasil! BI Rate saat ini: {latest_bi}%")
#     update_data_csv("data/BI-7Day-RR.csv", latest_bi_date, latest_bi, is_inflasi=False)
    
#     print("📥 Melakukan Web Scraping Inflasi terbaru...")
#     latest_inf_date, latest_inf = get_latest_inflation()
#     print(f"✅ Berhasil! Inflasi saat ini: {latest_inf}%")
#     update_data_csv("data/Data Inflasi.csv", latest_inf_date, latest_inf, is_inflasi=True)
    
#     for currency in currency_list:
#         print(f"\n🔄 Memperbarui model untuk {currency}...")
        
#         base_curr = currency.split('/')[0]
        
#         try:
#             #Tarik Data Historis Forex dari API 
#             df_raw = fetch_forex_alpha(base_curr, "IDR")
            
#             #Update CSV data forex
#             append_forex_csv(base_curr, df_raw)

#             #Hitung fitur (Lag, Return, Spread) menggunakan keseluruhan data
#             df_features = create_price_features(df_raw)
            
#             #Ambil HANYA baris terakhir (data hari ini/kemarin)
#             latest_data_point = df_features.iloc[[-1]].copy()
            
#             #Tempelkan data makroekonomi hasil scraping
#             latest_data_point['BI Rate'] = latest_bi
#             latest_data_point['Inflasi'] = latest_inf
            
#             #Pisahkan jadi format Target & Exog
#             latest_target = latest_data_point[['Close Price']]
#             latest_exog = latest_data_point[['Open_lag1', 'High_lag1', 'Low_lag1', 'Close_lag1', 'Return', 'HL_Spread', 'Inflasi', 'BI Rate']]
            
#             print(f"📅 Memasukkan data tanggal: {latest_data_point.index[0].strftime('%Y-%m-%d')}")
            
#             # ======================================================
#             # FITUR INSPEKSI DATA (Melihat data sebelum masuk model)
#             # ======================================================
#             print("\n🔍 [INSPEKSI DATA] Data yang akan masuk ke model:")
#             print("▶️ TARGET (Y) - Harga Close yang akan dipelajari:")
#             print(latest_target.to_string())
#             print("\n▶️ FITUR EKSOGEN (X) - Variabel pendukung:")
#             print(latest_exog.to_string())
#             print("========================================================\n")
            
#             manager = ModelManager(currency, mode="tuned")
#             if not manager.load_all_models():
#                 print(f"⚠️ Model untuk {currency} belum ada. Lewati update harian.")
#                 continue
                
#             # 7. Incremental Training 
#             print("-> Updating ARIMA...")
#             manager.arima.append_data(latest_target, latest_exog) 
            
#             print("-> Updating LSTM (1 Epoch)...")
#             manager.lstm.incremental_train(latest_target, latest_exog)
            
#             print("-> Updating Hybrid Model...")
#             manager.hybrid.incremental_train(latest_target, latest_exog)
            
#             manager.save_all_models()
#             print(f"✅ Model {currency} berhasil diperbarui dan disimpan!")
            
#         except Exception as e:
#             print(f"❌ Gagal memperbarui {currency}: {e}")
            
#     print("\n🎉 Proses Daily Training Selesai!")

# if __name__ == "__main__":
#     run_daily_retraining()

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
from utils.data_loader import fetch_forex_investing, combine_exog, create_price_features
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
            # STEP B: Load Full Data dari CSV (Sudah termasuk data baru tadi)
            # Pakai fetch_forex_investing yang sudah dimodifikasi di data_loader
            df_full = fetch_forex_investing(base_curr)
            
            # STEP C: Feature Engineering
            df_features = create_price_features(df_full)
            
            # STEP D: Gabungkan dengan Exogen terbaru
            exog_all = combine_exog()
            df_merged = df_features.join(exog_all, how="left").ffill().bfill()
            
            # Ambil HANYA baris terakhir untuk Incremental Training
            latest_point = df_merged.iloc[[-1]]
            
            target = latest_point[['Close Price']]
            exog = latest_point[['Open_lag1', 'High_lag1', 'Low_lag1', 'Close_lag1', 'Return', 'HL_Spread', 'Inflasi', 'BI Rate']]
            
            print(f"📅 Data Tanggal: {latest_point.index[0].date()}")
            
            # STEP E: Incremental Retraining (Loop untuk Baseline & Tuned)
            modes_to_train = ["baseline", "tuned"]
            
            for mode in modes_to_train:
                print(f"\n   ⚙️ Memproses model mode: [{mode.upper()}]")
                manager = ModelManager(currency, mode=mode)
                
                if manager.load_all_models():
                    print(f"   -> Updating ARIMA {mode}...")
                    manager.arima.append_data(target, exog) 
                    
                    print(f"   -> Updating LSTM {mode} (1 Epoch)...")
                    manager.lstm.incremental_train(target, exog)
                    
                    print(f"   -> Updating Hybrid {mode}...")
                    manager.hybrid.incremental_train(target, exog)
                    
                    manager.save_all_models()
                    print(f"   ✅ Model {currency} ({mode}) Berhasil Diperbarui!")
                else:
                    print(f"   ⚠️ Model {currency} ({mode}) tidak ditemukan. Pastikan sudah di-train penuh sebelumnya.")

        except Exception as e:
            print(f"❌ Error training {currency}: {e}")

    print("\n🎉 Proses Daily Training Selesai!")

if __name__ == "__main__":
    run_daily_retraining()