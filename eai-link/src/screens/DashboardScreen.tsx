import React, { useEffect, useState, useCallback, useRef } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { useAuth } from '../context/AuthContext';
import { MT5Account, MT5Position } from '../types/mt5';
import AccountCard from '../components/AccountCard';
import PositionItem from '../components/PositionItem';
import MarketTicker from '../components/MarketTicker';

const REFRESH_INTERVAL_MS = 10_000;

export default function DashboardScreen() {
  const { client, signOut } = useAuth();
  const [account, setAccount] = useState<MT5Account | null>(null);
  const [positions, setPositions] = useState<MT5Position[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [countdown, setCountdown] = useState(REFRESH_INTERVAL_MS / 1000);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const countdownRef = useRef<ReturnType<typeof setInterval> | null>(null);

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

  const startAutoRefresh = useCallback(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    if (countdownRef.current) clearInterval(countdownRef.current);

    setCountdown(REFRESH_INTERVAL_MS / 1000);

    intervalRef.current = setInterval(async () => {
      await fetchAll();
      setCountdown(REFRESH_INTERVAL_MS / 1000);
    }, REFRESH_INTERVAL_MS);

    countdownRef.current = setInterval(() => {
      setCountdown((c) => (c > 1 ? c - 1 : REFRESH_INTERVAL_MS / 1000));
    }, 1000);
  }, [fetchAll]);

  useEffect(() => {
    (async () => {
      setLoading(true);
      await fetchAll();
      setLoading(false);
      startAutoRefresh();
    })();
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (countdownRef.current) clearInterval(countdownRef.current);
    };
  }, [fetchAll, startAutoRefresh]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchAll();
    setRefreshing(false);
    startAutoRefresh();
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#3b82f6" />
        <Text style={styles.loadingText}>Menghubungkan ke MT5...</Text>
      </View>
    );
  }

  return (
    <FlatList
      data={positions}
      keyExtractor={(item) => String(item.ticket)}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={handleRefresh}
          tintColor="#3b82f6"
        />
      }
      ListHeaderComponent={
        <>
          <MarketTicker positions={positions} />
          {account && <AccountCard account={account} />}
          {error && (
            <View style={styles.errorBox}>
              <Text style={styles.errorText}>{error}</Text>
              <TouchableOpacity onPress={() => { fetchAll(); startAutoRefresh(); }}>
                <Text style={styles.retryText}>Coba lagi</Text>
              </TouchableOpacity>
            </View>
          )}
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>
              Posisi Terbuka ({positions.length})
            </Text>
            <View style={styles.headerRight}>
              <Text style={styles.countdown}>🔄 {countdown}s</Text>
              <TouchableOpacity onPress={signOut} style={styles.logoutBtn}>
                <Text style={styles.logoutText}>Logout</Text>
              </TouchableOpacity>
            </View>
          </View>
        </>
      }
      ListEmptyComponent={
        <View style={styles.emptyBox}>
          <Text style={styles.emptyIcon}>📭</Text>
          <Text style={styles.emptyText}>Tidak ada posisi terbuka</Text>
        </View>
      }
      renderItem={({ item }) => <PositionItem position={item} />}
      contentContainerStyle={styles.list}
    />
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
  loadingText: {
    color: '#64748b',
    fontSize: 14,
  },
  list: {
    backgroundColor: '#0f172a',
    paddingBottom: 24,
  },
  errorBox: {
    margin: 16,
    padding: 14,
    backgroundColor: '#1e293b',
    borderRadius: 10,
    borderLeftWidth: 4,
    borderLeftColor: '#ef4444',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  errorText: {
    color: '#fca5a5',
    fontSize: 13,
    flex: 1,
  },
  retryText: {
    color: '#3b82f6',
    fontSize: 13,
    fontWeight: '600',
    marginLeft: 12,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  sectionTitle: {
    color: '#94a3b8',
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  countdown: {
    color: '#475569',
    fontSize: 12,
  },
  logoutBtn: {},
  logoutText: {
    color: '#ef4444',
    fontSize: 13,
    fontWeight: '600',
  },
  emptyBox: {
    padding: 48,
    alignItems: 'center',
    gap: 8,
  },
  emptyIcon: {
    fontSize: 32,
  },
  emptyText: {
    color: '#475569',
    fontSize: 14,
  },
});
