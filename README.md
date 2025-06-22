# 홍들 (Hongdle) 🇰🇷

<div align="center">

![Korean Wordle](https://img.shields.io/badge/Korean-Wordle-red?style=for-the-badge&logo=gamepad)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Cross--platform-lightgrey?style=for-the-badge)

**한국어 자모음 기반 Wordle 게임 엔진**

*Wordle meets Korean linguistics - 한글의 아름다운 구조를 게임으로!*

</div>

---

## 🎯 Introduction

**홍들(Hongdle)**은 인기 있는 영어 Wordle 게임을 한국어로 구현한 프로젝트입니다. 단순한 번역이 아닌, **한글의 고유한 자모음 분해 시스템**을 활용하여 더욱 정교하고 흥미로운 게임 경험을 제공합니다.

### ✨ 주요 특징

- 🔤 **완전한 한글 자모음 분해**: 복합 모음(ㅐ→ㅏ+ㅣ), 쌍자음(ㄲ→ㄱ+ㄱ), 자음군(ㄳ→ㄱ+ㅅ) 완벽 지원
- 🎮 **고급 게임 로직**: Y+B 조합으로 자모음 개수 확정, 위치별 제외 조건 등
- 💾 **SQLite 기반 DB**: 10만+ 한국어 단어 데이터베이스
- 🚀 **Zero Dependencies**: Python 표준 라이브러리만 사용
- 🎯 **최적 시작 단어**: 데이터 분석 기반 추천 단어 목록

### 🎲 게임 규칙

| 색상 | 의미 | 설명 |
|------|------|------|
| 🟩 **G**reen | 정확! | 자모음이 정확한 위치에 있음 |
| 🟨 **Y**ellow | 포함되지만 위치 틀림 | 단어에 포함되지만 다른 위치에 있음 |
| ⬛ **B**lack | 없음 | 해당 자모음이 단어에 없음 |

**핵심 규칙**: Y와 B가 같은 자모음에 대해 동시에 나타나면, 그 자모음의 **정확한 개수**가 확정됩니다!

---

## 📁 Project Structure

```
hongdle/
│
├── 📂 data/                     # 데이터 파일들
│   ├── korean_words_clean.txt       # 한국어 단어 원본 (구버전)
│   ├── korean_words_clean_v2.txt    # 한국어 단어 데이터셋 ⭐ (현재 사용)
│   ├── korean_words.db              # 자모음 분해 SQLite 데이터베이스
│   ├── optimal_words_5jamos.txt     # 5자모음 최적 시작 단어
│   ├── optimal_words_6jamos.txt     # 6자모음 최적 시작 단어
│   └── optimal_words_7jamos.txt     # 7자모음 최적 시작 단어
│
├── 📂 misc/                     # 유틸리티 스크립트들
│   ├── excel_converter.py          # 엑셀 → TXT 변환기
│   ├── optimal_word_finder.py      # 최적 시작 단어 추출기
│   ├── play_hongdle.py            # 🎮 게임 플레이어 (메인)
│   └── word_list_cleanup.py        # 단어 목록 정리 도구
│
├── 📂 src/                      # 핵심 엔진 코드
│   ├── word_processor.py           # 한글 자모음 분해 엔진
│   ├── word_database.py            # SQLite 데이터베이스 관리
│   └── game_engine.py              # 홍들 게임 로직 엔진
│
└── 📄 requirements.txt          # 의존성 (빈 파일)
```

### 📊 데이터 설명

- **korean_words_clean_v2.txt**: 약 10만개의 한국어 단어 데이터셋 (현재 사용 중)
- **korean_words.db**: 자모음 분해된 단어들의 SQLite 데이터베이스
- **optimal_words_Njamos.txt**: 각 길이별 최적 시작 단어 목록
  - ⚠️ **업데이트 예정**: 현재 사용빈도가 낮은 단어들이 많이 포함되어 있음

---

## 🚀 Installation

홍들은 **Python 표준 라이브러리만** 사용하므로 별도의 설치 과정이 필요하지 않습니다!

### 📋 요구사항

- **Python 3.8+** (pathlib, typing 안정 지원)
- **운영체제**: Windows, macOS, Linux 모두 지원

### 💾 설치 방법

```bash
# 1. 저장소 클론
git clone https://github.com/JaewonSongJ1/hongdle.git

# 2. 프로젝트 폴더로 이동
cd hongdle

# 3. 바로 실행! (설치 끝)
python misc/play_hongdle.py
```

---

## 🎮 Usage

### 기본 게임 플레이

```bash
python misc/play_hongdle.py
```

게임을 시작하면 다음과 같은 인터페이스가 나타납니다:

```
🎮 한국어 Wordle (홍들)
==================================================
📋 입력 형식: 단어 패턴
   예시: 세제 GYBBBG

🎨 패턴 설명:
   B(Black): 등장하지 않음
   Y(Yellow): 등장하지만 위치 틀림
   G(Green): 등장하고 위치 정확

💡 핵심 규칙:
   - Y와 B가 같이 나타나면 정확한 개수가 확정됩니다
   - 예: ㅓ가 Y 1개 + B 1개 = ㅓ는 정확히 1개만 존재
```

### 🎯 게임 플레이 예시

```
✏️  입력 (단어 패턴): 세제 GYBBBG

🎯 ㅓ: 정확히 1개 (G:0 + Y:1, B:1)
🎯 ㅣ: 정확히 1개 (G:1 + Y:0, B:1)
❌ ㅈ: 완전히 등장하지 않음

=== 누적 조건 ===
확정 위치(G): {0: 'ㅅ', 5: 'ㅣ'}
포함 필수(Y): {'ㅓ'}
Y 제외 위치: {'ㅓ': [1]}
B 제외 위치: {위치2:[ㅣ], 위치3:[ㅈ], 위치4:[ㅓ]}
완전 제외(B): {'ㅈ'}
정확한 개수: {'ㅓ': 1, 'ㅣ': 1}

=== 후보 단어들 (14개) ===
📊 현재 후보: 14개
```

### 🔧 개발자 도구

#### 데이터베이스 구축/업데이트
```bash
python src/word_database.py
```

#### 최적 시작 단어 찾기
```bash
python misc/optimal_word_finder.py
```

#### 단어 목록 정리
```bash
python misc/word_list_cleanup.py
```

---

## 🛠️ Customization

### 새로운 단어 추가하기

1. **데이터 파일 수정**
   ```bash
   # data/korean_words_clean_v2.txt 파일을 열고
   # 원하는 단어를 한 줄에 하나씩 추가
   echo "새단어" >> data/korean_words_clean_v2.txt
   ```

2. **데이터베이스 업데이트**
   ```bash
   python src/word_database.py
   ```

3. **확인**
   ```bash
   python misc/play_hongdle.py
   # 새로 추가한 단어로 게임 플레이 가능!
   ```

### 게임 로직 커스터마이징

- **src/game_engine.py**: 게임 규칙 수정
- **src/word_processor.py**: 자모음 분해 로직 수정
- **misc/play_hongdle.py**: 게임 인터페이스 수정

---

## 🔬 Technical Details

### 한글 자모음 분해 시스템

홍들은 한글의 복잡한 구조를 완벽하게 처리합니다:

```python
# 예시: '깎는' 단어 분해
'깎는' → ['ㄱ', 'ㄱ', 'ㅏ', 'ㄱ', 'ㄴ', 'ㅡ', 'ㄴ']

# 분해 규칙:
- 쌍자음: ㄲ → ㄱ + ㄱ
- 복합모음: ㅐ → ㅏ + ㅣ  
- 자음군: ㄳ → ㄱ + ㅅ
```

### 고급 게임 로직

```python
# Y+B 조합으로 정확한 개수 확정
세제 GYBBBG → ㅅ ㅓ ㅣ ㅈ ㅓ ㅣ
# ㅓ: 위치 1(Y) + 위치 4(B) = 정확히 1개
# ㅣ: 위치 2(B) + 위치 5(G) = 정확히 1개
```

---

## 🎯 Roadmap

- [ ] **데이터 품질 개선**: 사용빈도 낮은 단어 제거
- [ ] **웹 인터페이스**: Flask 기반 웹 버전
- [ ] **AI 도우미**: 최적 전략 제안 기능
- [ ] **통계 시스템**: 게임 기록 및 분석
- [ ] **멀티플레이어**: 실시간 대전 모드

---

## 📄 License

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

---

## 🤝 Contributing

홍들 프로젝트에 기여해주세요! 

- 🐛 **버그 리포트**: Issues 탭에서 버그를 신고해주세요
- 💡 **기능 제안**: 새로운 아이디어를 공유해주세요  
- 🔧 **코드 기여**: Pull Request를 보내주세요
- 📖 **문서 개선**: README나 주석 개선에 참여해주세요

---

<div align="center">

**즐거운 홍들 라이프! 🎮🇰🇷**

*Made with ❤️ for Korean word game lovers*

[![GitHub stars](https://img.shields.io/github/stars/JaewonSongJ1/hongdle?style=social)](https://github.com/JaewonSongJ1/hongdle)
[![GitHub forks](https://img.shields.io/github/forks/JaewonSongJ1/hongdle?style=social)](https://github.com/JaewonSongJ1/hongdle)

</div>