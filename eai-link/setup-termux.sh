#!/data/data/com.termux/files/usr/bin/bash
# EAi Link — Termux Setup Script
# Jalankan: bash setup-termux.sh

set -e

REPO_URL="https://github.com/nengahjambonada1303408010-byte/superpowers"
APP_DIR="$HOME/eai-link"
CLONE_DIR="$HOME/superpowers"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${BOLD}${BLUE}================================${NC}"
echo -e "${BOLD}${BLUE}   EAi Link — Termux Installer  ${NC}"
echo -e "${BOLD}${BLUE}================================${NC}"
echo ""

# 1. Update pkg dan install dependensi
echo -e "${YELLOW}[1/5]${NC} Memperbarui package list..."
pkg update -y -q 2>/dev/null || true

echo -e "${YELLOW}[2/5]${NC} Menginstall git dan Node.js..."
pkg install -y git nodejs-lts 2>/dev/null || pkg install -y git nodejs

# Cek versi
echo -e "   Node: $(node --version 2>/dev/null || echo 'tidak terinstall')"
echo -e "   npm : $(npm --version 2>/dev/null || echo 'tidak terinstall')"
echo -e "   git : $(git --version 2>/dev/null | head -1 || echo 'tidak terinstall')"
echo ""

# 2. Clone atau update repo
if [ -d "$CLONE_DIR/.git" ]; then
  echo -e "${YELLOW}[3/5]${NC} Repo sudah ada — update dari GitHub..."
  git -C "$CLONE_DIR" pull origin claude/create-eai-link-apk-GTyKl
else
  echo -e "${YELLOW}[3/5]${NC} Clone repository dari GitHub..."
  git clone --branch claude/create-eai-link-apk-GTyKl --depth 1 "$REPO_URL" "$CLONE_DIR"
fi

# Buat symlink/alias ke folder eai-link agar mudah diakses
if [ ! -L "$APP_DIR" ] && [ ! -d "$APP_DIR" ]; then
  ln -s "$CLONE_DIR/eai-link" "$APP_DIR"
  echo -e "   Shortcut dibuat: ${GREEN}~/eai-link${NC}"
fi

# 3. Install dependencies npm
echo ""
echo -e "${YELLOW}[4/5]${NC} Menginstall dependencies (npm install)..."
cd "$CLONE_DIR/eai-link"
npm install --prefer-offline 2>&1 | grep -E "(added|error|warn)" | tail -10

# 4. Install expo-cli lokal jika belum ada
if ! command -v expo &>/dev/null && ! npx expo --version &>/dev/null 2>&1; then
  echo ""
  echo -e "${YELLOW}     Menginstall expo CLI..."
  npm install -g expo-cli 2>/dev/null | tail -3
fi

echo ""
echo -e "${GREEN}[5/5] Setup selesai!${NC}"
echo ""
echo -e "${BOLD}================================${NC}"
echo -e "${BOLD}  Cara menjalankan EAi Link:${NC}"
echo -e "${BOLD}================================${NC}"
echo ""
echo -e "  ${BLUE}cd ~/superpowers/eai-link${NC}"
echo -e "  ${BLUE}npx expo start --tunnel${NC}"
echo ""
echo -e "  Lalu buka ${BOLD}Expo Go${NC} di HP dan scan QR code."
echo ""
echo -e "  ${YELLOW}Tips:${NC}"
echo -e "  • Gunakan ${BOLD}--tunnel${NC} agar QR code bisa di-scan dari jaringan berbeda"
echo -e "  • Install ${BOLD}Expo Go${NC} dari Play Store jika belum ada"
echo -e "  • Untuk build APK: ${BLUE}eas build --platform android --profile preview${NC}"
echo ""
