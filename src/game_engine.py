"""
한국어 Wordle (홍들) 게임 엔진

핵심 규칙:
* 자음은 'ㄱ,ㄴ,ㄷ,ㄹ,ㅁ,ㅂ,ㅅ,ㅇ,ㅈ,ㅊ,ㅋ,ㅌ,ㅍ,ㅎ' 만 사용
* 모음은 'ㅏ,ㅑ,ㅓ,ㅕ,ㅗ,ㅛ,ㅜ,ㅠ,ㅡ,ㅣ' 만 사용
* 겹자음, 쌍자음은 자음 2개 조합으로 생성
* 겹모음은 모음 2개 조합으로 생성
* 등장하지 않는 자모음은 검정색 B
* 등장하되 위치가 틀린 자모음은 노란색 Y
* 등장하고 위치까지 맞은 자모음은 초록색 G

중요한 B(검정) 규칙:
* 다만, 등장하지 않는 자모음은 주의해야 할 것이 검정색 B라고 되어 있다고 해도 무조건 후보군에서 배제해서는 안됨.
* 만약, '국군' (ㄱ,ㅜ,ㄱ,ㄱ,ㅜ,ㄴ) 이라는 단어가 YBBBBBY 일 경우, 
  첫 번째 ㄱ은 Y 이고 3,4번째 ㄱ은 B 이므로, ㄱ이 B에 포함되어 있다고 해서 
  무조건 등장하지 않는다는 것이 아니라 Y인 ㄱ이 한 개 있으므로 ㄱ은 한 번만 등장한다는 것
* 이렇게 Y에 포함되어 있는 경우를 제외한다면, B로 표시된 자모음은 무조건 그 단어에는 
  등장하지 않는다는 것을 의미하므로 로직을 짤 때 참고
"""

import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple
from collections import Counter

# 같은 폴더의 모듈들 import
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from word_processor import WordProcessor
from word_database import WordDatabase

