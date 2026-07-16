import { useState, useRef, useCallback, useEffect } from 'react';

function getSS() {
  return typeof window !== 'undefined' && window.speechSynthesis ? window.speechSynthesis : null;
}

/**
 * useTTS — 语音朗读 hook
 * 支持 speak/pause/resume/stop，自动切分中文文本为按句朗读
 */
export default function useTTS() {
  const [state, setState] = useState('idle');
  const utteranceRef = useRef(null);
  const textChunksRef = useRef([]);
  const chunkIdxRef = useRef(0);

  const stop = useCallback(() => {
    const ss = getSS();
    if (ss) ss.cancel();
    utteranceRef.current = null;
    textChunksRef.current = [];
    chunkIdxRef.current = 0;
    setState('idle');
  }, []);

  useEffect(() => {
    return () => { const ss = getSS(); if (ss) ss.cancel(); };
  }, []);

  const speak = useCallback((text) => {
    const ss = getSS();
    if (!ss || !text) return;
    ss.cancel();
    const chunks = [];
    let current = '';
    for (const char of text) {
      current += char;
      if (current.length > 150 && /[。！？\n.!?]/.test(char)) {
        chunks.push(current.trim());
        current = '';
      }
    }
    if (current.trim()) chunks.push(current.trim());
    textChunksRef.current = chunks;
    chunkIdxRef.current = 0;

    const speakChunk = (idx) => {
      if (idx >= chunks.length) { setState('idle'); return; }
      const utt = new SpeechSynthesisUtterance(chunks[idx]);
      utt.lang = 'zh-CN';
      utt.rate = 1.0;
      utt.pitch = 1.0;
      const voices = ss.getVoices();
      const zhVoice = voices.find((v) => v.lang.startsWith('zh'));
      if (zhVoice) utt.voice = zhVoice;
      utt.onend = () => { chunkIdxRef.current = idx + 1; speakChunk(idx + 1); };
      utt.onerror = () => setState('idle');
      utteranceRef.current = utt;
      ss.speak(utt);
      setState('playing');
    };

    if (ss.getVoices().length === 0) {
      ss.onvoiceschanged = () => speakChunk(0);
    } else {
      speakChunk(0);
    }
  }, []);

  const pause = useCallback(() => { const ss = getSS(); if (ss) ss.pause(); setState('paused'); }, []);
  const resume = useCallback(() => { const ss = getSS(); if (ss) ss.resume(); setState('playing'); }, []);

  const toggle = useCallback((text) => {
    if (state === 'idle') { speak(text); }
    else if (state === 'playing') { pause(); }
    else if (state === 'paused') { resume(); }
  }, [state, speak, pause, resume]);

  return { state, toggle, stop };
}
