#!/data/data/com.termux/files/usr/bin/bash
# Jalankan EAi Link dev server di Termux
# Usage: bash run-termux.sh [tunnel|lan|localhost]

cd "$(dirname "$0")"

MODE="${1:-tunnel}"

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
  tunnel)
    npx expo start --tunnel
    ;;
  lan)
    npx expo start --lan
    ;;
  localhost)
    npx expo start --localhost
    ;;
  *)
    echo "  Usage: bash run-termux.sh [tunnel|lan|localhost]"
    echo "  Default: tunnel"
    npx expo start --tunnel
    ;;
esac
