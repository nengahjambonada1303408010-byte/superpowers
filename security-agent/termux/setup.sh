#!/data/data/com.termux/files/usr/bin/bash
# =============================================================
# Setup Agentic AI Security Scanner di Termux (Android)
# Jalankan: bash setup.sh
# =============================================================

set -eo pipefail 2>/dev/null || true   # lanjut walau satu step gagal

RED='\033[91m'; YELLOW='\033[93m'; GREEN='\033[92m'
CYAN='\033[96m'; BOLD='\033[1m'; RESET='\033[0m'

echo -e "${CYAN}${BOLD}"
echo "╔══════════════════════════════════════════════╗"
echo "║   Setup Agentic AI Security Scanner          ║"
echo "║   Termux / Android                           ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${RESET}"

# ── Step 1: Update Termux packages ───────────────────────────
echo -e "${CYAN}[1/6] Update package list...${RESET}"
pkg update -y -o Dpkg::Options::="--force-confnew" 2>/dev/null || true

# ── Step 2: Install system dependencies ──────────────────────
echo -e "${CYAN}[2/6] Install dependencies sistem...${RESET}"
pkg install -y python python-pip clang libffi openssl libjpeg-turbo libxml2 libxslt curl git 2>/dev/null || {
    echo -e "${YELLOW}Beberapa paket mungkin tidak tersedia, melanjutkan...${RESET}"
}

# ── Step 3: Upgrade pip via pkg (bukan pip install --upgrade pip) ────
echo -e "${CYAN}[3/6] Upgrade pip via pkg...${RESET}"
pkg upgrade python-pip -y 2>/dev/null || true

# ── Step 4: Install Python packages ──────────────────────────
echo -e "${CYAN}[4/6] Install Python packages...${RESET}"
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
pip install -r "$SCRIPT_DIR/requirements-termux.txt" --quiet

# ── Step 5: Setup .env ───────────────────────────────────────
echo -e "${CYAN}[5/6] Konfigurasi .env...${RESET}"
ENV_FILE="$SCRIPT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    cp "$SCRIPT_DIR/.env.example" "$ENV_FILE"
    echo -e "${YELLOW}File .env dibuat. Isi API key Anda:${RESET}"
    echo ""
    echo -e "  ${BOLD}nano $ENV_FILE${RESET}"
    echo ""
    echo -e "  Ganti: ${YELLOW}ANTHROPIC_API_KEY=sk-ant-your-key-here${RESET}"
    echo -e "  Dengan API key dari: https://console.anthropic.com"
else
    echo -e "${GREEN}File .env sudah ada.${RESET}"
fi

# ── Step 6: Buat direktori laporan ───────────────────────────
echo -e "${CYAN}[6/6] Membuat direktori laporan...${RESET}"
mkdir -p ~/security-reports
echo -e "${GREEN}Laporan akan disimpan di: ~/security-reports/${RESET}"

# ── Step 7: Buat shortcut ────────────────────────────────────
SHORTCUT="$PREFIX/bin/aisec"
cat > "$SHORTCUT" << 'SHORTCUT_EOF'
#!/data/data/com.termux/files/usr/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")/../../home/$(whoami)/security-agent" 2>/dev/null || echo "$HOME/security-agent")"
# Coba temukan direktori security-agent
for D in "$HOME/security-agent" "$HOME/superpowers/security-agent" "$(pwd)/security-agent" "$(pwd)"; do
    if [ -f "$D/cli.py" ]; then
        cd "$D" && python cli.py "$@"
        exit $?
    fi
done
echo "ERROR: Tidak bisa menemukan cli.py. Jalankan dari direktori security-agent:"
echo "  cd ~/security-agent && python cli.py $@"
SHORTCUT_EOF
chmod +x "$SHORTCUT" 2>/dev/null || true

echo ""
echo -e "${GREEN}${BOLD}══════════════════════════════════════${RESET}"
echo -e "${GREEN}${BOLD}  Setup selesai!${RESET}"
echo -e "${GREEN}${BOLD}══════════════════════════════════════${RESET}"
echo ""
echo -e "Langkah selanjutnya:"
echo -e "  1. ${YELLOW}nano $ENV_FILE${RESET}  ← isi ANTHROPIC_API_KEY"
echo -e "  2. Gunakan salah satu cara berikut:"
echo ""
echo -e "  ${BOLD}Cara A — CLI langsung (direkomendasikan di Termux):${RESET}"
echo -e "  ${CYAN}cd $SCRIPT_DIR${RESET}"
echo -e "  ${CYAN}python cli.py scan --url https://target.com${RESET}"
echo -e "  ${CYAN}python cli.py scan --file login.php${RESET}"
echo -e "  ${CYAN}python cli.py adaptive --url https://target.com${RESET}"
echo ""
echo -e "  ${BOLD}Cara B — REST API Server:${RESET}"
echo -e "  ${CYAN}python cli.py server${RESET}"
echo -e "  Buka browser: http://localhost:8000/docs"
echo ""
