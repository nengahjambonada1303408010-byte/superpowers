import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { MT5Account } from '../types/mt5';

interface Props {
  account: MT5Account;
}

function formatCurrency(n: number, currency: string) {
  return n.toLocaleString('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
  });
}

function Stat({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <View style={styles.stat}>
      <Text style={styles.statLabel}>{label}</Text>
      <Text style={[styles.statValue, highlight && styles.statHighlight]}>{value}</Text>
    </View>
  );
}

export default function AccountCard({ account }: Props) {
  const floatingPL = account.equity - account.balance;
  const plPositive = floatingPL >= 0;

  return (
    <View style={styles.card}>
      <View style={styles.topRow}>
        <View>
          <Text style={styles.name}>{account.name}</Text>
          <Text style={styles.meta}>
            #{account.login} · {account.server}
          </Text>
        </View>
        <View style={styles.leverageBadge}>
          <Text style={styles.leverageText}>1:{account.leverage}</Text>
        </View>
      </View>

      <View style={styles.balanceRow}>
        <Text style={styles.balanceLabel}>Balance</Text>
        <Text style={styles.balanceValue}>
          {formatCurrency(account.balance, account.currency)}
        </Text>
      </View>

      <View style={styles.divider} />

      <View style={styles.grid}>
        <Stat
          label="Equity"
          value={formatCurrency(account.equity, account.currency)}
        />
        <Stat
          label="Float P/L"
          value={(plPositive ? '+' : '') + formatCurrency(floatingPL, account.currency)}
          highlight
        />
        <Stat
          label="Margin"
          value={formatCurrency(account.margin, account.currency)}
        />
        <Stat
          label="Free Margin"
          value={formatCurrency(account.freeMargin, account.currency)}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    margin: 16,
    marginBottom: 8,
    backgroundColor: '#1e293b',
    borderRadius: 16,
    padding: 16,
  },
  topRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  name: {
    color: '#f1f5f9',
    fontSize: 18,
    fontWeight: '700',
  },
  meta: {
    color: '#64748b',
    fontSize: 12,
    marginTop: 2,
  },
  leverageBadge: {
    backgroundColor: '#0f172a',
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  leverageText: {
    color: '#94a3b8',
    fontSize: 12,
    fontWeight: '600',
  },
  balanceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  balanceLabel: {
    color: '#64748b',
    fontSize: 13,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  balanceValue: {
    color: '#f8fafc',
    fontSize: 22,
    fontWeight: '800',
  },
  divider: {
    height: 1,
    backgroundColor: '#334155',
    marginBottom: 12,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  stat: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: '#0f172a',
    borderRadius: 8,
    padding: 10,
  },
  statLabel: {
    color: '#64748b',
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  statValue: {
    color: '#cbd5e1',
    fontSize: 14,
    fontWeight: '600',
  },
  statHighlight: {
    color: '#22c55e',
  },
});
