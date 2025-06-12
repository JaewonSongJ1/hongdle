import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple

# 같은 폴더의 모듈들 import
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from word_processor import WordProcessor
from word_database import WordDatabase

class GameEngine:
    """한국어 Wordle 게임 엔진 - 누적 조건 지원"""
    
    def __init__(self, db_path: str = None):
        """게임 엔진 초기화"""
        self.processor = WordProcessor()
        self.db = WordDatabase(db_path) if db_path else WordDatabase()
        self.reset_game()
    
    def reset_game(self):
        """게임 초기화"""
        self.turns = []  # 모든 턴 기록
        self.word_length = None  # 게임 단어 길이
        
        # 누적 조건들
        self.green_positions = {}  # {위치: 자모음} - 확정된 자모음
        self.yellow_jamos = set()  # 포함되어야 하는 자모음들
        self.yellow_excluded_positions = {}  # {자모음: [제외위치들]}
        self.black_jamos = set()  # 포함되지 않아야 하는 자모음들
    
    def add_turn(self, guess_word: str, result_pattern: str) -> List[str]:
        """
        새로운 턴 추가
        
        Args:
            guess_word: 추측 단어 ('비상구')
            result_pattern: 결과 패턴 ('BYBBYBB')
            
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
        """조건 업데이트"""
        for i, (jamo, result) in enumerate(zip(jamos, pattern)):
            if result == 'G':
                # Green: 정확한 위치
                self.green_positions[i] = jamo
                
            elif result == 'Y':
                # Yellow: 포함되지만 이 위치는 아님
                self.yellow_jamos.add(jamo)
                if jamo not in self.yellow_excluded_positions:
                    self.yellow_excluded_positions[jamo] = []
                self.yellow_excluded_positions[jamo].append(i)
                
            elif result == 'B':
                # Black: 포함되지 않음
                self.black_jamos.add(jamo)
    
    def _find_candidates(self) -> List[str]:
        """현재 조건에 맞는 후보 단어들 찾기"""
        # 같은 길이의 모든 단어 가져오기
        all_words = self.db.get_words_by_length(self.word_length)
        
        candidates = []
        
        for word_info in all_words:
            word = word_info['word']
            jamos = word_info['jamos']
            
            if self._check_conditions(jamos):
                candidates.append(word)
        
        return candidates
    
    def _check_conditions(self, jamos: str) -> bool:
        """단어가 모든 조건을 만족하는지 확인"""
        jamos_list = list(jamos)
        
        # 1. Green 조건 확인
        for pos, jamo in self.green_positions.items():
            if pos >= len(jamos_list) or jamos_list[pos] != jamo:
                return False
        
        # 2. Black 조건 확인
        for black_jamo in self.black_jamos:
            if black_jamo in jamos_list:
                return False
        
        # 3. Yellow 조건 확인
        # 모든 yellow 자모음이 포함되어야 함
        for yellow_jamo in self.yellow_jamos:
            if yellow_jamo not in jamos_list:
                return False
        
        # Yellow 자모음이 제외된 위치에 있으면 안됨
        for yellow_jamo, excluded_positions in self.yellow_excluded_positions.items():
            for pos in excluded_positions:
                if pos < len(jamos_list) and jamos_list[pos] == yellow_jamo:
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
        print(f"제외 자모음(B): {self.black_jamos}")
    
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
                jamos_display = ' '.join(jamos)
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
        print(f"  확정된 자모음: {self.green_positions}")
        print(f"  포함되어야 함: {self.yellow_jamos}")
        print(f"  제외된 자모음: {self.black_jamos}")
        
        # 현재 후보 수
        if self.word_length:
            candidates = self._find_candidates()
            print(f"  현재 후보: {len(candidates)}개")
    
    def get_current_candidates(self) -> List[str]:
        """현재 후보 단어들 반환"""
        if not self.word_length:
            return []
        return self._find_candidates()
    
    def single_turn_analysis(self, guess_word: str, result_pattern: str) -> List[str]:
        """단일 턴 분석 (독립적, 게임 상태에 영향 없음)"""
        jamos = self.processor.decompose_hangul(guess_word)
        
        print(f"\n=== 단일 턴 분석 ===")
        print(f"단어: {guess_word}")
        print(f"자모음: {' '.join(jamos)}")
        print(f"패턴: {result_pattern}")
        print(f"길이: {len(jamos)}자모음")
        
        # 임시 조건 분석
        temp_green = {}
        temp_yellow = set()
        temp_yellow_excluded = {}
        temp_black = set()
        
        for i, (jamo, result) in enumerate(zip(jamos, result_pattern)):
            if result == 'G':
                temp_green[i] = jamo
            elif result == 'Y':
                temp_yellow.add(jamo)
                if jamo not in temp_yellow_excluded:
                    temp_yellow_excluded[jamo] = []
                temp_yellow_excluded[jamo].append(i)
            elif result == 'B':
                temp_black.add(jamo)
        
        print(f"확정 위치(G): {temp_green}")
        print(f"포함 필수(Y): {temp_yellow}")
        print(f"Y 제외 위치: {temp_yellow_excluded}")
        print(f"제외 자모음(B): {temp_black}")
        
        # 후보 찾기
        all_words = self.db.get_words_by_length(len(jamos))
        candidates = []
        
        for word_info in all_words:
            word = word_info['word']
            word_jamos = list(word_info['jamos'])
            
            # 조건 확인
            valid = True
            
            # Green 확인
            for pos, jamo in temp_green.items():
                if pos >= len(word_jamos) or word_jamos[pos] != jamo:
                    valid = False
                    break
            
            if not valid:
                continue
            
            # Black 확인
            for black_jamo in temp_black:
                if black_jamo in word_jamos:
                    valid = False
                    break
            
            if not valid:
                continue
            
            # Yellow 확인
            for yellow_jamo in temp_yellow:
                if yellow_jamo not in word_jamos:
                    valid = False
                    break
            
            if not valid:
                continue
            
            for yellow_jamo, excluded_positions in temp_yellow_excluded.items():
                for pos in excluded_positions:
                    if pos < len(word_jamos) and word_jamos[pos] == yellow_jamo:
                        valid = False
                        break
                if not valid:
                    break
            
            if valid:
                candidates.append(word)
        
        self._print_candidates(candidates)
        return candidates

# 테스트 실행
if __name__ == "__main__":
    print("=" * 60)
    print("🎮 한국어 Wordle 게임 엔진 테스트")
    print("=" * 60)
    
    # 게임 엔진 초기화
    engine = GameEngine()
    
    # DB 상태 확인
    stats = engine.db.get_statistics()
    print(f"데이터베이스: 총 {stats['total_words']:,}개 단어")
    
    if stats['total_words'] == 0:
        print("❌ 데이터베이스가 비어있습니다.")
        sys.exit()
    
    print("\n[ 테스트 1: 누적 게임 플레이 ]")
    print("-" * 40)
    
    # 턴 1
    print("턴 1: '하모니' → 'BYBYBY'")
    candidates1 = engine.add_turn('하모니', 'BYBYBY')
    
    # 턴 2
    print(f"\n턴 2: '소비자' → 'BGBYBY'")
    candidates2 = engine.add_turn('소비자', 'BGBYBY')
    
    # 게임 상황 요약
    engine.show_game_summary()
      
       
    print("\n✅ 모든 테스트 완료!")
    
    print("\n사용법:")
    print("# 누적 게임")
    print("engine = GameEngine()")
    print("engine.add_turn('비상구', 'BYBBYBB')")
    print("engine.add_turn('놀이터', 'BBBGGBY')")
    print("engine.show_game_summary()")

    