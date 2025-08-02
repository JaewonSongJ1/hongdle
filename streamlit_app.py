#!/usr/bin/env python3
"""
홍들 (Hongdle) Streamlit 웹앱
play_hongdle.py의 모든 기능을 웹 인터페이스로 구현
"""

import streamlit as st
import sys
import io
from pathlib import Path

# 페이지 설정
st.set_page_config(
    page_title="홍들 (Hongdle) - 한글 Wordle",
    page_icon="🎯",
    layout="centered"
)

# CSS 스타일링
st.markdown("""
<style>
.main-title {
    text-align: center;
    color: #2E8B57;
    font-size: 3em;
    margin-bottom: 0.2em;
}
.subtitle {
    text-align: center;
    color: #666;
    margin-bottom: 1em;
}
.candidate-button {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 8px;
    margin: 4px 0;
    text-align: center;
    font-size: 12px;
    height: 80px;
}
</style>
""", unsafe_allow_html=True)

def setup_modules():
    """홍들 모듈 import 설정"""
    try:
        # 경로 설정
        current_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
        src_dir = current_dir / 'src'
        
        if not src_dir.exists():
            src_dir = current_dir.parent / 'src'
        
        if not src_dir.exists():
            st.error("❌ src 폴더를 찾을 수 없습니다. 홍들 프로젝트 루트에서 실행해주세요.")
            return False
            
        if str(src_dir) not in sys.path:
            sys.path.append(str(src_dir))
        
        # GameEngine import
        from game_engine import GameEngine
        return True
        
    except ImportError as e:
        st.error(f"❌ GameEngine 모듈 import 실패: {e}")
        return False
    except Exception as e:
        st.error(f"❌ 모듈 설정 오류: {e}")
        return False

def get_database_path(mode):
    """데이터베이스 파일 경로 반환"""
    current_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
    project_root = current_dir if (current_dir / 'data').exists() else current_dir.parent
    
    db_filename = "korean_words.db" if mode == '1' else "korean_words_full.db"
    db_path = project_root / "data" / db_filename
    
    return str(db_path) if db_path.exists() else None

def display_candidates_as_buttons(candidates, max_display=20):
    """후보 단어들을 클릭 가능한 버튼으로 표시 (더 보기 기능 포함)"""
    if len(candidates) == 0:
        return
    
    # 세션 상태에서 현재 표시 개수 관리
    if 'display_count' not in st.session_state:
        st.session_state.display_count = max_display
    
    # 실제 표시할 개수 계산
    current_display = min(st.session_state.display_count, len(candidates))
    
    # 헤더 표시
    if len(candidates) <= max_display:
        st.subheader(f"🎯 후보 단어 ({len(candidates)}개) - 클릭하여 선택")
    else:
        st.subheader(f"🎪 후보 단어 ({current_display}/{len(candidates):,}개) - 클릭하여 선택")
    
    # 4열 그리드로 배치
    cols = st.columns(4)
    for i in range(current_display):
        candidate = candidates[i]
        word = candidate['word']
        jamos = candidate['jamos']
        freq = candidate.get('frequency', 0)
        
        col_idx = i % 4
        with cols[col_idx]:
            if st.button(
                f"**{word}**\n`{' '.join(list(jamos))}`\n빈도: {freq}",
                key=f"candidate_btn_{i}",
                use_container_width=True,
                help=f"클릭하면 '{word}'가 입력창에 자동으로 채워집니다"
            ):
                st.session_state.selected_word = word
                st.rerun()
    
    # "더 보기" 버튼 표시
    if current_display < len(candidates):
        remaining = len(candidates) - current_display
        next_batch = min(20, remaining)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                f"📋 더 보기 (+{next_batch}개)",
                use_container_width=True,
                help=f"다음 {next_batch}개 후보를 추가로 표시합니다"
            ):
                st.session_state.display_count += 20
                st.rerun()
        
        # 진행 상황 표시
        progress = current_display / len(candidates)
        st.progress(progress, text=f"{current_display}/{len(candidates):,}개 표시됨 ({progress:.1%})")
    
    elif len(candidates) > max_display:
        # 모든 후보를 다 보여준 경우
        st.success(f"✅ 모든 {len(candidates):,}개 후보를 표시했습니다!")
        
        # "처음으로" 버튼
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔝 처음 20개만 보기", use_container_width=True):
                st.session_state.display_count = max_display
                st.rerun()

