import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { MT5Position } from '../types/mt5';

interface Props {
  positions: MT5Position[];
}

export default function MarketTicker({ positions }: Props) {
  if (positions.length === 0) return null;

  // Deduplicate by symbol, show current price and net P&L
  const symbolMap = new Map<string, { currentPrice: number; totalPL: number; type: 0 | 1 }>();
  for (const p of positions) {
    const existing = symbolMap.get(p.symbol);
    if (existing) {
      existing.totalPL += p.profit + p.swap;
    } else {
      symbolMap.set(p.symbol, {
        currentPrice: p.currentPrice,
        totalPL: p.profit + p.swap,
        type: p.type,
      });
    }
  }

  const tickers = Array.from(symbolMap.entries());

  return (
    <View style={styles.wrapper}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.row}>
        {tickers.map(([symbol, data]) => {
          const positive = data.totalPL >= 0;
          return (
            <View key={symbol} style={styles.chip}>
              <Text style={styles.symbol}>{symbol}</Text>
              <Text style={styles.price}>{data.currentPrice.toFixed(5)}</Text>
              <Text style={[styles.pl, positive ? styles.pos : styles.neg]}>
                {positive ? '+' : ''}{data.totalPL.toFixed(2)}
              </Text>
            </View>
          );
        })}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    backgroundColor: '#1e293b',
    borderBottomWidth: 1,
    borderBottomColor: '#334155',
  },
  row: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    gap: 8,
  },
  chip: {
    backgroundColor: '#0f172a',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
    alignItems: 'center',
    minWidth: 80,
  },
  symbol: {
    color: '#94a3b8',
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  price: {
    color: '#f1f5f9',
    fontSize: 13,
    fontWeight: '600',
    marginTop: 2,
  },
  pl: {
    fontSize: 11,
    fontWeight: '700',
    marginTop: 1,
  },
  pos: { color: '#22c55e' },
  neg: { color: '#ef4444' },
});
