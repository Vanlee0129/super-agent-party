'use client';

import { useState, useEffect } from 'react';

export function useKeyboardHeight() {
  const [keyboardHeight, setKeyboardHeight] = useState(0);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const handleKeyboardShow = (e: KeyboardEvent) => {
      if ('endCoordinates' in e && e.endCoordinates) {
        setKeyboardHeight((e as unknown as { endCoordinates: { height: number } }).endCoordinates.height);
      }
    };

    const handleKeyboardHide = () => {
      setKeyboardHeight(0);
    };

    // Check for iOS keyboard height via visualViewport
    const handleVisualViewportChange = () => {
      if (typeof window !== 'undefined' && 'visualViewport' in window) {
        const visualViewport = window.visualViewport;
        if (visualViewport) {
          const keyboardHeightValue = window.innerHeight - (visualViewport?.height || 0);
          // Only set if keyboard appears to be visible (height difference > 100px)
          setKeyboardHeight(keyboardHeightValue > 100 ? keyboardHeightValue : 0);
        }
      }
    };

    // Try the standard Keyboard API first (modern browsers)
    const keyboardShowListener = window.addEventListener('keyboardDidShow', handleKeyboardShow as EventListener);
    const keyboardHideListener = window.addEventListener('keyboardDidHide', handleKeyboardHide);

    // Fallback for iOS Safari and other browsers using visualViewport
    const visualViewportListener = window.visualViewport?.addEventListener?.('resize', handleVisualViewportChange);

    return () => {
      window.removeEventListener('keyboardDidShow', handleKeyboardShow as EventListener);
      window.removeEventListener('keyboardDidHide', handleKeyboardHide);
      if (visualViewportListener && window.visualViewport) {
        window.visualViewport.removeEventListener('resize', handleVisualViewportChange);
      }
    };
  }, []);

  return keyboardHeight;
}
