#!/usr/bin/env bash
# 다했어요판 자동 점검 (연습용 기록장 사용, 실제 Firebase에는 접속하지 않음)
# 사용법: bash dev/run-tests.sh [점검할 index.html 경로]
#   경로를 비우면 GitHub에 올라가 있는 index.html을 받아서 점검합니다.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
TARGET="${1:-}"
mkdir -p /home/claude/fb/mock /home/claude/serve /home/claude/shots
if [ -z "$TARGET" ]; then
  curl -sf -o /home/claude/serve/index.html https://raw.githubusercontent.com/800yearoldteacher/dahaesseoyo/main/index.html
else
  cp "$TARGET" /home/claude/serve/index.html
fi
echo "점검 대상 버전: $(grep -o "APP_VERSION = '[^']*'" /home/claude/serve/index.html | head -1)"
for f in app auth firestore; do cat "$HERE/mock/core.js" "$HERE/mock/$f.js" > "/home/claude/fb/mock/served-$f.js"; done
cp "$HERE"/tests/*.py /home/claude/fb/
curl -s -o /dev/null http://localhost:8000/index.html || { (cd /home/claude/serve && setsid nohup python3 -m http.server 8000 > /tmp/http.log 2>&1 &); sleep 1; }
cd /home/claude/fb
for t in test_fb.py test_fb2.py test_fb3.py test_fb4.py; do
  echo "=== $t ==="
  timeout 300 python3 "$t" 2>&1 | grep -E "^FAIL|통과|pageerror" || true
done