class GameEngine:
    """한국어 Wordle 게임 엔진 - 간소화된 누적 조건 전용"""
    
    def __init__(self, db_path: str, fallback_db_path: str = None):
        """게임 엔진 초기화"""
        self.processor = WordProcessor()

        if not Path(db_path).exists():
            raise FileNotFoundError(f"주 데이터베이스를 찾을 수 없습니다: {db_path}")
        self.db = WordDatabase(db_path)
        # print(f"[INFO] 주 DB가 설정되었습니다: {db_path}") # play_hongdle.py에서 이미 안내하므로 주석 처리

        self.db_fallback = None
        if fallback_db_path:
            if Path(fallback_db_path).exists():
                self.db_fallback = WordDatabase(fallback_db_path)
                # print(f"[INFO] 폴백(Fallback) DB가 설정되었습니다: {fallback_db_path}")
            else:
                # 폴백 DB는 필수가 아니므로 경고만 출력합니다.
                print(f"[WARNING] 폴백(Fallback) DB를 찾을 수 없습니다: {fallback_db_path}")

        self.reset_game()
    
    def reset_game(self):
        """게임 초기화"""
        self.turns = []  # 모든 턴 기록
        self.word_length = None  # 게임 단어 길이
        
        # 조건들
        self.green_positions = {}  # {위치: 자모음} - 확정된 위치
        self.yellow_jamos = set()  # 포함되어야 하는 자모음들
        self.yellow_excluded_positions = {}  # {자모음: [제외위치들]}
        self.black_positions = {}  # {위치: 자모음} - 특정 위치에서 제외된 자모음들
        self.pure_black_jamos = set()  # 완전히 등장하지 않는 자모음들 (Y에 없는 B)
        self.jamo_exact_counts = {}  # {자모음: 정확한개수} - Y+B 조합으로 확정된 개수
    
    def add_turn(self, guess_word: str, result_pattern: str) -> List[str]:
        """
        새로운 턴 추가
        
        Args:
            guess_word: 추측 단어 ('세제')
            result_pattern: 결과 패턴 ('GYBBBG')
            
        Returns:
            현재 조건에 맞는 후보 단어들
        """
        # 자모음 분해
        jamos = self.processor.decompose_hangul(guess_word)
        
        # 길이 확인
        if self.word_length is None:
            self.word_length = len(jamos)
        elif self.word_length != len(jamos):
            raise ValueError(f"단어 길이 불일치: {len(jamos)} != {self.word_length}")
        
        if len(jamos) != len(result_pattern):
            raise ValueError(f"자모음 개수와 패턴 길이 불일치: {len(jamos)} != {len(result_pattern)}")
        
        # 턴 정보 저장
        turn_info = {
            'turn': len(self.turns) + 1,
            'word': guess_word,
            'jamos': jamos,
            'pattern': result_pattern
        }
        self.turns.append(turn_info)
        
        # 조건 업데이트
        self._update_conditions(jamos, result_pattern)
        
        # 분석 출력
        self._print_turn_analysis(turn_info)
        
        # 후보 찾기
        candidates = self._find_candidates()
        
        # 결과 출력
        self._print_candidates(candidates)
        
        return candidates
    
    def _update_conditions(self, jamos: List[str], pattern: str):
        """조건 업데이트 - 위치별 제외 조건 추가"""
        
        # 1단계: 기본 조건 수집
        for i, (jamo, result) in enumerate(zip(jamos, pattern)):
            if result == 'G':
                self.green_positions[i] = jamo
                
            elif result == 'Y':
                self.yellow_jamos.add(jamo)
                if jamo not in self.yellow_excluded_positions:
                    self.yellow_excluded_positions[jamo] = []
                self.yellow_excluded_positions[jamo].append(i)
            
            elif result == 'B':
                # B로 판명된 위치에 해당 자모음이 올 수 없음 (핵심!)
                if i not in self.black_positions:
                    self.black_positions[i] = set()
                self.black_positions[i].add(jamo)
        
        # 2단계: 고급 개수 분석 (핵심!)
        jamo_counts = Counter(jamos)
        jamo_results = {}
        
        # 각 자모음별로 G, Y, B 개수 집계
        for i, (jamo, result) in enumerate(zip(jamos, pattern)):
            if jamo not in jamo_results:
                jamo_results[jamo] = {'G': 0, 'Y': 0, 'B': 0}
            jamo_results[jamo][result] += 1
        
        # 3단계: 각 자모음별 규칙 적용
        for jamo, results in jamo_results.items():
            g_count = results['G']
            y_count = results['Y']
            b_count = results['B']
            
            if y_count > 0 or g_count > 0:
                # Y나 G가 있는 경우
                if b_count > 0:
                    # Y/G와 B가 동시에 있는 경우 = 정확한 개수 확정
                    exact_count = g_count + y_count
                    self.jamo_exact_counts[jamo] = exact_count
                    print(f"🎯 {jamo}: 정확히 {exact_count}개 (G:{g_count} + Y:{y_count}, B:{b_count})")
                else:
                    # Y/G만 있는 경우 = 최소 이만큼 존재
                    min_count = g_count + y_count
                    if jamo in self.jamo_exact_counts:
                        # 이미 정확한 개수가 있으면 더 엄격한 것 선택
                        self.jamo_exact_counts[jamo] = max(self.jamo_exact_counts[jamo], min_count)
                    # 정확한 개수가 없으면 일단 기록하지 않음 (나중에 더 정확한 정보가 올 수 있음)
            
            elif b_count > 0:
                # B만 있는 경우 = 완전히 등장하지 않음
                self.pure_black_jamos.add(jamo)
                print(f"❌ {jamo}: 완전히 등장하지 않음")
    
    def _find_candidates(self) -> List[str]:
        """현재 조건에 맞는 후보 단어들 찾기"""
        # 1. 주 DB에서 검색
        all_words_primary = self.db.get_words_by_length(self.word_length)
        candidates = []
        
        for word_info in all_words_primary:
            word = word_info['word']
            jamos = list(word_info['jamos'])
            
            if self._check_word_conditions(jamos):
                candidates.append(word)
        
        # 2. 주 DB에서 후보를 찾았거나, 폴백 DB가 없으면 결과 반환
        if candidates or not self.db_fallback:
            return candidates

        # 3. 주 DB에 후보가 없고 폴백 DB가 있으면, 폴백 DB에서 검색
        print("\n[ℹ️  기본 DB에 후보가 없어 전체 DB에서 검색합니다...]")
        all_words_fallback = self.db_fallback.get_words_by_length(self.word_length)
        for word_info in all_words_fallback:
            word = word_info['word']
            jamos = list(word_info['jamos'])
            if self._check_word_conditions(jamos):
                candidates.append(word)
        
        return candidates
    
    def _check_word_conditions(self, jamos_list: List[str]) -> bool:
        """단어가 모든 조건을 만족하는지 확인"""
        
        # 1. Green 조건 확인 (정확한 위치)
        for pos, jamo in self.green_positions.items():
            if pos >= len(jamos_list) or jamos_list[pos] != jamo:
                return False
        
        # 2. Black 위치 조건 확인 (핵심 추가!)
        for pos, excluded_jamos in self.black_positions.items():
            if pos < len(jamos_list) and jamos_list[pos] in excluded_jamos:
                return False
        
        # 3. Pure Black 조건 확인 (완전히 등장하지 않는 자모음)
        for black_jamo in self.pure_black_jamos:
            if black_jamo in jamos_list:
                return False
        
        # 4. Yellow 조건 확인 (포함되어야 함)
        for yellow_jamo in self.yellow_jamos:
            if yellow_jamo not in jamos_list:
                return False
        
        # 5. Yellow 제외 위치 확인
        for yellow_jamo, excluded_positions in self.yellow_excluded_positions.items():
            for pos in excluded_positions:
                if pos < len(jamos_list) and jamos_list[pos] == yellow_jamo:
                    return False
        
        # 6. 정확한 개수 확인 (핵심!)
        jamo_counts = Counter(jamos_list)
        for jamo, exact_count in self.jamo_exact_counts.items():
            if jamo_counts[jamo] != exact_count:
                return False
        
        return True
    
    def _print_turn_analysis(self, turn_info: Dict):
        """턴 분석 결과 출력"""
        print(f"\n=== 턴 {turn_info['turn']} 분석 ===")
        print(f"단어: {turn_info['word']}")
        print(f"자모음: {' '.join(turn_info['jamos'])}")
        print(f"패턴: {turn_info['pattern']}")
        
        print(f"\n=== 누적 조건 ===")
        print(f"확정 위치(G): {self.green_positions}")
        print(f"포함 필수(Y): {self.yellow_jamos}")
        print(f"Y 제외 위치: {self.yellow_excluded_positions}")
        print(f"B 제외 위치: {self._format_black_positions()}")
        print(f"완전 제외(B): {self.pure_black_jamos}")
        if self.jamo_exact_counts:
            print(f"정확한 개수: {self.jamo_exact_counts}")
    
    def _format_black_positions(self) -> str:
        """B 위치 제외 조건을 읽기 쉽게 포맷"""
        if not self.black_positions:
            return "{}"
        
        formatted = []
        for pos, jamos in self.black_positions.items():
            jamos_str = ','.join(sorted(jamos))
            formatted.append(f"위치{pos}:[{jamos_str}]")
        return "{" + ", ".join(formatted) + "}"
    
    def _print_candidates(self, candidates: List[str]):
        """후보 단어들 출력"""
        print(f"\n=== 후보 단어들 ({len(candidates)}개) ===")
        
        if not candidates:
            print("❌ 조건에 맞는 단어가 없습니다!")
            return
        
        # 20개씩 나누어 출력
        for i in range(0, len(candidates), 20):
            batch = candidates[i:i+20]
            print(f"\n[ {i+1}-{i+len(batch)} ]")
            for j, word in enumerate(batch):
                jamos = self.processor.decompose_to_string(word)
                jamos_display = ' '.join(list(jamos))
                print(f"{i+j+1:3d}. {word:<8} -> {jamos_display}")
            
            if i + 20 < len(candidates):
                input("계속하려면 Enter를 누르세요...")
    
    def show_game_summary(self):
        """게임 진행 상황 요약"""
        print(f"\n{'='*60}")
        print(f"🎮 게임 진행 상황")
        print(f"{'='*60}")
        
        if not self.turns:
            print("아직 시작되지 않았습니다.")
            return
        
        print(f"단어 길이: {self.word_length}자모음")
        print(f"진행 턴: {len(self.turns)}턴")
        
        print(f"\n턴별 기록:")
        for turn_info in self.turns:
            turn = turn_info['turn']
            word = turn_info['word']
            pattern = turn_info['pattern']
            print(f"  턴 {turn}: {word} → {pattern}")
        
        print(f"\n현재 조건:")
        print(f"  확정된 위치: {self.green_positions}")
        print(f"  포함되어야 함: {self.yellow_jamos}")
        print(f"  완전히 제외: {self.pure_black_jamos}")
        if self.jamo_exact_counts:
            print(f"  정확한 개수: {self.jamo_exact_counts}")
        
        # 현재 후보 수
        candidates = self._find_candidates()
        print(f"  현재 후보: {len(candidates)}개")
    
    def get_current_candidates(self) -> List[str]:
        """현재 후보 단어들 반환"""
        if not self.word_length:
            return []
        return self._find_candidates()

