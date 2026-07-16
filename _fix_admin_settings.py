# -*- coding: utf-8 -*-
import os

pages_dir = 'D:\\MyPrograms\\ai-industry-digest\\frontend\\src\\pages'

# === SettingsPage: add page header with gold gradient ===
path = os.path.join(pages_dir, 'SettingsPage.jsx')
text = open(path, 'r', encoding='utf8').read()
old_header = '''    <div className="flex-1 overflow-y-auto">
        <div className="px-5 lg:px-6" style={{ paddingTop: '28px', paddingBottom: '32px', maxWidth: '520px', margin: '0 auto' }}>'''
new_header = '''    <div className="flex-1 overflow-y-auto">
        <div className="px-5 lg:px-6" style={{ paddingTop: '28px', paddingBottom: '32px', maxWidth: '800px', margin: '0 auto' }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 20 }}>
            <h1 style={{ fontFamily: "var(--font-display)", fontSize: '20px', fontWeight: 700, color: 'var(--color-text-title)' }}>设置</h1>
            <span style={{ flex: 1, height: '1px', background: 'linear-gradient(90deg, var(--color-brass) 0%, var(--color-border-light) 100%)' }} />
          </div>'''
if old_header in text:
    text = text.replace(old_header, new_header)
    open(path, 'w', encoding='utf8').write(text)
    print('SettingsPage: gold header added')
else:
    print('SettingsPage: header pattern not found')

# === AdminDashboard: redesign cards with gold/ink tokens ===
path = os.path.join(pages_dir, 'AdminDashboard.jsx')
text = open(path, 'r', encoding='utf8').read()

replacements = [
    ('bg-white rounded-xl p-6 shadow-sm border', 'rounded-xl p-6'),
    ('className="p-3 rounded-lg', 'style={{ background: "var(--color-brass-bg)" }} className="p-3 rounded-lg'),
    ('text-gray-500', 'text-muted'),
    ('text-gray-400', 'text-label'),
    ('text-blue-500', 'text-brass'),
    ('bg-blue-100', 'bg-brass-bg'),
    ('text-lg font-semibold', 'font-semibold'),
]

for old, new in replacements:
    if old in text:
        text = text.replace(old, new)
        print(f'AdminDashboard: replaced "{old[:30]}"')

# Add page-specific style
old_import = "import { BarChart3, Users, FileText, Bookmark, TrendingUp, Activity } from 'lucide-react';"
new_import = """import { BarChart3, Users, FileText, Bookmark, TrendingUp, Activity } from 'lucide-react';

const cardStyle = {
  background: 'var(--color-bg-off)',
  padding: '20px',
  borderRadius: '12px',
};

const statValueStyle = {
  fontSize: '28px',
  fontWeight: 700,
  color: 'var(--color-text-title)',
};

const statLabelStyle = {
  fontSize: '12px',
  color: 'var(--color-text-muted)',
  marginTop: 2,
};"""

if old_import in text:
    text = text.replace(old_import, new_import)
    print('AdminDashboard: card styles added')
else:
    print('AdminDashboard: import pattern not found')

open(path, 'w', encoding='utf8').write(text)
print('AdminDashboard: done')
