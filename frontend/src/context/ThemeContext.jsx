import { createContext, useContext, useState, useEffect, useCallback } from 'react';

const ThemeContext = createContext(null);

const STORAGE_KEY = 'signal_preferences';

function loadPrefs() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch {}
  return {};
}

function savePrefs(prefs) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
}

function getSystemTheme() {
  if (window.matchMedia('(prefers-color-scheme: dark)').matches) return 'dark';
  return 'light';
}

export function ThemeProvider({ children }) {
  const stored = loadPrefs();

  const [themeMode, setThemeMode] = useState(stored.themeMode || 'system');
  const [fontSize, setFontSize] = useState(stored.fontSize || 'medium');
  const [langPref, setLangPref] = useState(stored.langPref || 'all');

  const resolvedTheme = themeMode === 'system' ? getSystemTheme() : themeMode;

  const persist = useCallback((key, value) => {
    const prefs = loadPrefs();
    prefs[key] = value;
    savePrefs(prefs);
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', resolvedTheme);
  }, [resolvedTheme]);

  useEffect(() => {
    document.documentElement.setAttribute('data-font-size', fontSize);
    const sizeMap = { small: '12px', medium: '15px', large: '18px' };
    document.documentElement.style.fontSize = sizeMap[fontSize] || '15px';
  }, [fontSize]);

  useEffect(() => {
    if (themeMode !== 'system') return;
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = () => {
      const t = getSystemTheme();
      document.documentElement.setAttribute('data-theme', t);
    };
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, [themeMode]);

  const updateThemeMode = useCallback((mode) => {
    setThemeMode(mode);
    persist('themeMode', mode);
    const resolved = mode === 'system' ? getSystemTheme() : mode;
    document.documentElement.setAttribute('data-theme', resolved);
  }, [persist]);

  const updateFontSize = useCallback((size) => {
    setFontSize(size);
    persist('fontSize', size);
    document.documentElement.setAttribute('data-font-size', size);
    const sizeMap = { small: '12px', medium: '15px', large: '18px' };
    document.documentElement.style.fontSize = sizeMap[size] || '15px';
  }, [persist]);

  const updateLangPref = useCallback((lang) => {
    setLangPref(lang);
    persist('langPref', lang);
  }, [persist]);

  return (
    <ThemeContext.Provider value={{
      themeMode, resolvedTheme, updateThemeMode,
      fontSize, updateFontSize,
      langPref, updateLangPref,
    }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}
