import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { useAuth } from '../context/AuthContext';
import { MT5Account, MT5Position } from '../types/mt5';

interface Signal {
  symbol: string;
  direction: 'BUY' | 'SELL' | 'HOLD';
  strength: 'KUAT' | 'SEDANG' | 'LEMAH';
  reason: string;
  score: number;
}

interface PortfolioHealth {
  label: string;
  color: string;
  description: string;
}

function analyzePositions(positions: MT5Position[], account: MT5Account): Signal[] {
  const bySymbol = new Map<string, MT5Position[]>();
  for (const p of positions) {
    const list = bySymbol.get(p.symbol) ?? [];
    list.push(p);
    bySymbol.set(p.symbol, list);
  }

  const signals: Signal[] = [];
  for (const [symbol, pos] of bySymbol.entries()) {
    const totalPL = pos.reduce((s, p) => s + p.profit + p.swap, 0);
    const totalVol = pos.reduce((s, p) => s + p.volume, 0);
    const buyVol = pos.filter((p) => p.type === 0).reduce((s, p) => s + p.volume, 0);
    const sellVol = pos.filter((p) => p.type === 1).reduce((s, p) => s + p.volume, 0);
    const netBias = buyVol - sellVol;
    const plPct = account.balance > 0 ? (totalPL / account.balance) * 100 : 0;

    let direction: Signal['direction'] = 'HOLD';
    let strength: Signal['strength'] = 'LEMAH';
    let reason = '';
    let score = 50;

    if (totalPL < 0 && Math.abs(plPct) > 2) {
      direction = netBias > 0 ? 'SELL' : 'BUY';
      strength = Math.abs(plPct) > 5 ? 'KUAT' : 'SEDANG';
      reason = `Floating loss ${plPct.toFixed(2)}% — pertimbangkan hedging atau cut loss`;
      score = 30;
    } else if (totalPL > 0 && plPct > 1) {
      direction = 'HOLD';
      strength = plPct > 3 ? 'KUAT' : 'SEDANG';
      reason = `Profit berjalan ${plPct.toFixed(2)}% — pertahankan dan set trailing stop`;
      score = 75;
    } else if (netBias > 0.5) {
      direction = 'BUY';
      strength = 'LEMAH';
      reason = `Net bias BUY (${buyVol.toFixed(2)} lot vs ${sellVol.toFixed(2)} lot SELL)`;
      score = 60;
    } else if (netBias < -0.5) {
      direction = 'SELL';
      strength = 'LEMAH';
      reason = `Net bias SELL (${sellVol.toFixed(2)} lot vs ${buyVol.toFixed(2)} lot BUY)`;
      score = 40;
    } else {
      direction = 'HOLD';
      strength = 'SEDANG';
      reason = `Posisi seimbang — total volume ${totalVol.toFixed(2)} lot`;
      score = 55;
    }

    signals.push({ symbol, direction, strength, reason, score });
  }

  return signals.sort((a, b) => Math.abs(a.score - 50) - Math.abs(b.score - 50)).reverse();
}

function getPortfolioHealth(account: MT5Account, positions: MT5Position[]): PortfolioHealth {
  if (!account || positions.length === 0) {
    return { label: 'IDLE', color: '#64748b', description: 'Tidak ada posisi terbuka.' };
  }
  const floatPL = account.equity - account.balance;
  const floatPct = account.balance > 0 ? (floatPL / account.balance) * 100 : 0;
  const marginLevel = account.margin > 0 ? (account.equity / account.margin) * 100 : 9999;

  if (marginLevel < 150 || floatPct < -10) {
    return {
      label: 'BAHAYA',
      color: '#ef4444',
      description: `Margin level ${marginLevel.toFixed(0)}% — risiko margin call tinggi!`,
    };
  }
  if (marginLevel < 300 || floatPct < -5) {
    return {
      label: 'WASPADA',
      color: '#f59e0b',
      description: `Margin level ${marginLevel.toFixed(0)}% — monitor ketat diperlukan.`,
    };
  }
  if (floatPct >= 2) {
    return {
      label: 'SEHAT',
      color: '#22c55e',
      description: `Floating profit +${floatPct.toFixed(2)}% — portfolio dalam kondisi baik.`,
    };
  }
  return {
    label: 'NORMAL',
    color: '#3b82f6',
    description: `Margin level ${marginLevel.toFixed(0)}% — kondisi stabil.`,
  };
}

function SignalCard({ signal }: { signal: Signal }) {
  const dirColor =
    signal.direction === 'BUY'
      ? '#22c55e'
      : signal.direction === 'SELL'
      ? '#ef4444'
      : '#f59e0b';
  const strengthColor =
    signal.strength === 'KUAT'
      ? '#ef4444'
      : signal.strength === 'SEDANG'
      ? '#f59e0b'
      : '#64748b';

  return (
    <View style={styles.signalCard}>
      <View style={styles.signalTop}>
        <Text style={styles.signalSymbol}>{signal.symbol}</Text>
        <View style={styles.badges}>
          <View style={[styles.badge, { backgroundColor: dirColor + '22' }]}>
            <Text style={[styles.badgeText, { color: dirColor }]}>{signal.direction}</Text>
          </View>
          <View style={[styles.badge, { backgroundColor: strengthColor + '22' }]}>
            <Text style={[styles.badgeText, { color: strengthColor }]}>{signal.strength}</Text>
          </View>
        </View>
      </View>
      <View style={styles.scoreBar}>
        <View style={[styles.scoreFill, { width: `${signal.score}%`, backgroundColor: dirColor }]} />
      </View>
      <Text style={styles.signalReason}>{signal.reason}</Text>
    </View>
  );
}