def display_game_history(engine):
    """게임 진행 히스토리 표시"""
    if not engine.turns:
        return
        
    st.subheader("🎮 게임 진행 상황")
    
    for i, turn in enumerate(engine.turns):
        # turn 구조 안전하게 처리
        if hasattr(turn, 'guess_word'):
            word = turn.guess_word
            pattern = turn.pattern
        elif isinstance(turn, dict):
            word = turn.get('guess_word', turn.get('word', 'Unknown'))
            pattern = turn.get('pattern', 'Unknown')
        else:
            word = str(turn)
            pattern = 'Unknown'
        
        jamos = engine.processor.decompose_to_string(word)
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.write(f"**턴 {i+1}**: {word}")
            st.write(f"**패턴**: {pattern}")
        with col2:
            st.write(f"**자모음**: `{' '.join(list(jamos))}`")
        
        st.markdown("---")

def safe_add_turn(engine, word, pattern):
    """터미널 입출력을 완전히 차단하고 안전하게 턴 추가"""
    import builtins
    
    # 원본 함수들 백업
    old_print = builtins.print
    old_input = builtins.input
    old_stdout = sys.stdout
    old_stdin = sys.stdin
    
    try:
        # 모든 출력과 입력을 차단
        builtins.print = lambda *args, **kwargs: None  # print 함수 무효화
        builtins.input = lambda prompt="": ""  # input 함수가 빈 문자열 반환
        sys.stdout = io.StringIO()  # stdout 리다이렉트
        sys.stdin = io.StringIO()   # stdin 리다이렉트
        
        # 턴 추가
        result = engine.add_turn(word, pattern)
        return result
        
    finally:
        # 모든 함수들 복원
        builtins.print = old_print
        builtins.input = old_input
        sys.stdout = old_stdout
        sys.stdin = old_stdin

# === 메인 앱 시작 ===

# 헤더
st.markdown('<h1 class="main-title">🎯 홍들 (Hongdle)</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">한국어 Wordle 누적 게임 - 웹 버전</p>', unsafe_allow_html=True)

# 모듈 설정 확인
if not setup_modules():
    st.stop()

# GameEngine import
from game_engine import GameEngine

# 세션 상태 초기화
if 'game_initialized' not in st.session_state:
    st.session_state.game_initialized = False
if 'engine' not in st.session_state:
    st.session_state.engine = None
if 'selected_word' not in st.session_state:
    st.session_state.selected_word = ''
if 'display_count' not in st.session_state:
    st.session_state.display_count = 20

