export interface MT5Credentials {
  serverUrl: string;
  login: string;
  password: string;
}

export interface MT5LoginResponse {
  token: string;
}

export interface MT5Account {
  login: number;
  name: string;
  server: string;
  balance: number;
  equity: number;
  margin: number;
  freeMargin: number;
  currency: string;
  leverage: number;
}

export interface MT5Position {
  ticket: number;
  symbol: string;
  type: 0 | 1; // 0 = BUY, 1 = SELL
  volume: number;
  openPrice: number;
  currentPrice: number;
  profit: number;
  swap: number;
  openTime: string;
  comment: string;
}

export interface MT5ApiError {
  code: number;
  message: string;
}
