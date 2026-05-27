# Agentic AI Security Service

Layanan keamanan berbasis AI multi-agent menggunakan Claude AI (Anthropic). Mendukung scanning kode, analisis log, penetration testing, dan pembuatan laporan keamanan otomatis.

---

## Fitur Utama

| Fitur | Endpoint | Deskripsi |
|---|---|---|
| Vulnerability Scanner | `POST /api/v1/scan` | Scan kode/URL untuk OWASP Top 10 |
| Log Monitor | `POST /api/v1/monitor` | Deteksi serangan dari log Apache/Nginx |
| Penetration Test | `POST /api/v1/pentest` | Uji keamanan aktif terhadap URL |
| Full Audit | `POST /api/v1/audit` | Semua fitur sekaligus + laporan lengkap |

---

## Prasyarat

- Python 3.11+
- API Key dari Anthropic: https://console.anthropic.com
- Koneksi internet (untuk akses Claude API)

---

## Instalasi

### 1. Ekstrak file ZIP

```bash
unzip agentic-ai-security.zip
cd security-agent
```

### 2. (Opsional) Buat virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Konfigurasi

Salin file konfigurasi contoh:

```bash
cp .env.example .env
```

Edit file `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx   # Wajib: API key dari Anthropic
SERVICE_API_KEY=ganti-dengan-password-kuat  # Wajib: Password untuk memanggil API ini
MODEL=claude-opus-4-7                        # Model AI yang digunakan
MAX_TOKENS=8192                              # Maksimum token per respons
RATE_LIMIT_PER_MINUTE=60                     # Batas request per menit
ENVIRONMENT=development                      # development / production
```

### 5. Jalankan service

```bash
python main.py
```

Service berjalan di: **http://localhost:8000**

Dokumentasi API interaktif: **http://localhost:8000/docs**

---

## Cara Penggunaan

### Autentikasi

Setiap request (kecuali `/api/v1/health`) wajib menyertakan header:

```
X-API-Key: <nilai SERVICE_API_KEY di file .env>
```

---

### 1. Scan Kode Aplikasi (Input Langsung)

Cocok untuk: analisis cepat potongan kode yang dicurigai.

```bash
curl -X POST http://localhost:8000/api/v1/scan \
  -H "X-API-Key: ganti-dengan-password-kuat" \
  -H "Content-Type: application/json" \
  -d '{
    "target_type": "code",
    "target_content": "<?php $id = $_GET[\"id\"]; $q = \"SELECT * FROM users WHERE id=$id\"; ?>",
    "filename": "login.php",
    "scan_profile": "full"
  }'
```

**scan_profile:** `quick` | `standard` | `full`

---

### 2. Scan File Aplikasi (Upload File)

Cocok untuk: upload langsung file PHP, Python, JS, Java, dll.

```bash
curl -X POST http://localhost:8000/api/v1/scan/upload \
  -H "X-API-Key: ganti-dengan-password-kuat" \
  -F "file=@/path/ke/file/login.php" \
  -F "scan_profile=full"
```

**Format file yang didukung:** `.py` `.php` `.js` `.ts` `.java` `.go` `.rb` `.cs` `.cpp` `.c` `.html` `.sql` `.yaml` `.json` `.conf` `.xml`

---

### 3. Scan Website via URL

Cocok untuk: analisis keamanan website pelanggan dari URL.

```bash
curl -X POST http://localhost:8000/api/v1/scan \
  -H "X-API-Key: ganti-dengan-password-kuat" \
  -H "Content-Type: application/json" \
  -d '{
    "target_type": "url",
    "target_url": "https://website-pelanggan.com",
    "scan_profile": "standard"
  }'
```

---

### 4. Analisis Log Website

Cocok untuk: deteksi serangan aktif dari log Apache/Nginx.

**Dari teks langsung:**
```bash
curl -X POST http://localhost:8000/api/v1/monitor \
  -H "X-API-Key: ganti-dengan-password-kuat" \
  -H "Content-Type: application/json" \
  -d '{
    "log_content": "192.168.1.1 - - [27/May/2026] \"GET /login?id=1+OR+1=1 HTTP/1.1\" 200 1234",
    "log_format": "apache"
  }'
```

**Upload file log:**
```bash
curl -X POST http://localhost:8000/api/v1/monitor/upload \
  -H "X-API-Key: ganti-dengan-password-kuat" \
  -F "logfile=@/var/log/nginx/access.log" \
  -F "log_format=nginx"
```

**log_format:** `apache` | `nginx` | `json` | `auto` (deteksi otomatis)

---

### 5. Penetration Testing

Cocok untuk: uji keamanan aktif terhadap website pelanggan (wajib ada izin tertulis).

```bash
curl -X POST http://localhost:8000/api/v1/pentest \
  -H "X-API-Key: ganti-dengan-password-kuat" \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "https://website-pelanggan.com",
    "scope": ["https://website-pelanggan.com/*"],
    "allowed_techniques": ["headers", "xss_probe", "sqli_probe", "auth_check"]
  }'
```

**allowed_techniques:** `headers` `xss_probe` `sqli_probe` `auth_check`

> **PERINGATAN:** Hanya gunakan pada sistem yang Anda miliki atau yang telah memberikan izin tertulis.

---

### 6. Full Audit (Semua Fitur Sekaligus)

Cocok untuk: audit keamanan menyeluruh — scan kode + analisis log + pentest + laporan.

