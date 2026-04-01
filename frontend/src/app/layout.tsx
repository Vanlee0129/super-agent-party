import type { Metadata } from 'next';
import { Suspense } from 'react';
import { MainLayout } from '@/components/layout/main-layout';
import { Skeleton } from '@/components/ui/skeleton';
import './globals.css';

export const metadata: Metadata = {
  title: 'Super Agent Party',
  description: 'AI Agent Platform with VRM and Multi-platform Bot Support',
};

function LoadingFallback() {
  return (
    <div className="p-6 space-y-4">
      <Skeleton className="h-8 w-64" />
      <Skeleton className="h-64 w-full" />
      <div className="flex gap-4">
        <Skeleton className="h-10 w-24" />
        <Skeleton className="h-10 w-24" />
      </div>
    </div>
  );
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased">
        <MainLayout>
          <Suspense fallback={<LoadingFallback />}>
            {children}
          </Suspense>
        </MainLayout>
      </body>
    </html>
  );
}
