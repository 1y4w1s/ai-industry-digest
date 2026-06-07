#!/bin/bash

curl -X POST "https://vobpkdrujixghvttgkuq.supabase.co/rest/v1/rpc/execute_sql" \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZvYnBrZHJ1aml4Z2h2dHRna3VxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MDQ4Mjg3MiwiZXhwIjoyMDk2MDU4ODcyfQ.fHqbH-1qytRby_hF_YfNqhIEvWQxkLXCNKVmB2U5F5A" \
  -H "Content-Type: application/json" \
  -d '{"sql": "ALTER TABLE reading_history ADD COLUMN IF NOT EXISTS read_percent double precision"}'

echo ""
echo "---"

curl -X POST "https://vobpkdrujixghvttgkuq.supabase.co/rest/v1/rpc/execute_sql" \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZvYnBrZHJ1aml4Z2h2dHRna3VxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MDQ4Mjg3MiwiZXhwIjoyMDk2MDU4ODcyfQ.fHqbH-1qytRby_hF_YfNqhIEvWQxkLXCNKVmB2U5F5A" \
  -H "Content-Type: application/json" \
  -d '{"sql": "ALTER TABLE reading_history ADD COLUMN IF NOT EXISTS duration_sec integer"}'

echo ""
echo "迁移完成！"
