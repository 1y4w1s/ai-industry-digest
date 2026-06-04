import os
import json
from supabase import create_client

def main():
    url = os.environ['SUPABASE_URL']
    key = os.environ['SUPABASE_KEY']
    client = create_client(url, key)

    arts = client.table('articles').select('*').execute()
    with open('backup_articles.json', 'w', encoding='utf-8') as f:
        json.dump(arts.data, f, ensure_ascii=False, default=str)
    print(f'Exported {len(arts.data)} articles')

if __name__ == '__main__':
    main()
