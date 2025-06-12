import re
from pathlib import Path

class WordCleaner:
    """한국어 단어 목록을 정제하는 클래스"""
    
    def __init__(self):
        # 자음 목록 (종성이 아닌 단독 자음)
        self.standalone_consonants = [
            'ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 
            'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'
        ]
        
        # 모음 목록
        self.standalone_vowels = [
            'ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 
            'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ'
        ]
    
    def has_standalone_jamo(self, word: str) -> bool:
        """
        단어에 단독 자음이나 모음이 포함되어 있는지 확인
        
        Args:
            word: 검사할 단어
            
        Returns:
            단독 자모음 포함 여부
        """
        # 단독 자음이 포함된 경우
        for consonant in self.standalone_consonants:
            if consonant in word:
                return True
        
        # 단독 모음이 포함된 경우
        for vowel in self.standalone_vowels:
            if vowel in word:
                return True
        
        return False
    
    def is_valid_korean_word(self, word: str) -> bool:
        """
        유효한 한국어 단어인지 확인
        
        Args:
            word: 검사할 단어
            
        Returns:
            유효한 단어 여부
        """
        # 빈 문자열이나 공백만 있는 경우
        if not word or not word.strip():
            return False
        
        word = word.strip()
        
        # 단독 자모음이 포함된 경우 제외
        if self.has_standalone_jamo(word):
            return False
        
        # 한글이 아닌 문자가 포함된 경우 (영어, 숫자, 특수문자 등)
        if not re.match(r'^[가-힣]+$', word):
            return False
        
        # 너무 짧거나 긴 단어 제외
        if len(word) < 1 or len(word) > 10:
            return False
        
        return True
    
    def clean_wordlist(self, input_file: str, output_file: str = None) -> dict:
        """
        단어 목록 파일을 정제
        
        Args:
            input_file: 입력 파일 경로
            output_file: 출력 파일 경로 (None이면 자동 생성)
            
        Returns:
            정제 결과 통계
        """
        input_path = Path(input_file)
        
        if not input_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {input_file}")
        
        # 출력 파일명 자동 생성
        if output_file is None:
            output_file = input_path.stem + "_clean.txt"
        
        output_path = Path(output_file)
        
        print(f"📖 입력 파일: {input_path}")
        print(f"💾 출력 파일: {output_path}")
        
        # 단어 읽기 및 정제
        valid_words = set()  # 중복 제거를 위해 set 사용
        invalid_examples = []  # 제외된 단어 예시
        
        total_count = 0
        invalid_count = 0
        
        with open(input_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                word = line.strip()
                total_count += 1
                
                if self.is_valid_korean_word(word):
                    valid_words.add(word)
                else:
                    invalid_count += 1
                    # 예시로 처음 20개만 저장
                    if len(invalid_examples) < 20:
                        reason = self._get_invalid_reason(word)
                        invalid_examples.append(f"{word} ({reason})")
                
                # 진행상황 출력
                if line_num % 10000 == 0:
                    print(f"  처리 중... {line_num:,}줄")
        
        # 정렬된 단어 목록으로 변환
        sorted_words = sorted(list(valid_words))
        
        # 정제된 단어 목록 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            for word in sorted_words:
                f.write(word + '\n')
        
        # 결과 통계
        result = {
            'total_input': total_count,
            'valid_words': len(sorted_words),
            'invalid_words': invalid_count,
            'duplicates_removed': total_count - invalid_count - len(sorted_words),
            'invalid_examples': invalid_examples,
            'input_file': str(input_path),
            'output_file': str(output_path)
        }
        
        return result
    
    def _get_invalid_reason(self, word: str) -> str:
        """단어가 무효한 이유 반환"""
        if not word or not word.strip():
            return "빈 문자열"
        
        word = word.strip()
        
        if self.has_standalone_jamo(word):
            return "단독 자모음 포함"
        
        if not re.match(r'^[가-힣]+$', word):
            return "한글 이외 문자 포함"
        
        if len(word) < 1:
            return "너무 짧음"
        
        if len(word) > 10:
            return "너무 김"
        
        return "기타"
    
    def analyze_file(self, input_file: str) -> None:
        """파일 분석 (정제하지 않고 통계만)"""
        input_path = Path(input_file)
        
        if not input_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {input_file}")
        
        print(f"=== 파일 분석: {input_path} ===")
        
        total_count = 0
        valid_count = 0
        invalid_examples = {}  # {이유: [예시들]}
        
        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip()
                total_count += 1
                
                if self.is_valid_korean_word(word):
                    valid_count += 1
                else:
                    reason = self._get_invalid_reason(word)
                    if reason not in invalid_examples:
                        invalid_examples[reason] = []
                    if len(invalid_examples[reason]) < 5:  # 각 이유별로 5개까지만
                        invalid_examples[reason].append(word)
        
        print(f"총 단어 수: {total_count:,}개")
        print(f"유효한 단어: {valid_count:,}개 ({valid_count/total_count*100:.1f}%)")
        print(f"무효한 단어: {total_count-valid_count:,}개 ({(total_count-valid_count)/total_count*100:.1f}%)")
        
        print(f"\n무효한 단어 예시:")
        for reason, examples in invalid_examples.items():
            print(f"  {reason}: {', '.join(examples)}")

# 사용 예시 및 실행
if __name__ == "__main__":
    cleaner = WordCleaner()
    
    # 파일 경로 (실제 파일 경로로 수정하세요)
    input_file = r"C:\Users\Jaewon Song\Documents\Development\hongdle\data\wordslistUnique.txt"
    output_file = r"C:\Users\Jaewon Song\Documents\Development\hongdle\data\korean_words_clean_v2.txt"
    
    print("=" * 60)
    print("🧹 한국어 단어 목록 정제기")
    print("=" * 60)
    
    try:
        # 1. 파일 분석
        print("\n[ 1단계: 파일 분석 ]")
        cleaner.analyze_file(input_file)
        
        # 2. 정제 실행
        print(f"\n[ 2단계: 정제 실행 ]")
        result = cleaner.clean_wordlist(input_file, output_file)
        
        # 3. 결과 출력
        print(f"\n[ 3단계: 결과 ]")
        print(f"✅ 정제 완료!")
        print(f"  📥 입력: {result['total_input']:,}개 단어")
        print(f"  ✅ 유효: {result['valid_words']:,}개 단어")
        print(f"  ❌ 무효: {result['invalid_words']:,}개 단어")
        print(f"  🔄 중복제거: {result['duplicates_removed']:,}개")
        print(f"  💾 출력파일: {result['output_file']}")
        
        if result['invalid_examples']:
            print(f"\n제외된 단어 예시:")
            for example in result['invalid_examples']:
                print(f"  - {example}")
        
        print(f"\n🎉 정제된 파일을 사용해서 DB를 다시 구축하세요!")
        print(f"processor.parse_text_file('{output_file}')")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")