# 테스트 실행
if __name__ == "__main__":
    print("=" * 60)
    print("🎮 한국어 Wordle 게임 엔진 (새 버전)")
    print("=" * 60)
    
    # 게임 엔진 초기화
    # 테스트를 위해 경로를 직접 지정합니다. 실제 플레이는 play_hongdle.py를 사용하세요.
    project_root = Path(__file__).parent.parent
    db_path = str(project_root / 'data' / 'korean_words_full.db') # 테스트용 기본 DB
    engine = GameEngine(db_path=db_path)
    
    # DB 상태 확인
    stats = engine.db.get_statistics()
    print(f"테스트 데이터베이스: 총 {stats['total_words']:,}개 단어")
    
    if stats['total_words'] == 0:
        print("❌ 데이터베이스가 비어있습니다.")
        sys.exit()
    
    print("\n[ 테스트: 핵심 버그 수정 확인 ]")
    print("-" * 40)
    
    # 테스트 1: 세제 GYBBBG
    print("테스트 1: 세제 GYBBBG")
    candidates1 = engine.add_turn('세제', 'GYBBBG')
    print(f"후보 개수: {len(candidates1)}개")
    
    # 새 게임으로 테스트 2
    engine.reset_game()
    print("\n테스트 2: 실세 GBBBYG")
    candidates2 = engine.add_turn('실세', 'GBBBYG')
    print(f"후보 개수: {len(candidates2)}개")
    
    # 복합 테스트
    engine.reset_game()
    print("\n테스트 3: 복합 테스트")
    engine.add_turn('세제', 'GYBBBG')
    candidates3 = engine.add_turn('실세', 'GBBBYG')
    
    engine.show_game_summary()
    
    print("\n✅ 새 버전 테스트 완료!")