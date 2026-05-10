#!/data/data/com.termux/files/usr/bin/bash
# Jalankan EAi Link dev server di Termux
# Usage: bash run-termux.sh [tunnel|lan|localhost]

cd "$(dirname "$0")"

MODE="${1:-lan}"

echo ""
echo "  EAi Link — starting Expo ($MODE mode)"
echo "  Ctrl+C untuk berhenti"
echo ""

# Pastikan dependencies terinstall
if [ ! -d node_modules ]; then
  echo "  [!] node_modules tidak ada — jalankan npm install..."
  npm install
fi

case "$MODE" in
  lan)
    # Pakai WiFi lokal — HP & Termux harus di jaringan WiFi yang sama
    npx expo start --lan
    ;;
  localhost)
    # Pakai localhost — cocok jika Termux & Expo Go di HP yang sama
    npx expo start --localhost
    ;;
  tunnel)
    # Tunnel via ngrok — butuh ngrok terinstall
    echo "  [!] Mode tunnel butuh ngrok. Install dulu: pkg install ngrok"
    echo "  [!] Coba pakai: bash run-termux.sh lan"
    exit 1
    ;;
  *)
    echo "  Usage: bash run-termux.sh [lan|localhost]"
    echo "  Default: lan"
    npx expo start --lan
    ;;
esac
