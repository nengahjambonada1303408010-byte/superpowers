import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { MT5Position } from '../types/mt5';

interface Props {
  position: MT5Position;
}

export default function PositionItem({ position: p }: Props) {
  const isBuy = p.type === 0;
  const totalPL = p.profit + p.swap;
  const positive = totalPL >= 0;

  return (
    <View style={styles.row}>
      <View style={[styles.typeBadge, isBuy ? styles.buyBadge : styles.sellBadge]}>
        <Text style={styles.typeText}>{isBuy ? 'BUY' : 'SELL'}</Text>
      </View>

      <View style={styles.info}>
        <Text style={styles.symbol}>{p.symbol}</Text>
        <Text style={styles.detail}>
          {p.volume.toFixed(2)} lot · @{p.openPrice.toFixed(5)}
        </Text>
        {p.comment ? (
          <Text style={styles.comment} numberOfLines={1}>
            {p.comment}
          </Text>
        ) : null}
      </View>

      <View style={styles.right}>
        <Text style={[styles.profit, positive ? styles.profitPos : styles.profitNeg]}>
          {positive ? '+' : ''}
          {totalPL.toFixed(2)}
        </Text>
        <Text style={styles.ticket}>#{p.ticket}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 16,
    marginVertical: 4,
    backgroundColor: '#1e293b',
    borderRadius: 10,
    padding: 12,
    gap: 12,
  },
  typeBadge: {
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 4,
    minWidth: 44,
    alignItems: 'center',
  },
  buyBadge: { backgroundColor: '#14532d' },
  sellBadge: { backgroundColor: '#450a0a' },
  typeText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  info: { flex: 1 },
  symbol: {
    color: '#f1f5f9',
    fontSize: 15,
    fontWeight: '700',
  },
  detail: {
    color: '#64748b',
    fontSize: 12,
    marginTop: 2,
  },
  comment: {
    color: '#475569',
    fontSize: 11,
    marginTop: 2,
  },
  right: { alignItems: 'flex-end' },
  profit: {
    fontSize: 16,
    fontWeight: '700',
  },
  profitPos: { color: '#22c55e' },
  profitNeg: { color: '#ef4444' },
  ticket: {
    color: '#475569',
    fontSize: 11,
    marginTop: 2,
  },
});
