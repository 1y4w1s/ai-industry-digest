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
  console.log('[ThemeContext] === INIT === | localStorage prefs:', stored);

  const [themeMode, setThemeMode] = useState(stored.themeMode || 'system');
  const [fontSize, setFontSize] = useState(stored.fontSize || 'medium');
  const [langPref, setLangPref] = useState(stored.langPref || 'all');

  console.log(`[ThemeContext] === INIT STATE === | themeMode="${themeMode}" fontSize="${fontSize}"`);

  const resolvedTheme = themeMode === 'system' ? getSystemTheme() : themeMode;

  const persist = useCallback((key, value) => {
    const prefs = loadPrefs();
    prefs[key] = value;
    savePrefs(prefs);
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', resolvedTheme);
    console.log('[ThemeContext] mount: set data-theme=', resolvedTheme, '| DOM attr=', document.documentElement.getAttribute('data-theme'));
  }, []); // only on mount, sync in callbacks handles changes

  useEffect(() => {
    document.documentElement.setAttribute('data-font-size', fontSize);
    const sizeMap = { small: '12px', medium: '15px', large: '18px' };
    document.documentElement.style.fontSize = sizeMap[fontSize] || '15px';
    console.log('[ThemeContext] mount: set data-font-size=', fontSize, '| html.style.fontSize=', document.documentElement.style.fontSize);
  }, []); // only on mount, sync in callbacks handles changes

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
    console.log('[ThemeContext] updateThemeMode | STEP 1: called with', mode, '| React state fontSize=', fontSize);
    setThemeMode(mode);
    persist('themeMode', mode);
    const resolved = mode === 'system' ? getSystemTheme() : mode;
    document.documentElement.setAttribute('data-theme', resolved);
    console.log('[ThemeContext] updateThemeMode | STEP 2: DOM set data-theme=', resolved, '| verify getAttribute=', document.documentElement.getAttribute('data-theme'));
  }, [persist, fontSize]);

  const updateFontSize = useCallback((size) => {
    console.log('[ThemeContext] updateFontSize | STEP 1: called with', size, '| current DOM attr=', document.documentElement.getAttribute('data-font-size'));
    setFontSize(size);
    persist('fontSize', size);
    // 同步写入 DOM 属性
    document.documentElement.setAttribute('data-font-size', size);
    console.log('[ThemeContext] updateFontSize | STEP 2: DOM set data-font-size=', size, '| verify getAttribute=', document.documentElement.getAttribute('data-font-size'));
    // STEP 3: 直接写 style.fontSize 确保最高优先级
    const sizeMap = { small: '12px', medium: '15px', large: '18px' };
    document.documentElement.style.fontSize = sizeMap[size] || '15px';
    console.log('[ThemeContext] updateFontSize | STEP 3: html.style.fontSize =', document.documentElement.style.fontSize);
    // STEP 4: 验证实际 computed 值
    const check = document.body || document.documentElement;
    const computed = window.getComputedStyle(check).fontSize;
    console.log('[ThemeContext] updateFontSize | STEP 4: body computed font-size:', computed);
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
