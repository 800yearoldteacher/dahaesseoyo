# 다했어요판 점검 도구 (dev)

실제 Firebase 대신 브라우저 안에서 돌아가는 **연습용 기록장**으로 교사 화면과 태블릿을 함께 띄워, 주요 흐름을 자동으로 점검합니다. 학생 이름이나 선생님 계정 같은 개인정보는 들어 있지 않습니다.

## 들어 있는 것
- `mock/`: 연습용 Firebase (보안 규칙과 같은 판단을 자바스크립트로 옮긴 것 포함)
- `tests/`: 점검 묶음 4개 (기본 흐름 31, 교사 기능 16, 판별 명단·매일 반복·기록 달력 36, 규칙 미게시 대비 4)
- `run-tests.sh`: 한 번에 돌리는 스크립트

## 쓰는 법 (Claude 작업 공간에서)
```bash
git clone --depth 1 https://github.com/800yearoldteacher/dahaesseoyo.git /home/claude/repo
bash /home/claude/repo/dev/run-tests.sh                      # GitHub에 올라간 index.html 점검
bash /home/claude/repo/dev/run-tests.sh /home/claude/work/index.html   # 고친 파일 점검
```
Playwright(파이썬)와 크로미움이 필요합니다. 새 기능을 넣으면 `tests/`에 점검을 더하고, 보안 규칙을 바꾸면 `mock/core.js`의 판단도 함께 고칩니다.
