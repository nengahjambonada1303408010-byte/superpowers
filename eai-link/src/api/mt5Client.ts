import axios, { AxiosInstance, AxiosError } from 'axios';
import {
  MT5LoginResponse,
  MT5Account,
  MT5Position,
  MT5ApiError,
} from '../types/mt5';

export class MT5Client {
  private http: AxiosInstance;
  private token: string | null = null;

  constructor(serverUrl: string) {
    this.http = axios.create({
      baseURL: serverUrl.replace(/\/$/, '') + '/api',
      timeout: 15000,
      headers: { 'Content-Type': 'application/json' },
    });

    this.http.interceptors.request.use((config) => {
      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`;
      }
      return config;
    });
  }

  setToken(token: string) {
    this.token = token;
  }

  clearToken() {
    this.token = null;
  }

  async login(login: string, password: string): Promise<string> {
    try {
      const res = await this.http.post<MT5LoginResponse>('/login', {
        login,
        password,
      });
      this.token = res.data.token;
      return res.data.token;
    } catch (err) {
      throw this.normalizeError(err);
    }
  }

  async getAccount(): Promise<MT5Account> {
    try {
      const res = await this.http.get<MT5Account>('/account');
      return res.data;
    } catch (err) {
      throw this.normalizeError(err);
    }
  }

  async getPositions(): Promise<MT5Position[]> {
    try {
      const res = await this.http.get<MT5Position[]>('/positions');
      return res.data;
    } catch (err) {
      throw this.normalizeError(err);
    }
  }

  private normalizeError(err: unknown): MT5ApiError {
    if (axios.isAxiosError(err)) {
      const axErr = err as AxiosError<{ message?: string; error?: string }>;
      return {
        code: axErr.response?.status ?? 0,
        message:
          axErr.response?.data?.message ??
          axErr.response?.data?.error ??
          axErr.message,
      };
    }
    return { code: -1, message: String(err) };
  }
}
