import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
} from 'react';
import * as SecureStore from 'expo-secure-store';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { MT5Client } from '../api/mt5Client';
import { MT5Credentials } from '../types/mt5';

const SECURE_TOKEN_KEY = 'mt5_token';
const ASYNC_SERVER_KEY = 'mt5_server_url';
const ASYNC_LOGIN_KEY = 'mt5_login';

interface AuthState {
  client: MT5Client | null;
  isAuthenticated: boolean;
  serverUrl: string;
  login: string;
  error: string | null;
  loading: boolean;
  signIn: (creds: MT5Credentials) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [client, setClient] = useState<MT5Client | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [serverUrl, setServerUrl] = useState('');
  const [login, setLogin] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    (async () => {
      const [savedUrl, savedLogin, savedToken] = await Promise.all([
        AsyncStorage.getItem(ASYNC_SERVER_KEY),
        AsyncStorage.getItem(ASYNC_LOGIN_KEY),
        SecureStore.getItemAsync(SECURE_TOKEN_KEY),
      ]);
      if (savedUrl && savedLogin && savedToken) {
        const c = new MT5Client(savedUrl);
        c.setToken(savedToken);
        setClient(c);
        setServerUrl(savedUrl);
        setLogin(savedLogin);
        setIsAuthenticated(true);
      }
    })();
  }, []);

  const signIn = useCallback(async (creds: MT5Credentials) => {
    setLoading(true);
    setError(null);
    try {
      const c = new MT5Client(creds.serverUrl);
      const token = await c.login(creds.login, creds.password);
      await Promise.all([
        SecureStore.setItemAsync(SECURE_TOKEN_KEY, token),
        AsyncStorage.setItem(ASYNC_SERVER_KEY, creds.serverUrl),
        AsyncStorage.setItem(ASYNC_LOGIN_KEY, creds.login),
      ]);
      setClient(c);
      setServerUrl(creds.serverUrl);
      setLogin(creds.login);
      setIsAuthenticated(true);
    } catch (e: any) {
      setError(e.message ?? 'Login gagal');
    } finally {
      setLoading(false);
    }
  }, []);

  const signOut = useCallback(async () => {
    await Promise.all([
      SecureStore.deleteItemAsync(SECURE_TOKEN_KEY),
      AsyncStorage.removeItem(ASYNC_SERVER_KEY),
      AsyncStorage.removeItem(ASYNC_LOGIN_KEY),
    ]);
    client?.clearToken();
    setClient(null);
    setIsAuthenticated(false);
    setServerUrl('');
    setLogin('');
  }, [client]);

  return (
    <AuthContext.Provider
      value={{
        client,
        isAuthenticated,
        serverUrl,
        login,
        error,
        loading,
        signIn,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