export default function SignalScreen() {
  const { client } = useAuth();
  const [account, setAccount] = useState<MT5Account | null>(null);
  const [positions, setPositions] = useState<MT5Position[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    if (!client) return;
    try {
      const [acct, pos] = await Promise.all([
        client.getAccount(),
        client.getPositions(),
      ]);
      setAccount(acct);
      setPositions(pos);
      setError(null);
    } catch (e: any) {
      setError(e.message ?? 'Gagal memuat data');
    }
  }, [client]);

  useEffect(() => {
    (async () => {
      setLoading(true);
      await fetchAll();
      setLoading(false);
    })();
  }, [fetchAll]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchAll();
    setRefreshing(false);
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#3b82f6" />
        <Text style={styles.loadingText}>Menganalisis posisi...</Text>
      </View>
    );
  }

  const signals = account ? analyzePositions(positions, account) : [];
  const health = account ? getPortfolioHealth(account, positions) : null;

  return (
    <ScrollView
      style={styles.scroll}
      contentContainerStyle={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} tintColor="#3b82f6" />
      }
    >
      {error && (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity onPress={fetchAll}>
            <Text style={styles.retryText}>Coba lagi</Text>
          </TouchableOpacity>
        </View>
      )}

      {health && (
        <View style={[styles.healthCard, { borderLeftColor: health.color }]}>
          <View style={styles.healthTop}>
            <Text style={styles.healthLabel}>Status Portfolio</Text>
            <Text style={[styles.healthStatus, { color: health.color }]}>{health.label}</Text>
          </View>
          <Text style={styles.healthDesc}>{health.description}</Text>
        </View>
      )}

      <Text style={styles.sectionTitle}>Analisis Sinyal per Simbol</Text>

      {signals.length === 0 ? (
        <View style={styles.emptyBox}>
          <Text style={styles.emptyIcon}>🤖</Text>
          <Text style={styles.emptyText}>Tidak ada posisi untuk dianalisis</Text>
          <Text style={styles.emptySubtext}>Buka posisi di MT5 untuk melihat sinyal</Text>
        </View>
      ) : (
        signals.map((s) => <SignalCard key={s.symbol} signal={s} />)
      )}

      <Text style={styles.disclaimer}>
        * Sinyal ini bersifat informatif berdasarkan posisi aktif Anda.
        Bukan saran investasi.
      </Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  center: {
    flex: 1,
    backgroundColor: '#0f172a',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  loadingText: { color: '#64748b', fontSize: 14 },
  scroll: { flex: 1, backgroundColor: '#0f172a' },
  container: { padding: 16, paddingBottom: 32 },
  errorBox: {
    marginBottom: 12,
    padding: 14,
    backgroundColor: '#1e293b',
    borderRadius: 10,
    borderLeftWidth: 4,
    borderLeftColor: '#ef4444',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  errorText: { color: '#fca5a5', fontSize: 13, flex: 1 },
  retryText: { color: '#3b82f6', fontSize: 13, fontWeight: '600', marginLeft: 12 },
  healthCard: {
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderLeftWidth: 4,
  },
  healthTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  healthLabel: { color: '#64748b', fontSize: 12, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 1 },
  healthStatus: { fontSize: 16, fontWeight: '800' },
  healthDesc: { color: '#94a3b8', fontSize: 13, lineHeight: 18 },
  sectionTitle: {
    color: '#64748b',
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 10,
  },
  signalCard: {
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
  },
  signalTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  signalSymbol: { color: '#f1f5f9', fontSize: 16, fontWeight: '700' },
  badges: { flexDirection: 'row', gap: 6 },
  badge: { borderRadius: 6, paddingHorizontal: 8, paddingVertical: 3 },
  badgeText: { fontSize: 11, fontWeight: '700', letterSpacing: 0.5 },
  scoreBar: {
    height: 4,
    backgroundColor: '#0f172a',
    borderRadius: 2,
    marginBottom: 10,
    overflow: 'hidden',
  },
  scoreFill: { height: '100%', borderRadius: 2 },
  signalReason: { color: '#94a3b8', fontSize: 13, lineHeight: 18 },
  emptyBox: { alignItems: 'center', paddingVertical: 48, gap: 8 },
  emptyIcon: { fontSize: 40 },
  emptyText: { color: '#475569', fontSize: 15, fontWeight: '600' },
  emptySubtext: { color: '#334155', fontSize: 13 },
  disclaimer: {
    color: '#334155',
    fontSize: 11,
    textAlign: 'center',
    marginTop: 20,
    lineHeight: 16,
  },
});
