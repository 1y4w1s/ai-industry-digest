import os, fnmatch

root = 'D:\\MyPrograms\\ai-industry-digest\\frontend\\src'

# 4a: ArticleCard padding 10px->12px
path = os.path.join(root, 'components', 'ArticleCard.jsx')
text = open(path, 'r', encoding='utf8').read()
text = text.replace("padding: '10px 0',", "padding: '12px 0',")
open(path, 'w', encoding='utf8').write(text)
print('4a OK')

# 4b: FilterBar buttons padding
# 4c: share/link buttons min-height
# These are in multiple files, let's do the most common pattern
for dirpath, dirs, files in os.walk(root):
    for f in files:
        if f.endswith('.jsx'):
            fpath = os.path.join(dirpath, f)
            text = open(fpath, 'r', encoding='utf8').read()
            changed = False
            # Find buttons with padding less than 6px and increase them
            # Replace common small padding patterns
            for old, new in [
                ("padding: '4px 10px'", "padding: '8px 12px'"),
                ("padding: '4px 12px'", "padding: '8px 14px'"),
                ("padding: '6px 8px'", "padding: '8px 10px'"),
                ("padding: '6px 12px'", "padding: '8px 14px'"),
                ("padding: '4px 8px'", "padding: '8px 10px'"),
                ("padding: '2px 4px'", "padding: '6px 8px'"),
                ("padding: 0,", "padding: '6px 8px',"),
            ]:
                if old in text:
                    text = text.replace(old, new)
                    changed = True
            if changed:
                open(fpath, 'w', encoding='utf8').write(text)
                print(f'  Updated: {fpath}')

print('Done')
