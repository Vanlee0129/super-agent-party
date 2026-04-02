'use client';

import { useState, useRef, useCallback } from 'react';

interface UsePullToRefreshOptions {
  onRefresh: () => Promise<void>;
  threshold?: number;
  resistance?: number;
}

interface UsePullToRefreshReturn {
  isRefreshing: boolean;
  handleRefresh: () => Promise<void>;
  pullProgress: number;
  containerProps: {
    onTouchStart: (e: React.TouchEvent) => void;
    onTouchMove: (e: React.TouchEvent) => void;
    onTouchEnd: (e: React.TouchEvent) => void;
    style: React.CSSProperties;
  };
  indicatorProps: {
    className: string;
    style: React.CSSProperties;
  };
}

export function usePullToRefresh({
  onRefresh,
  threshold = 80,
  resistance = 2.5,
}: UsePullToRefreshOptions): UsePullToRefreshReturn {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [pullDistance, setPullDistance] = useState(0);
  const [pullProgress, setPullProgress] = useState(0);

  const startYRef = useRef<number>(0);
  const currentYRef = useRef<number>(0);
  const isPullingRef = useRef<boolean>(false);

  const handleRefresh = useCallback(async () => {
    if (isRefreshing) return;
    setIsRefreshing(true);
    try {
      await onRefresh();
    } finally {
      setIsRefreshing(false);
      setPullDistance(0);
      setPullProgress(0);
    }
  }, [isRefreshing, onRefresh]);

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    // Only activate when at the top of the scroll
    const scrollTop = (e.currentTarget as HTMLElement).scrollTop;
    if (scrollTop <= 0) {
      startYRef.current = e.touches[0].clientY;
      isPullingRef.current = true;
    }
  }, []);

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (!isPullingRef.current) return;

    currentYRef.current = e.touches[0].clientY;
    const pullDelta = Math.max(0, currentYRef.current - startYRef.current);
    const resistedDistance = pullDelta / resistance;
    const progress = Math.min(pullDelta / threshold, 1);

    setPullDistance(resistedDistance);
    setPullProgress(progress);
  }, [resistance, threshold]);

  const handleTouchEnd = useCallback(() => {
    if (!isPullingRef.current) return;

    isPullingRef.current = false;

    if (pullProgress >= 1) {
      handleRefresh();
    } else {
      setPullDistance(0);
      setPullProgress(0);
    }
  }, [pullProgress, handleRefresh]);

  const containerProps = {
    onTouchStart: handleTouchStart,
    onTouchMove: handleTouchMove,
    onTouchEnd: handleTouchEnd,
    style: {
      transform: pullDistance > 0 ? `translateY(${pullDistance}px)` : undefined,
      transition: pullDistance > 0 ? 'none' : 'transform 0.3s ease-out',
    } as React.CSSProperties,
  };

  const indicatorProps = {
    className: 'flex justify-center items-center',
    style: {
      height: isRefreshing ? 60 : pullDistance > 0 ? Math.min(pullDistance, threshold) : 0,
      opacity: isRefreshing ? 1 : pullDistance > 0 ? Math.min(pullProgress * 2, 1) : 0,
    } as React.CSSProperties,
  };

  return {
    isRefreshing,
    handleRefresh,
    pullProgress,
    containerProps,
    indicatorProps,
  };
}