# 1단계: 게임 모드 선택
if not st.session_state.game_initialized:
    st.subheader("🎮 게임 모드 선택")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📝 기본 모드 (추천)", use_container_width=True):
            db_path = get_database_path('1')
            if db_path:
                st.session_state.mode = '1'
                st.session_state.db_path = db_path
                st.session_state.game_initialized = True
                st.rerun()
            else:
                st.error("❌ korean_words.db 파일을 찾을 수 없습니다.")
                st.info("먼저 `python src/word_database.py`를 실행해주세요.")
    
    with col2:
        if st.button("📚 전체 모드", use_container_width=True):
            db_path = get_database_path('2')
            if db_path:
                st.session_state.mode = '2'
                st.session_state.db_path = db_path
                st.session_state.game_initialized = True
                st.rerun()
            else:
                st.error("❌ korean_words_full.db 파일을 찾을 수 없습니다.")
                st.info("먼저 `python src/word_database.py --full`를 실행해주세요.")
    
    # 게임 설명
    with st.expander("📖 게임 설명"):
        st.markdown("""
        ### 🎯 홍들 게임 방법
        
        **기본 플로우**:
        1. 추측 단어를 입력하거나 후보에서 선택
        2. 각 자모음의 상태에 따라 패턴 입력 (G/Y/B)
        3. 여러 턴을 통해 후보를 1개까지 줄이기
        
        **패턴 설명**:
        - **G (Green)**: 정확한 위치의 정확한 자모음 🟩
        - **Y (Yellow)**: 포함되지만 위치가 틀린 자모음 🟨
        - **B (Black)**: 포함되지 않는 자모음 ⬛
        
        **핵심 규칙**:
        - 한글은 자모음 단위로 분해되어 판단됩니다
        - Y와 B가 함께 나타나면 정확한 개수가 확정됩니다
        
        **모드 차이**:
        - **기본 모드**: 자주 쓰는 단어 (~3만개)
        - **전체 모드**: 모든 단어 포함 (더 많음)
        """)
    
    st.stop()

# 2단계: 게임 엔진 초기화
if st.session_state.engine is None:
    try:
        with st.spinner("게임 엔진 초기화 중..."):
            engine = GameEngine(db_path=st.session_state.db_path)
            st.session_state.engine = engine
            
            # DB 통계 표시
            stats = engine.db.get_statistics()
            mode_name = '기본 모드' if st.session_state.mode == '1' else '전체 모드'
            db_name = Path(st.session_state.db_path).name
            
            st.success(f"✅ {mode_name} ({db_name}) | 총 {stats['total_words']:,}개 단어 로드 완료")
            
    except Exception as e:
        st.error(f"❌ 게임 엔진 초기화 실패: {e}")
        if st.button("🔄 모드 다시 선택"):
            st.session_state.game_initialized = False
            st.session_state.engine = None
            st.rerun()
        st.stop()

engine = st.session_state.engine

# 3단계: 게임 상태 표시
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("현재 턴", len(engine.turns))

with col2:
    candidates = engine.get_current_candidates()
    st.metric("후보 단어", f"{len(candidates):,}개")

with col3:
    mode_name = '기본' if st.session_state.mode == '1' else '전체'
    st.metric("모드", mode_name)

with col4:
    if st.button("🔄 게임 리셋"):
        engine.reset_game()
        # 표시 개수도 리셋
        if 'display_count' in st.session_state:
            st.session_state.display_count = 20
        st.rerun()

# 4단계: 게임 히스토리 표시
display_game_history(engine)

# 5단계: 게임 상태별 처리
if len(candidates) == 1:
    # 정답 발견!
    final_word = candidates[0]['word']
    jamos = engine.processor.decompose_to_string(final_word)
    
    st.balloons()
    st.success(f"🎉 **축하합니다! 정답을 찾았습니다!**")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**정답**: {final_word}")
    with col2:
        st.info(f"**자모음**: `{' '.join(list(jamos))}`")
    
    st.metric("총 턴 수", len(engine.turns))
    
    if st.button("🆕 새 게임 시작", use_container_width=True):
        engine.reset_game()
        # 표시 개수도 리셋
        if 'display_count' in st.session_state:
            st.session_state.display_count = 20
        st.rerun()

