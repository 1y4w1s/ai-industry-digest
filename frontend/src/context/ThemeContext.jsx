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
  console.log('[ThemeContext] init | localStorage prefs:', stored);

  const [themeMode, setThemeMode] = useState(stored.themeMode || 'system');
  const [fontSize, setFontSize] = useState(stored.fontSize || 'medium');
  const [langPref, setLangPref] = useState(stored.langPref || 'all');

  const resolvedTheme = themeMode === 'system' ? getSystemTheme() : themeMode;

  const persist = useCallback((key, value) => {
    const prefs = loadPrefs();
    prefs[key] = value;
    savePrefs(prefs);
    console.log(`[ThemeContext] persist | ${key} = ${value} | full prefs:`, prefs);
  }, []);

  useEffect(() => {
    console.log(`[ThemeContext] apply data-theme="${resolvedTheme}" to <html>`);
    document.documentElement.setAttribute('data-theme', resolvedTheme);
  }, [resolvedTheme]);

  useEffect(() => {
    console.log(`[ThemeContext] apply data-font-size="${fontSize}" to <html> | current html:`, document.documentElement.outerHTML.slice(0, 300));
    document.documentElement.setAttribute('data-font-size', fontSize);
  }, [fontSize]);

  useEffect(() => {
    if (themeMode !== 'system') return;
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = () => {
      const t = getSystemTheme();
      console.log(`[ThemeContext] system theme changed → ${t}`);
      document.documentElement.setAttribute('data-theme', t);
    };
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, [themeMode]);

  const updateThemeMode = useCallback((mode) => {
    console.log(`[ThemeContext] updateThemeMode called with "${mode}" | previous="${themeMode}"`);
    setThemeMode(mode);
    persist('themeMode', mode);
  }, [themeMode, persist]);

  const updateFontSize = useCallback((size) => {
    console.log(`[ThemeContext] updateFontSize called with "${size}" | previous fontSize="${fontSize}"`);
    setFontSize(size);
    persist('fontSize', size);
  }, [fontSize, persist]);

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