```bash
curl -X POST http://localhost:8000/api/v1/audit \
  -H "X-API-Key: ganti-dengan-password-kuat" \
  -H "Content-Type: application/json" \
  -d '{
    "target_type": "full",
    "target_url": "https://website-pelanggan.com",
    "target_content": "<?php echo $_GET[\"q\"]; ?>",
    "filename": "search.php",
    "log_content": "192.168.1.1 - - [27/May/2026] \"GET /login?id=1+OR+1=1\" 200",
    "log_format": "apache",
    "scope": ["https://website-pelanggan.com/*"],
    "scan_profile": "full"
  }'
```

---

### 7. Async Job (untuk audit besar)

Untuk target besar yang membutuhkan waktu lama:

```bash
# Mulai audit async
curl -X POST http://localhost:8000/api/v1/audit/async \
  -H "X-API-Key: ganti-dengan-password-kuat" \
  -H "Content-Type: application/json" \
  -d '{"target_url": "https://website-pelanggan.com", "scan_profile": "full"}'

# Respons: {"job_id": "abc-123", "status": "queued", ...}

# Cek status
curl http://localhost:8000/api/v1/audit/abc-123 \
  -H "X-API-Key: ganti-dengan-password-kuat"
```

---

## Contoh Respons

```json
{
  "report_id": "a1b2c3d4-...",
  "generated_at": "2026-05-27T10:00:00Z",
  "target": "https://website-pelanggan.com",
  "risk_score": 8.5,
  "executive_summary": "Ditemukan 2 kerentanan CRITICAL dan 3 HIGH...",
  "severity_distribution": {
    "CRITICAL": 2,
    "HIGH": 3,
    "MEDIUM": 4,
    "LOW": 1,
    "INFO": 2
  },
  "findings": [
    {
      "id": "f1a2b3",
      "agent_type": "vulnerability_scanner",
      "owasp_category": "A03:2021",
      "title": "SQL Injection di endpoint login",
      "description": "Input pengguna langsung digabung ke query SQL tanpa sanitasi.",
      "severity": "CRITICAL",
      "cvss_score": 9.8,
      "evidence": "SELECT * FROM users WHERE id=' + user_id",
      "file_path": "login.php",
      "line_number": 12,
      "remediation": "Gunakan prepared statements: $stmt->prepare('SELECT * FROM users WHERE id = ?')"
    }
  ],
  "recommendations": [
    "1. [SEGERA] Perbaiki SQL Injection di login.php baris 12 — risiko kebocoran seluruh database",
    "2. [MINGGU INI] Tambahkan Content-Security-Policy header untuk mencegah XSS",
    "3. [BULAN INI] Update library yang sudah outdated"
  ],
  "human_readable": "# Security Assessment Report\n\n## Executive Summary\n..."
}
```

---

## Menjalankan Tests

```bash
# Semua tests
pytest tests/ -v

# Hanya log parser
pytest tests/test_log_parser.py -v

# Hanya API tests
pytest tests/test_api.py -v
```

---

## Struktur Proyek

```
security-agent/
├── main.py                    # Entry point FastAPI
├── requirements.txt           # Dependencies Python
├── .env.example               # Template konfigurasi
├── core/
│   ├── config.py              # Pengaturan dari .env
│   ├── models.py              # Struktur data (Pydantic)
│   └── orchestrator.py        # Koordinator multi-agent
├── agents/
│   ├── base_agent.py          # Dasar agent (tool loop + caching)
│   ├── vulnerability_scanner.py
│   ├── monitor_agent.py
│   ├── pentest_agent.py
│   └── report_agent.py
├── tools/
│   ├── file_tools.py          # Baca file kode
│   ├── http_tools.py          # HTTP probe & security header check
│   └── log_parser.py          # Parser log Apache/Nginx
├── prompts/
│   ├── vulnerability_scanner.md
│   ├── monitor_agent.md
│   ├── pentest_agent.md
│   └── report_agent.md
├── api/
│   ├── middleware.py          # Auth & rate limiting
│   ├── router.py
│   └── endpoints/
│       ├── scan.py
│       ├── monitor.py
│       ├── pentest.py
│       └── audit.py
└── tests/
    ├── conftest.py
    ├── test_api.py
    └── test_log_parser.py
```

---

## Keamanan

- Semua request diproteksi dengan `X-API-Key`
- Rate limiting: 60 request/menit per IP
- PentestAgent hanya mengakses URL dalam `scope` yang dideklarasikan
- `file_tools` hanya membaca ekstensi file yang diizinkan
- Payload SQLi/XSS yang dikirim bersifat **detection-only** (non-destructive)

---

## Troubleshooting

| Error | Solusi |
|---|---|
| `401 Unauthorized` | Periksa header `X-API-Key` — harus sama dengan `SERVICE_API_KEY` di `.env` |
| `ValidationError: ANTHROPIC_API_KEY` | Isi `ANTHROPIC_API_KEY` di file `.env` |
| `Connection refused` | Pastikan service berjalan: `python main.py` |
| `429 Too Many Requests` | Tunggu 1 menit atau naikkan `RATE_LIMIT_PER_MINUTE` di `.env` |
| `File extension not allowed` | Format file tidak didukung. Cek daftar ekstensi yang diizinkan di atas |

---

## Lisensi

MIT License — bebas digunakan dan dimodifikasi.