else:
    # 게임 진행 중
    
    # 후보 단어를 클릭 가능한 버튼으로 표시
    if len(candidates) > 1:
        display_candidates_as_buttons(candidates, max_display=20)
    
    # 새로운 턴 입력
    st.markdown("---")
    st.subheader(f"✏️ 턴 {len(engine.turns) + 1} 입력")
    
    # 선택된 단어 처리
    default_word = st.session_state.selected_word
    if default_word:
        st.success(f"선택된 단어: **{default_word}**")
        # 사용 후 초기화
        st.session_state.selected_word = ''
    
    # 입력 폼
    with st.form("turn_input_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            user_word = st.text_input(
                "추측 단어",
                value=default_word,
                placeholder="예: 안녕하세요",
                help="한글 단어를 직접 입력하거나 위의 후보에서 선택하세요"
            )
        
        with col2:
            user_pattern = st.text_input(
                "패턴 (G/Y/B)",
                placeholder="예: GYBBY",
                help="G(정확위치), Y(포함/위치틀림), B(미포함)"
            ).upper()
        
        submitted = st.form_submit_button("🎯 턴 실행", use_container_width=True)
        
        if submitted:
            # 입력 검증
            if not user_word.strip() or not user_pattern.strip():
                st.error("❌ 단어와 패턴을 모두 입력해주세요.")
            elif not all(c in 'GYB' for c in user_pattern):
                st.error("❌ 패턴은 G, Y, B만 사용 가능합니다.")
            elif not all('가' <= c <= '힣' for c in user_word.strip()):
                st.error("❌ 한글 단어만 입력 가능합니다.")
            else:
                try:
                    # 자모음 길이 검증
                    word = user_word.strip()
                    pattern = user_pattern.strip()
                    
                    jamos = engine.processor.decompose_to_string(word)
                    
                    if len(jamos) != len(pattern):
                        st.error(f"❌ 자모음 길이({len(jamos)})와 패턴 길이({len(pattern)})가 일치하지 않습니다.")
                        st.info(f"**{word}**의 자모음: `{' '.join(list(jamos))}` ({len(jamos)}개)")
                    else:
                        # 턴 추가 (터미널 입출력 차단)
                        with st.spinner("턴 처리 중..."):
                            new_candidates = safe_add_turn(engine, word, pattern)
                        
                        # 새 턴이므로 표시 개수 리셋
                        st.session_state.display_count = 20
                        
                        st.success(f"✅ 턴이 추가되었습니다! 후보: {len(new_candidates):,}개")
                        st.rerun()
                        
                except ValueError as e:
                    st.error(f"❌ 입력 오류: {e}")
                except Exception as e:
                    st.error(f"❌ 예상치 못한 오류: {e}")
                    # 디버깅용 에러 상세 정보
                    with st.expander("🔧 에러 상세 정보"):
                        import traceback
                        st.code(traceback.format_exc())

# 사이드바 정보
with st.sidebar:
    st.header("📊 게임 정보")
    
    # 현재 상태
    st.write(f"**현재 턴**: {len(engine.turns)}")
    st.write(f"**후보 단어**: {len(candidates):,}개")
    
    # DB 정보
    try:
        stats = engine.db.get_statistics()
        st.write(f"**전체 단어**: {stats['total_words']:,}개")
    except:
        pass
    
    st.markdown("---")
    
    # 턴별 요약
    if engine.turns:
        st.subheader("🎯 턴 요약")
        for i, turn in enumerate(engine.turns):
            if hasattr(turn, 'guess_word'):
                word = turn.guess_word
                pattern = turn.pattern
            elif isinstance(turn, dict):
                word = turn.get('guess_word', turn.get('word', 'Unknown'))
                pattern = turn.get('pattern', 'Unknown')
            else:
                continue
            
            st.write(f"턴 {i+1}: `{word}` → `{pattern}`")
    
    st.markdown("---")
    
    # 게임 컨트롤
    if st.button("🔄 모드 변경"):
        st.session_state.game_initialized = False
        st.session_state.engine = None
        # 표시 개수도 리셋
        if 'display_count' in st.session_state:
            st.session_state.display_count = 20
        st.rerun()
    
    st.markdown("---")
    st.markdown("**Made with ❤️ using Streamlit**")
    st.markdown("[GitHub](https://github.com/JaewonSongJ1/hongdle)")