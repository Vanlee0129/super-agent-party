import type { Metadata } from 'next';
import { MainLayout } from '@/components/layout/main-layout';
import './globals.css';

export const metadata: Metadata = {
  title: 'Super Agent Party',
  description: 'AI Agent Platform with VRM and Multi-platform Bot Support',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased">
        <MainLayout>{children}</MainLayout>
      </body>
    </html>
  );
}
