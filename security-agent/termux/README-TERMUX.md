# Panduan Lengkap — Termux (Android)

## Prasyarat

- **Termux** dari F-Droid: https://f-droid.org/packages/com.termux/
  *(JANGAN dari Play Store — versi lama & tidak diupdate)*
- **API Key Anthropic**: https://console.anthropic.com
- Koneksi internet aktif

---

## Instalasi (Satu Kali)

### Langkah 1 — Buka Termux dan copy project

```bash
# Opsi A: Clone dari GitHub (jika sudah di repo)
pkg install git -y
git clone https://github.com/USER/REPO ~/superpowers
cd ~/superpowers/security-agent

# Opsi B: Extract ZIP yang sudah didownload
pkg install unzip -y
cp /sdcard/Download/agentic-ai-security-v3.zip ~/
cd ~
unzip agentic-ai-security-v3.zip
cd security-agent
```

### Langkah 2 — Jalankan setup otomatis

```bash
bash termux/setup.sh
```

Script ini akan:
- Install Python, pip, dan library sistem yang diperlukan
- Install semua Python package
- Membuat file `.env` dari template
- Membuat direktori `~/security-reports/`

### Langkah 3 — Isi API Key

```bash
nano .env
```

Ganti baris ini:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```
Dengan API key Anda dari https://console.anthropic.com

Tekan `Ctrl+X` → `Y` → `Enter` untuk menyimpan.

---

## Cara Penggunaan di Termux

### Scan Website (URL)

```bash
python cli.py scan --url https://target.com
python cli.py scan --url https://target.com --profile full
```

### Scan File Kode

```bash
# Scan file dari storage internal Android
python cli.py scan --file /sdcard/Download/login.php

# Scan file di direktori saat ini
python cli.py scan --file app.py --profile full
```

Format file yang didukung: `.php` `.py` `.js` `.ts` `.java` `.go` `.rb` `.html` `.sql` `.json` `.yaml`

### Analisis Log Website

```bash
# Dari file log
python cli.py monitor --file /sdcard/Download/access.log

# Dari stdin (paste langsung)
python cli.py monitor
# Paste log, lalu tekan Ctrl+D
```

### Penetration Testing

```bash
python cli.py pentest --url https://target.com
python cli.py pentest --url https://target.com --scope "https://target.com/*"
```

> **Penting:** Hanya gunakan pada sistem yang Anda miliki atau yang sudah memberikan izin.

### Deep Scan (Multi-ronde sampai CRITICAL ditemukan)

```bash
# Scan website hingga CRITICAL ditemukan (maks 5 ronde)
python cli.py deepscan --url https://target.com

# Scan file, 3 ronde, lanjutkan walau sudah ketemu CRITICAL
python cli.py deepscan --file app.php --rounds 3 --no-stop

# Scan website, 2 ronde saja (hemat kuota)
python cli.py deepscan --url https://target.com --rounds 2
```

### Adaptive Scan (Agent Buat Tools Sendiri)

```bash
# Mode paling menyeluruh — agent menulis tools & strategi sendiri
python cli.py adaptive --url https://target.com

# Dengan rounds terbatas untuk hemat kuota
python cli.py adaptive --url https://target.com --rounds 2
```

### Full Audit (Semua Fitur Sekaligus)

```bash
python cli.py audit \
  --url https://target.com \
  --file /sdcard/Download/app.php \
  --log /sdcard/Download/access.log
```

### Jalankan REST API Server

```bash
python cli.py server
```

Akses dari browser HP: `http://localhost:8000/docs`

---

## Tips Penggunaan di Android

### Hemat Baterai & Kuota

Gunakan mode yang lebih ringan untuk target sederhana:

```bash
# Cepat, 1 ronde saja
python cli.py scan --url https://target.com --profile quick

# Deep scan 2 ronde saja
python cli.py deepscan --url https://target.com --rounds 2
```

### Akses File dari Storage Android

Aktifkan akses storage di Termux:
```bash
termux-setup-storage
```

Kemudian file bisa diakses dari:
- `/sdcard/Download/` — folder Download
- `/sdcard/Documents/` — folder Documents
- `~/storage/shared/` — seluruh internal storage

```bash
# Scan file dari folder Download
python cli.py scan --file ~/storage/downloads/login.php
```

### Jalankan di Background

```bash
# Jalankan dan simpan output ke file
nohup python cli.py adaptive --url https://target.com > ~/security-reports/output.txt 2>&1 &
echo "Job ID: $!"

# Lihat output
tail -f ~/security-reports/output.txt
```

### Simpan API Key Permanen

Agar tidak perlu isi API key berulang:
```bash
echo 'export ANTHROPIC_API_KEY=sk-ant-xxxxxxxxx' >> ~/.bashrc
source ~/.bashrc
```

---

## Lihat Hasil Laporan

Semua laporan disimpan otomatis di `~/security-reports/`:

```bash
# Lihat daftar laporan
ls ~/security-reports/

# Baca laporan terbaru (format teks)
cat ~/security-reports/$(ls -t ~/security-reports/*.md | head -1)

# Baca laporan JSON
cat ~/security-reports/$(ls -t ~/security-reports/*.json | head -1) | python -m json.tool | head -100

# Kirim laporan ke email/WhatsApp (via Termux:API)
pkg install termux-api -y
termux-share ~/security-reports/laporan.md
```

---

## Troubleshooting

| Masalah | Solusi |
|---|---|
| `ModuleNotFoundError: anthropic` | Jalankan `pip install -r requirements-termux.txt` |
| `ANTHROPIC_API_KEY tidak ditemukan` | Edit `.env` dan isi API key, atau gunakan `python cli.py --key sk-ant-xxx scan ...` |
| `pip install` gagal kompilasi | Jalankan `pkg install clang libffi openssl -y` lalu coba lagi |
| Port 8000 sudah digunakan | `pkill -f uvicorn` atau ganti port: `uvicorn main:app --port 8080` |
| Scan lambat di HP | Gunakan `--rounds 1` atau `--profile quick` |
| Storage tidak terdeteksi | Jalankan `termux-setup-storage` dan izinkan akses |
| `SSL: CERTIFICATE_VERIFY_FAILED` | Normal — `httpx` di scanner sudah diset `verify=False` |

---

## Contoh Sesi Lengkap

```bash
# Buka Termux
cd ~/security-agent

# Scan cepat website
python cli.py scan --url https://testphp.vulnweb.com --profile full

# Hasil muncul di terminal + disimpan di ~/security-reports/
# Contoh output:
# ✓ Scanning https://testphp.vulnweb.com ...
# ──────────────────────────────────────────────────
# HASIL SCAN: https://testphp.vulnweb.com
# Risk Score  : 9.2/10
# Findings    : 3 CRITICAL  2 HIGH  4 MEDIUM  1 LOW
#
# ── Temuan Kerentanan ──
# [1] CRITICAL  SQL Injection di /artists.php?artist parameter
#     OWASP: A03:2021  CVSS: 9.8
#     Evidence: artist=1' error: mysql_fetch_array()
#     Fix: Gunakan prepared statements
```
