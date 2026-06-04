import { create } from 'zustand';

export type UserRole = 'Director' | 'Host' | 'Mentor' | 'Admin';

interface UserState {
  user: { email: string; role: UserRole } | null;
  hydrated: boolean;
  hydrate: () => void;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const storageKey = 'tfi-command-center-user';

export const useAuthStore = create<UserState>((set) => ({
  user: null,
  hydrated: false,
  hydrate: () => {
    if (typeof window === 'undefined') return;
    const stored = window.localStorage.getItem(storageKey);
    set({ user: stored ? JSON.parse(stored) : null, hydrated: true });
  },
  login: async (email, password) => {
    const response = await fetch('/api/auth', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    const data = await response.json();
    const user = { email: data.email, role: data.role as UserRole };
    if (typeof window !== 'undefined') window.localStorage.setItem(storageKey, JSON.stringify(user));
    set({ user });
  },
  logout: async () => {
    await fetch('/api/auth', { method: 'DELETE' }).catch(() => null);
    if (typeof window !== 'undefined') window.localStorage.removeItem(storageKey);
    set({ user: null });
  },
}));
