# 📘 Panduan Lengkap: Gold House AI — XAUUSD Scalping Bot

> **Untuk siapa panduan ini?**
> Panduan ini ditulis untuk pemula yang belum pernah menyentuh kode Python sebelumnya.
> Ikuti langkah demi langkah, jangan dilewati.

---

## 📋 Daftar Isi

1. [Apa itu aplikasi ini?](#1-apa-itu-aplikasi-ini)
2. [Yang dibutuhkan sebelum mulai](#2-yang-dibutuhkan-sebelum-mulai)
3. [Instalasi MetaTrader 5](#3-instalasi-metatrader-5)
4. [Instalasi Python](#4-instalasi-python)
5. [Instalasi aplikasi Gold House AI](#5-instalasi-aplikasi-gold-house-ai)
6. [Mendapatkan API Key Kimi AI](#6-mendapatkan-api-key-kimi-ai)
7. [Konfigurasi file .env](#7-konfigurasi-file-env)
8. [Menjalankan aplikasi](#8-menjalankan-aplikasi)
9. [Memahami tampilan aplikasi](#9-memahami-tampilan-aplikasi)
10. [Pengaturan risiko](#10-pengaturan-risiko)
11. [Panduan pengembangan lanjutan](#11-panduan-pengembangan-lanjutan)
12. [Troubleshooting (Masalah umum)](#12-troubleshooting-masalah-umum)
13. [FAQ](#13-faq)

---

## 1. Apa itu aplikasi ini?

**Gold House AI** adalah robot trading otomatis untuk XAUUSD (emas/dolar) yang:

- 🤖 **Menggunakan AI** — Hermes Agent dari NousResearch menganalisis pasar
- 🧠 **Belajar sendiri** — Agent bisa membuat strategi baru dari pengalamannya
- 📊 **Terhubung ke MT5** — Eksekusi order langsung di MetaTrader 5 Anda
- 💰 **Compounding otomatis** — Lot size tumbuh seiring profit
- 🖥️ **Tampilan visual** — Desktop app dengan chart, log, dan posisi terbuka

```
Alur kerja bot:
MT5 (data harga) → Hermes AI (analisis) → MT5 (eksekusi order) → GUI (tampilan)
```

**Penting:** Selalu mulai dengan akun DEMO dulu. Jangan langsung live!

---

## 2. Yang dibutuhkan sebelum mulai

### Spesifikasi minimum PC:
| Komponen | Minimum | Rekomendasi |
|----------|---------|-------------|
| OS | Windows 10 64-bit | Windows 11 |
| RAM | 4 GB | 8 GB |
| Storage | 2 GB kosong | 5 GB |
| Internet | Stabil 1 Mbps | 10 Mbps |
| CPU | Intel Core i3 | Intel Core i5+ |

> ⚠️ **MetaTrader 5 Python hanya bisa di Windows.** Mac/Linux tidak bisa trading live (hanya bisa test tanpa MT5).

### Daftar yang harus disiapkan:
- [ ] PC Windows 10/11
- [ ] Akun broker MT5 (demo dulu)
- [ ] Email untuk daftar Kimi AI
- [ ] Koneksi internet stabil

---

## 3. Instalasi MetaTrader 5

### Langkah 1: Download MT5
1. Buka browser, pergi ke situs broker Anda
   - Rekomendasi broker untuk pemula: **ICMarkets**, **Pepperstone**, atau **XM**
   - Cari tombol "Download MT5" atau "Download Platform"
2. Download file installer MT5 (biasanya bernama `mt5setup.exe`)

### Langkah 2: Install MT5
1. Klik dua kali file `mt5setup.exe` yang sudah didownload
2. Klik **"Next"** → **"Next"** → **"Install"**
3. Tunggu sampai selesai, klik **"Finish"**

### Langkah 3: Buka akun demo
1. Buka MetaTrader 5 yang baru diinstall
2. Klik menu **"File"** → **"Open an Account"**
3. Pilih broker Anda dari daftar (ketik nama broker di kolom pencarian)
4. Pilih **"Open a demo account"**
5. Isi nama, email, pilih leverage **1:100**, deposit **10,000 USD**
6. Klik **"Next"** → catat **Login, Password, Server** yang diberikan
7. Klik **"Finish"**

### Langkah 4: Login ke MT5
1. Klik **"File"** → **"Login to Trade Account"**
2. Masukkan Login, Password, Server yang tadi dicatat
3. Pastikan ada tanda ✅ di pojok kanan bawah (artinya terhubung)

> 💡 **MT5 harus tetap terbuka dan login saat bot berjalan!**

---

## 4. Instalasi Python

### Langkah 1: Download Python
1. Buka browser, pergi ke: **https://www.python.org/downloads/**
2. Klik tombol besar **"Download Python 3.11.x"** (atau versi 3.11 terbaru)

### Langkah 2: Install Python
1. Klik dua kali file installer yang didownload
2. ⚠️ **PENTING:** Centang kotak **"Add Python to PATH"** di bagian bawah
3. Klik **"Install Now"**
4. Tunggu sampai selesai, klik **"Close"**

### Langkah 3: Verifikasi Python berhasil
1. Tekan tombol **Windows + R** di keyboard
2. Ketik `cmd` → tekan Enter
3. Di jendela hitam yang muncul, ketik:
   ```
   python --version
   ```
4. Harus muncul tulisan seperti: `Python 3.11.x`
   - Jika muncul error, ulangi instalasi Python dengan centang "Add to PATH"

---

## 5. Instalasi aplikasi Gold House AI

### Langkah 1: Extract file ZIP
1. Klik kanan file **`hermest-xauusd-scalping.zip`**
2. Pilih **"Extract All..."** atau **"Extract Here"**
3. Pilih lokasi yang mudah diingat, contoh: `C:\TradingBot\`
4. Klik **"Extract"**
5. Hasilnya ada folder bernama `hermest-xauusd-scalping`

### Langkah 2: Buka Command Prompt di folder bot
1. Buka folder `hermest-xauusd-scalping` di File Explorer
2. Klik pada address bar (bagian atas yang menampilkan path folder)
3. Ketik `cmd` → tekan Enter
4. Jendela Command Prompt terbuka di folder yang benar

> Cara alternatif: Tekan **Shift + klik kanan** di dalam folder → pilih **"Open PowerShell window here"**

### Langkah 3: Install semua library yang dibutuhkan

Ketik perintah-perintah berikut satu per satu (tekan Enter setelah tiap baris):

```
pip install MetaTrader5
```
Tunggu sampai selesai (1-2 menit)...

```
pip install PyQt5
```
Tunggu sampai selesai...

```
pip install pyqtgraph
```
Tunggu...

```
pip install pandas numpy python-dotenv pyyaml openai
```
Tunggu...

```
pip install git+https://github.com/NousResearch/hermes-agent.git
```
Ini paling lama (2-5 menit), tunggu sampai muncul `Successfully installed`

> 💡 Jika muncul error "pip is not recognized": Python belum ditambahkan ke PATH. Reinstall Python dengan centang "Add to PATH"

> 💡 Jika muncul error saat install hermes-agent: Pastikan komputer terhubung internet dan tidak ada firewall yang memblokir GitHub

### Langkah 4: Verifikasi instalasi
Ketik perintah ini untuk memastikan semua terpasang:
```
python -c "import MetaTrader5, PyQt5, pyqtgraph, pandas, openai; print('Semua library OK!')"
```
Harus muncul: `Semua library OK!`

---

## 6. Mendapatkan API Key Kimi AI

Kimi AI adalah "otak" yang menganalisis pasar. Anda butuh API key untuk menggunakannya.

### Langkah 1: Daftar akun Kimi AI
1. Buka browser, pergi ke: **https://platform.moonshot.cn**
2. Klik **"注册"** (Register/Daftar)
3. Masukkan email Anda
4. Verifikasi email (cek inbox, klik link verifikasi)
5. Buat password

### Langkah 2: Isi saldo (top up)
1. Login ke platform.moonshot.cn
2. Klik menu **"充值"** (Top Up/Isi Saldo)
3. Isi minimal 10 CNY (~Rp 20.000) — sudah cukup untuk ratusan analisis
4. Bayar via kartu kredit atau metode yang tersedia

> 💰 **Estimasi biaya:** Setiap analisis ~800 token. Dengan model `moonshot-v1-32k`, biaya ~$0.0001 per analisis. Saldo $5 = ribuan analisis.

### Langkah 3: Buat API Key
1. Klik menu **"API Key"** di sidebar kiri
2. Klik tombol **"新建 API Key"** (Create New API Key)
3. Beri nama (contoh: "GoldHouseAI")
4. Klik **"确认"** (Confirm)
5. **COPY** API key yang muncul — hanya muncul sekali!
   - Bentuknya seperti: `sk-xxxxxxxxxxxxxxxxxxxxx`
6. Simpan di tempat aman (Notepad, dll.)

---

## 7. Konfigurasi file .env

File `.env` adalah file konfigurasi berisi password dan API key. **Jangan dibagikan ke siapapun!**

### Langkah 1: Buat file .env
1. Di folder `hermest-xauusd-scalping`, cari file `.env.example`
2. Klik kanan → **"Copy"**
3. Klik kanan di area kosong folder → **"Paste"**
4. Rename file copy tersebut menjadi `.env` (hapus `.example`)
   - Jika Windows bertanya "Are you sure?", klik **"Yes"**

> 💡 Jika tidak bisa rename: Buka File Explorer → View → centang "File name extensions"

### Langkah 2: Edit file .env
1. Klik kanan file `.env` → **"Open with"** → **"Notepad"**
2. Edit isinya sesuai data Anda:

```
# Kimi AI
KIMI_API_KEY=sk-paste-api-key-anda-disini
HERMES_MODEL=moonshot-v1-32k

# MetaTrader 5 (dari langkah 3 instalasi MT5)
MT5_LOGIN=12345678
MT5_PASSWORD=password_mt5_anda
MT5_SERVER=NamaBroker-Demo

# Pengaturan Risiko (untuk demo, biarkan default dulu)
RISK_PCT_PER_TRADE=1.0
MAX_DAILY_LOSS_PCT=3.0
MAX_CONCURRENT_POSITIONS=2
ATR_PERIOD=14
ATR_SL_MULTIPLIER=1.5
RR_RATIO=2.0
COMPOUND_PROFIT=true

# Bot
LOOP_INTERVAL_SECONDS=10
SYMBOL=XAUUSD
```

3. Ganti nilai sesuai data nyata Anda:
   - `KIMI_API_KEY` → API key dari Kimi AI
   - `MT5_LOGIN` → Nomor login MT5 Anda
   - `MT5_PASSWORD` → Password MT5 Anda
   - `MT5_SERVER` → Server broker (cek di MT5: File → Login, lihat nama server)

4. Tekan **Ctrl+S** untuk menyimpan
5. Tutup Notepad

### Contoh isi .env yang sudah diisi:
```
KIMI_API_KEY=sk-abc123def456ghi789
HERMES_MODEL=moonshot-v1-32k
MT5_LOGIN=88012345
MT5_PASSWORD=TradingBot2024!
MT5_SERVER=ICMarkets-Demo01
RISK_PCT_PER_TRADE=1.0
MAX_DAILY_LOSS_PCT=3.0
MAX_CONCURRENT_POSITIONS=2
ATR_PERIOD=14
ATR_SL_MULTIPLIER=1.5
RR_RATIO=2.0
COMPOUND_PROFIT=true
LOOP_INTERVAL_SECONDS=10
SYMBOL=XAUUSD
```

---

## 8. Menjalankan aplikasi

### Setiap kali ingin menjalankan bot, lakukan urutan ini:

**Urutan wajib:**
1. ✅ Nyalakan PC dan pastikan internet aktif
2. ✅ Buka **MetaTrader 5** dan pastikan sudah login (ada ✅ di pojok kanan bawah MT5)
3. ✅ Buka Command Prompt di folder `hermest-xauusd-scalping`
4. ✅ Ketik perintah:

```
python main.py
```

Tekan Enter. Tunggu 5-10 detik, jendela aplikasi akan terbuka.

### Mode test (tanpa MT5, untuk coba-coba):
```
python main.py --dry-run
```
Ini menggunakan data palsu — tidak ada trading nyata, berguna untuk belajar tampilan app.

### Jika ada error saat menjalankan:
- Pastikan MT5 sudah dibuka dan login terlebih dahulu
- Pastikan file `.env` sudah diisi dengan benar
- Pastikan semua library sudah terinstall (langkah 5.3)

---

## 9. Memahami tampilan aplikasi

```
┌─────────────────────────────────────────────────────────────────┐
│  🏆 Gold House AI — XAUUSD Scalping Desk                        │
├──────────┬───────────────────────────────────┬──────────────────┤
│  ACCOUNT │         CHART XAUUSD (M5)         │   LIVE PRICE     │
│          │    (grafik candlestick real-time)  │                  │
│ Balance  │                                    │  BID: 3,245.12  │
│ Equity   │                                    │  ASK: 3,245.35  │
│ Day P&L  │                                    │  Spread: 23 pts │
│ Compound │                                    │  ATR: 4.52      │
│          │                                    │  RSI: 58.3      │
├──────────┴───────────────────────────────────┴──────────────────┤
│                    OPEN POSITIONS                                │
│  Ticket | Type | Lots | Open | SL | TP | Current | P&L         │
├────────────────────────────────┬────────────────────────────────┤
│  HERMES AGENT LOG              │  RISK CONFIG   │ SKILL MANAGER │
│  [log aktivitas AI]            │  [pengaturan]  │  [skill list] │
├────────────────────────────────┴────────────────────────────────┤
│  [▶ START BOT]  [■ STOP]  [✕ Close All]    Chart: [M5 ▼]       │
└─────────────────────────────────────────────────────────────────┘
```

### Penjelasan tiap bagian:

#### 📊 ACCOUNT (kiri atas)
- **Balance** — Modal total akun Anda
- **Equity** — Balance + floating profit/loss posisi terbuka
- **Day P&L** — Profit/loss hari ini (hijau = profit, merah = rugi)
- **Compound** — Faktor pengali lot (1.0× = normal, 1.5× = sudah naik karena profit)

#### 📈 CHART (tengah atas)
- Grafik candlestick XAUUSD real-time
- Garis oranye = EMA 20 (indikator trend)
- Candle hijau = harga naik, candle merah = harga turun
- Update otomatis setiap kali bot berjalan

#### 💱 LIVE PRICE (kanan atas)
- **BID** = harga jual (merah)
- **ASK** = harga beli (hijau)
- **Spread** = selisih bid-ask (semakin kecil semakin bagus)
- **ATR** = Average True Range, ukuran volatilitas
- **RSI** = Relative Strength Index (>65 = overbought, <35 = oversold)

#### 📋 OPEN POSITIONS (tengah)
Daftar semua posisi terbuka saat ini:
- **Ticket** = nomor ID order
- **Type** = BUY atau SELL
- **Lots** = ukuran lot
- **Open** = harga buka posisi
- **SL** = Stop Loss (batas rugi)
- **TP** = Take Profit (target profit)
- **P&L** = Profit/Loss saat ini (hijau = untung, merah = rugi)

#### 🤖 HERMES AGENT LOG (bawah kiri)
Log real-time keputusan Hermes AI:
- Setiap 10 detik, AI menganalisis pasar
- Warna **hijau** = ACTION: BUY
- Warna **merah** = ACTION: SELL
- Warna **kuning** = ACTION: HOLD (tunggu)
- Warna **ungu** = ACTION: CLOSE_ALL

Contoh log:
```
[14:32:15] ACTION: BUY (conf: 0.82)
RSI oversold at 28.5, price bouncing from EMA support.
London session breakout confirmed. Signal score: 8/10.
```

#### ⚙️ RISK CONFIG (bawah tengah)
Pengaturan risiko yang bisa diubah tanpa restart bot:
- **Risk/Trade** = % modal yang dirisiko per trade
- **Max Daily Loss** = % loss maksimal per hari
- **Max Positions** = maksimal posisi terbuka bersamaan
- Klik **"Apply Settings"** setelah mengubah

#### 📚 SKILL MANAGER (bawah kanan)
Daftar skill/strategi yang dimiliki Hermes Agent:
- 5 skill bawaan (technical_analysis, risk_assessment, dll.)
- Skill baru yang dibuat otomatis oleh AI diberi tanda `*`
- Klik **"View"** untuk membaca isi skill

### Tombol kontrol (bawah layar):
| Tombol | Fungsi |
|--------|--------|
| ▶ START BOT | Mulai bot, AI mulai analisis dan trading |
| ■ STOP | Hentikan bot (posisi terbuka TIDAK otomatis ditutup) |
| ✕ Close All | Tutup SEMUA posisi terbuka sekarang |
| Chart M5 ▼ | Ganti timeframe chart (M1/M5/M15/H1) |

---

## 10. Pengaturan risiko

### Untuk DEMO (belajar):
```
RISK_PCT_PER_TRADE=1.0       # 1% per trade
MAX_DAILY_LOSS_PCT=3.0       # stop jika rugi 3%/hari
MAX_CONCURRENT_POSITIONS=2   # max 2 posisi
```

### Untuk LIVE ACCOUNT (sangat konservatif):
```
RISK_PCT_PER_TRADE=0.1       # hanya 0.1% per trade
MAX_DAILY_LOSS_PCT=1.0       # stop jika rugi 1%/hari
MAX_CONCURRENT_POSITIONS=1   # max 1 posisi
```

### Memahami compounding:
- Saat profit harian ≥ 3%: lot naik 10% hari berikutnya
- Saat rugi ≥ 2%: lot turun 20% untuk proteksi
- Compound factor maksimal 2.0× (tidak lebih dari 2× lot normal)

### Kapan bot berhenti otomatis:
1. Daily loss limit tercapai (contoh: rugi 3% dari balance)
2. Max positions tercapai (2 posisi sudah terbuka)
3. Spread terlalu lebar (>30 poin)
4. ATR terlalu kecil (pasar terlalu sepi)

---

## 11. Panduan pengembangan lanjutan

### A. Mengedit skill Hermes Agent

Skill adalah file `.md` di folder `agent/skills/`. Anda bisa edit dengan Notepad.

**Cara edit skill:**
1. Buka folder `hermest-xauusd-scalping/agent/skills/`
2. Klik kanan file skill → Open with Notepad
3. Edit sesuai kebutuhan
4. Simpan (Ctrl+S)
5. Restart bot untuk skill baru aktif

**Contoh tambah aturan baru di `technical_analysis.md`:**
```markdown
## Aturan tambahan saya:
- Jangan BUY jika harga di bawah MA 200 di H4
- Jangan SELL jika RSI di bawah 50 di H1
```

### B. Membuat skill baru manual

Buat file baru di `agent/skills/`, contoh `my_strategy.md`:
```markdown
# Skill: My Custom Strategy

## Kapan BUY:
- Harga breakout di atas resistance Asia
- RSI di bawah 45
- Spread di bawah 20 poin

## Kapan SELL:
- Harga breakout di bawah support Asia
- RSI di atas 55
- Spread di bawah 20 poin
```

Hermes Agent akan otomatis membaca skill baru ini saat restart.

### C. Mengubah model AI

Di file `.env`, ganti `HERMES_MODEL`:

| Model | Kecepatan | Biaya | Kemampuan |
|-------|-----------|-------|-----------|
| `moonshot-v1-8k` | Tercepat | Termurah | Cukup |
| `moonshot-v1-32k` | Sedang | Sedang | **Rekomendasi** |
| `moonshot-v1-128k` | Lambat | Termahal | Terbaik |

### D. Mengubah interval analisis

Di `.env`, ubah `LOOP_INTERVAL_SECONDS`:
- `5` = analisis tiap 5 detik (lebih aktif, lebih banyak token)
- `10` = analisis tiap 10 detik (default, seimbang)
- `30` = analisis tiap 30 detik (hemat token, lebih lambat)

### E. Menambah simbol trading lain

Secara default bot hanya trading XAUUSD. Untuk menambah simbol:
1. Buka file `config/trading_params.py`
2. Ubah `SYMBOL = "XAUUSD"` menjadi simbol yang diinginkan
3. Atau di `.env`, tambah `SYMBOL=EURUSD`

> ⚠️ Strategi dan skill saat ini dioptimalkan untuk XAUUSD. Untuk simbol lain, buat skill baru yang sesuai.

### F. Melihat log lengkap

Log tersimpan di folder `logs/gold_house_ai.log`. Buka dengan Notepad untuk melihat riwayat lengkap aktivitas bot.

### G. Menjalankan tests

Untuk memastikan semua kode berjalan benar:
```
python -m pytest tests/ -v
```
Harus muncul `19 passed` tanpa error.

### H. Struktur folder untuk referensi

```
hermest-xauusd-scalping/
│
├── main.py              ← ENTRY POINT: jalankan ini untuk start app
├── .env                 ← KONFIGURASI: isi API key dan MT5 di sini
├── requirements.txt     ← Daftar library yang dibutuhkan
│
├── agent/
│   ├── hermes_agent.py  ← Otak AI: Hermes Agent + Kimi AI
│   ├── skills/          ← Folder skill AI (bisa diedit bebas)
│   │   ├── technical_analysis.md   ← Cara analisis teknikal
│   │   ├── risk_assessment.md      ← Cara evaluasi risiko
│   │   ├── trade_execution.md      ← SOP eksekusi trade
│   │   ├── profit_compounding.md   ← Strategi compound
│   │   └── market_session.md       ← Jadwal sesi trading
│   └── mt5_tools_plugin/  ← Tools MT5 untuk Hermes Agent
│
├── connectors/
│   └── mt5_connector.py  ← Koneksi ke MetaTrader 5
│
├── config/
│   ├── settings.py       ← Baca file .env
│   └── trading_params.py ← Konstanta (simbol, timeframe, dll.)
│
├── risk/
│   └── risk_manager.py   ← Kalkulasi lot, SL, TP, compounding
│
├── core/
│   └── bot.py            ← Loop utama trading
│
├── gui/
│   ├── main_window.py    ← Jendela utama aplikasi
│   └── widgets/          ← Komponen tampilan (chart, log, dll.)
│
├── utils/
│   ├── indicators.py      ← Kalkulasi ATR, EMA, RSI
│   └── token_optimizer.py ← Hemat token Kimi AI
│
└── tests/                 ← Kode pengujian
```

---

## 12. Troubleshooting (Masalah umum)

### ❌ "ModuleNotFoundError: No module named 'MetaTrader5'"
**Solusi:** Install ulang MetaTrader5
```
pip install MetaTrader5
```

### ❌ "MT5 init failed" atau tidak bisa connect ke MT5
**Solusi:**
1. Pastikan MetaTrader 5 sudah dibuka dan login
2. Cek Login, Password, Server di file `.env` sudah benar
3. Cek koneksi internet
4. Coba jalankan MT5 sebagai Administrator (klik kanan → Run as Administrator)

### ❌ "KIMI_API_KEY not found" atau error API
**Solusi:**
1. Pastikan file `.env` ada di folder yang sama dengan `main.py`
2. Pastikan API key di `.env` sudah diisi (bukan contoh/placeholder)
3. Cek saldo Kimi AI masih ada di platform.moonshot.cn

### ❌ Aplikasi buka tapi chart kosong / tidak update
**Solusi:**
1. Klik tombol **▶ START BOT** (chart hanya update saat bot berjalan)
2. Pastikan MT5 sudah login dan XAUUSD tersedia di Market Watch

### ❌ Bot berjalan tapi tidak ada order
**Solusi ini normal jika:**
- AI menilai kondisi pasar HOLD (tidak ada sinyal)
- Risk limits aktif (spread terlalu lebar, atau sudah max positions)
- Di luar jam trading optimal (Asia session = sedikit sinyal)

**Cek di Agent Log** untuk melihat alasan AI tidak trading.

### ❌ "pip is not recognized as an internal or external command"
**Solusi:** Python belum ditambahkan ke PATH
1. Uninstall Python dari Control Panel
2. Install ulang Python, centang **"Add Python to PATH"** di awal instalasi

### ❌ Error saat install hermes-agent dari GitHub
**Solusi:**
1. Pastikan ada koneksi internet
2. Pastikan Git terinstall: download dari https://git-scm.com/download/win
3. Coba lagi: `pip install git+https://github.com/NousResearch/hermes-agent.git`

### ❌ Aplikasi crash / menutup sendiri
**Solusi:**
1. Buka file `logs/gold_house_ai.log` dengan Notepad
2. Cari baris terakhir dengan kata "ERROR"
3. Screenshot error tersebut untuk dicari solusinya

---

## 13. FAQ

**Q: Apakah bot ini menjamin profit?**
A: Tidak ada jaminan profit. Bot adalah alat bantu analisis — bukan mesin uang. Selalu ada risiko kehilangan modal.

**Q: Berapa lama harus di demo sebelum live?**
A: Minimal 1-2 bulan di demo dengan hasil konsisten. Perhatikan winrate (>55%) dan drawdown maksimal (<10%).

**Q: Apakah bisa ditinggal berjalan sendiri?**
A: Bisa, tapi tidak direkomendasikan untuk pemula. Selalu monitor minimal sekali beberapa jam. Bot bisa dimatikan manual kapan saja.

**Q: Berapa biaya API Kimi AI per bulan?**
A: Dengan interval 10 detik, bot membuat ~8.640 request/hari. Biaya estimasi ~$0.50-2.00/hari tergantung panjang respons.

**Q: Bisa pakai AI lain selain Kimi AI?**
A: Ya. Di `.env` ganti `KIMI_BASE_URL` dan `KIMI_API_KEY` dengan provider lain:
- OpenAI: `base_url=https://api.openai.com/v1`
- Groq: `base_url=https://api.groq.com/openai/v1`

**Q: Bagaimana cara update aplikasi jika ada versi baru?**
A: Download ZIP terbaru, extract, copy file `.env` lama ke folder baru.

**Q: Bot tidak bisa lihat berita forex — apakah berbahaya?**
A: Ya, ini risiko. Bot tidak tahu jadwal news. **Matikan bot secara manual** 30 menit sebelum dan sesudah news berdampak tinggi (NFP, CPI, Fed rate). Cek kalender ekonomi di forexfactory.com.

**Q: Skill yang dibuat AI apakah bisa dihapus?**
A: Ya. Buka folder `agent/skills/`, hapus file `.md` yang tidak diinginkan. Skill bawaan (5 file pertama) sebaiknya jangan dihapus.

**Q: Apakah bisa dijalankan di VPS?**
A: Bisa, tapi hanya VPS Windows (bukan Linux) karena keterbatasan library MT5. Cari "Windows VPS trading" di Google.

---

## 📞 Bantuan Lebih Lanjut

Jika ada masalah yang tidak tercakup di panduan ini:
1. Screenshot error yang muncul
2. Buka file `logs/gold_house_ai.log` dan copy beberapa baris terakhir
3. Cari solusi di Google dengan keyword error tersebut

---

> **⚠️ Disclaimer:** Aplikasi ini dibuat untuk tujuan edukasi. Trading forex dan emas mengandung risiko tinggi. Jangan pernah trading dengan uang yang tidak siap Anda kehilangan. Performa masa lalu tidak menjamin hasil di masa depan.

---

*Gold House AI — Powered by Hermes Agent (NousResearch) + Kimi AI (Moonshot)*
