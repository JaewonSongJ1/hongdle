# 홍들 (Hongdle) - 한국어 Wordle

한국어 자모음 기반 Wordle 게임 엔진

## 기능
- 한글 자모음 완전 분해 (복합 모음, 쌍자음, 자음군)
- Wordle 게임 로직 (B/Y/G 패턴 분석)
- 최적 시작 단어 추천
- SQLite 기반 단어 데이터베이스

## 설치 및 실행
```bash
pip install -r requirements.txt
python misc/play_hongdle.py