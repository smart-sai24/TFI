import '../styles/globals.css';
import type { Metadata } from 'next';
import { AppShell } from '../components/app-shell';
import { Providers } from '../components/providers';

export const metadata: Metadata = {
  title: 'TFI Command Center 2.0',
  description: 'AI-powered internship operations and intelligence platform for Techno Future India.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#0B1020] text-slate-100">
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
