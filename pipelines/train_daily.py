import sys
import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

# Mengamankan path import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.data_loader import fetch_forex_alpha
from utils.features import create_price_features
from models.model_manager import ModelManager

import warnings 
warnings.filterwarnings("ignore")

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

def append_forex_csv(base_curr, df_raw):
    # Pemetaan file sesuai dengan data_loader.py
    file_map = {"USD": "data/usd_idr.csv", "EUR": "data/eur_idr.csv", "GBP": "data/gbp_idr.csv"}
    file_path = file_map.get(base_curr)
    
    if not file_path or not os.path.exists(file_path):
        print(f"⚠️ File {file_path} tidak ditemukan, skip append CSV.")
        return

    # Ambil baris data paling terakhir (terbaru) dari hasil tarikan API
    latest_date = df_raw.index[-1].strftime('%Y-%m-%d')
    close_p = df_raw['Close Price'].iloc[-1]
    open_p = df_raw['Open'].iloc[-1]
    high_p = df_raw['High'].iloc[-1]
    low_p = df_raw['Low'].iloc[-1]
    
    # Buka CSV untuk membaca baris paling bawah
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    last_line = lines[-1]
    last_date_csv = last_line.split(',')[0].strip()
    
    # Validasi: Masukkan hanya jika tanggal terbaru belum ada di ujung CSV
    if latest_date not in last_date_csv:
        # Pengecekan agar data baru tidak menempel di baris yang sama jika tidak ada enter
        prefix = "" if last_line.endswith('\n') else "\n"
        
        # Susunan wajib sama dengan CSV lama: Date, Close Price, Open, High, Low
        new_line = f"{prefix}{latest_date},{close_p},{open_p},{high_p},{low_p}\n"
        
        # Mode 'a' (append) untuk men   empelkan di akhir file
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(new_line)
        print(f"📁 [CSV UPDATE] Data baru '{latest_date}' berhasil di-append ke ujung {file_path}!")
    else:
        print(f"📁 [CSV UPDATE] Data '{latest_date}' sudah ada di ujung {file_path}. Skip append.")

def run_daily_retraining(currency_list=["USD/IDR", "EUR/IDR", "GBP/IDR"]):
    print(f"🚀 Memulai Daily Retraining Pipeline: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("📥 Melakukan Web Scraping BI Rate terbaru...")
    latest_bi_date, latest_bi = get_latest_bi_rate()
    print(f"✅ Berhasil! BI Rate saat ini: {latest_bi}%")
    update_data_csv("data/BI-7Day-RR.csv", latest_bi_date, latest_bi, is_inflasi=False)
    
    print("📥 Melakukan Web Scraping Inflasi terbaru...")
    latest_inf_date, latest_inf = get_latest_inflation()
    print(f"✅ Berhasil! Inflasi saat ini: {latest_inf}%")
    update_data_csv("data/Data Inflasi.csv", latest_inf_date, latest_inf, is_inflasi=True)
    
    for currency in currency_list:
        print(f"\n🔄 Memperbarui model untuk {currency}...")
        
        base_curr = currency.split('/')[0]
        
        try:
            #Tarik Data Historis Forex dari API 
            df_raw = fetch_forex_alpha(base_curr, "IDR")
            
            #Update CSV data forex
            append_forex_csv(base_curr, df_raw)

            #Hitung fitur (Lag, Return, Spread) menggunakan keseluruhan data
            df_features = create_price_features(df_raw)
            
            #Ambil HANYA baris terakhir (data hari ini/kemarin)
            latest_data_point = df_features.iloc[[-1]].copy()
            
            #Tempelkan data makroekonomi hasil scraping
            latest_data_point['BI Rate'] = latest_bi
            latest_data_point['Inflasi'] = latest_inf
            
            #Pisahkan jadi format Target & Exog
            latest_target = latest_data_point[['Close Price']]
            latest_exog = latest_data_point[['Open_lag1', 'High_lag1', 'Low_lag1', 'Close_lag1', 'Return', 'HL_Spread', 'Inflasi', 'BI Rate']]
            
            print(f"📅 Memasukkan data tanggal: {latest_data_point.index[0].strftime('%Y-%m-%d')}")
            
            # ======================================================
            # FITUR INSPEKSI DATA (Melihat data sebelum masuk model)
            # ======================================================
            print("\n🔍 [INSPEKSI DATA] Data yang akan masuk ke model:")
            print("▶️ TARGET (Y) - Harga Close yang akan dipelajari:")
            print(latest_target.to_string())
            print("\n▶️ FITUR EKSOGEN (X) - Variabel pendukung:")
            print(latest_exog.to_string())
            print("========================================================\n")
            
            manager = ModelManager(currency, mode="tuned")
            if not manager.load_all_models():
                print(f"⚠️ Model untuk {currency} belum ada. Lewati update harian.")
                continue
                
            # 7. Incremental Training 
            print("-> Updating ARIMA...")
            manager.arima.append_data(latest_target, latest_exog) 
            
            print("-> Updating LSTM (1 Epoch)...")
            manager.lstm.incremental_train(latest_target, latest_exog)
            
            print("-> Updating Hybrid Model...")
            manager.hybrid.incremental_train(latest_target, latest_exog)
            
            manager.save_all_models()
            print(f"✅ Model {currency} berhasil diperbarui dan disimpan!")
            
        except Exception as e:
            print(f"❌ Gagal memperbarui {currency}: {e}")
            
    print("\n🎉 Proses Daily Training Selesai!")

if __name__ == "__main__":
    run_daily_retraining()