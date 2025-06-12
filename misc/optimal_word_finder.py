import sys
from pathlib import Path
from typing import List, Dict, Set
from collections import Counter

# src 폴더의 모듈들 import (misc에서 src로)
current_dir = Path(__file__).parent
src_dir = current_dir.parent / 'src'  # misc의 상위폴더/src
sys.path.append(str(src_dir))

from word_database import WordDatabase

class OptimalWordFinder:
    """자모음이 중복되지 않는 최적의 시작 단어를 찾는 클래스"""
    
    def __init__(self, db_path: str = r"C:\Users\Jaewon Song\Documents\Development\hongdle\data\korean_words.db"):
        """
        Args:
            db_path: 데이터베이스 경로
        """
        self.db = WordDatabase(db_path)
    
    def has_duplicate_jamos(self, jamos_str: str) -> bool:
        """
        자모음 문자열에 중복이 있는지 확인
        
        Args:
            jamos_str: 자모음 문자열 (예: "ㄱㅏㅣㄴㅏㄹㅣ")
            
        Returns:
            중복 여부
        """
        jamos_list = list(jamos_str)
        return len(jamos_list) != len(set(jamos_list))
    
    def find_optimal_words(self, target_length: int) -> List[Dict]:
        """
        특정 길이의 자모음 중복 없는 단어들 찾기
        
        Args:
            target_length: 목표 자모음 개수 (5, 6, 7)
            
        Returns:
            최적 단어들 리스트
        """
        print(f"\n=== {target_length}자모음 최적 단어 검색 중 ===")
        
        # 해당 길이의 모든 단어 조회
        all_words = self.db.get_words_by_length(target_length)
        print(f"총 {target_length}자모음 단어: {len(all_words)}개")
        
        optimal_words = []
        
        for word_info in all_words:
            jamos_str = word_info['jamos']
            
            # 자모음 중복 확인
            if not self.has_duplicate_jamos(jamos_str):
                optimal_words.append({
                    'word': word_info['word'],
                    'length': word_info['length'],
                    'jamos': jamos_str,
                    'jamos_list': list(jamos_str)
                })
        
        print(f"자모음 중복 없는 단어: {len(optimal_words)}개")
        return optimal_words
    
    def analyze_jamo_frequency(self, words_data: List[Dict]) -> Dict:
        """
        자모음별 사용 빈도 분석
        
        Args:
            words_data: 단어 데이터 리스트
            
        Returns:
            자모음별 빈도 정보
        """
        jamo_counter = Counter()
        
        for word_data in words_data:
            for jamo in word_data['jamos_list']:
                jamo_counter[jamo] += 1
        
        return dict(jamo_counter)
    
    def rank_words_by_frequency(self, words_data: List[Dict]) -> List[Dict]:
        """
        자모음 빈도를 고려해서 단어를 순위별로 정렬
        (더 자주 나오는 자모음들을 포함한 단어를 우선순위로)
        
        Args:
            words_data: 단어 데이터 리스트
            
        Returns:
            빈도 점수 순으로 정렬된 단어 리스트
        """
        # 전체 단어에서 자모음 빈도 계산
        all_words = []
        for length in [5, 6, 7]:
            length_words = self.db.get_words_by_length(length)
            all_words.extend(length_words)
        
        total_jamo_counter = Counter()
        for word_info in all_words:
            for jamo in word_info['jamos']:
                total_jamo_counter[jamo] += 1
        
        # 각 단어의 빈도 점수 계산
        for word_data in words_data:
            score = sum(total_jamo_counter[jamo] for jamo in word_data['jamos_list'])
            word_data['frequency_score'] = score
        
        # 빈도 점수 순으로 정렬 (높은 점수부터)
        return sorted(words_data, key=lambda x: x['frequency_score'], reverse=True)
    
    def export_optimal_words(self, output_dir: str = r"C:\Users\Jaewon Song\Documents\Development\hongdle\data") -> Dict[int, str]:
        """
        최적 단어들을 텍스트 파일로 내보내기
        
        Args:
            output_dir: 출력 디렉토리
            
        Returns:
            {길이: 파일경로} 딕셔너리
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        exported_files = {}
        
        for length in [5, 6, 7]:
            # 최적 단어 찾기
            optimal_words = self.find_optimal_words(length)
            
            if not optimal_words:
                print(f"❌ {length}자모음 최적 단어가 없습니다.")
                continue
            
            # 빈도별 순위 매기기
            ranked_words = self.rank_words_by_frequency(optimal_words)
            
            # 파일로 저장
            filename = f"optimal_words_{length}jamos.txt"
            file_path = output_path / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# {length}자모음 최적 시작 단어 (자모음 중복 없음)\n")
                f.write(f"# 총 {len(ranked_words)}개 단어\n")
                f.write(f"# 빈도 점수 순으로 정렬 (높은 점수 = 더 효율적)\n\n")
                
                for i, word_data in enumerate(ranked_words, 1):
                    jamos_display = ' '.join(word_data['jamos_list'])
                    f.write(f"{word_data['word']}\t{jamos_display}\t{word_data['frequency_score']}\n")
            
            exported_files[length] = str(file_path)
            print(f"✅ {length}자모음: {len(ranked_words)}개 단어 → {file_path}")
        
        return exported_files
    
    def show_top_recommendations(self, top_n: int = 10):
        """각 길이별 상위 추천 단어들 출력"""
        print("\n" + "="*80)
        print("🎯 자모음 중복 없는 최적 시작 단어 추천")
        print("="*80)
        
        for length in [5, 6, 7]:
            optimal_words = self.find_optimal_words(length)
            
            if not optimal_words:
                print(f"\n[ {length}자모음 ]: 추천 단어 없음")
                continue
            
            ranked_words = self.rank_words_by_frequency(optimal_words)
            
            print(f"\n[ {length}자모음 최적 단어 TOP {min(top_n, len(ranked_words))} ]")
            print("-" * 60)
            
            for i, word_data in enumerate(ranked_words[:top_n], 1):
                jamos_display = ' '.join(word_data['jamos_list'])
                score = word_data['frequency_score']
                print(f"{i:2d}. {word_data['word']:<8} → {jamos_display:<20} (점수: {score})")
    
    def analyze_database(self):
        """데이터베이스 전체 분석"""
        stats = self.db.get_statistics()
        
        print("=" * 60)
        print("📊 데이터베이스 분석")
        print("=" * 60)
        print(f"총 단어 수: {stats['total_words']:,}개")
        print(f"DB 크기: {stats['db_size_mb']}MB")
        print(f"길이별 분포:")
        
        total_optimal = 0
        
        for length, count in sorted(stats['length_distribution'].items()):
            optimal_words = self.find_optimal_words(length)
            optimal_count = len(optimal_words)
            optimal_ratio = (optimal_count / count * 100) if count > 0 else 0
            
            if length in [5, 6, 7]:
                total_optimal += optimal_count
                print(f"  {length}자모음: {count:,}개 → 최적: {optimal_count}개 ({optimal_ratio:.1f}%)")
            else:
                print(f"  {length}자모음: {count:,}개")
        
        print(f"\n총 최적 시작 단어: {total_optimal}개")

def main():
    """메인 실행 함수"""
    print("🎮 한국어 Wordle 최적 시작 단어 찾기")
    print("="*60)
    
    try:
        finder = OptimalWordFinder()
        
        # 1. 데이터베이스 분석
        finder.analyze_database()
        
        # 2. 최적 단어 추천
        finder.show_top_recommendations(10)
        
        # 3. 파일로 내보내기
        print(f"\n📁 파일 내보내기 중...")
        exported_files = finder.export_optimal_words()
        
        print(f"\n🎉 완료!")
        print(f"내보낸 파일:")
        for length, file_path in exported_files.items():
            print(f"  {length}자모음: {file_path}")
        
        print(f"\n💡 사용법:")
        print(f"  - 각 파일의 상위 단어들이 가장 효율적인 시작 단어입니다.")
        print(f"  - 빈도 점수가 높을수록 더 많은 정보를 얻을 수 있습니다.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    main()