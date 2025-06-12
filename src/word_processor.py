import re
from typing import List, Dict

class WordProcessor:
    """한글 단어 처리 전용 클래스 - 복합 모음을 기본 모음으로 분해"""
    
    def __init__(self):
        # 한글 자모음 정의
        self.CHOSUNG = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
        self.JUNGSUNG = ['ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ']
        self.JONGSUNG = ['', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
        
        # 기본 모음 (10개)
        self.BASIC_VOWELS = ['ㅏ', 'ㅑ', 'ㅓ', 'ㅕ', 'ㅗ', 'ㅛ', 'ㅜ', 'ㅠ', 'ㅡ', 'ㅣ']
        
        # 복합 모음 (11개)
        self.COMPLEX_VOWELS = ['ㅐ', 'ㅔ', 'ㅒ', 'ㅖ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅢ']
        
        # 복합 모음 → 기본 모음 분해 규칙
        self.DECOMPOSE_RULES = {
            'ㅐ': ['ㅏ', 'ㅣ'],
            'ㅔ': ['ㅓ', 'ㅣ'],
            'ㅒ': ['ㅑ', 'ㅣ'],
            'ㅖ': ['ㅕ', 'ㅣ'],
            'ㅘ': ['ㅗ', 'ㅏ'],
            'ㅙ': ['ㅗ', 'ㅏ', 'ㅣ'],
            'ㅚ': ['ㅗ', 'ㅣ'],
            'ㅝ': ['ㅜ', 'ㅓ'],
            'ㅞ': ['ㅜ', 'ㅓ', 'ㅣ'],
            'ㅟ': ['ㅜ', 'ㅣ'],
            'ㅢ': ['ㅡ', 'ㅣ']
        }
        
        # 기본 자음 (14개)
        self.BASIC_CONSONANTS = ['ㄱ', 'ㄴ', 'ㄷ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅅ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
        
        # 쌍자음 (5개)
        self.DOUBLE_CONSONANTS = ['ㄲ', 'ㄸ', 'ㅃ', 'ㅆ', 'ㅉ']
        
        # 자음군/복합 종성 (11개)
        self.COMPLEX_FINALS = ['ㄳ', 'ㄵ', 'ㄶ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅄ']
        
        # 쌍자음 분해 규칙
        self.DOUBLE_CONSONANT_RULES = {
            'ㄲ': ['ㄱ', 'ㄱ'],
            'ㄸ': ['ㄷ', 'ㄷ'],
            'ㅃ': ['ㅂ', 'ㅂ'],
            'ㅆ': ['ㅅ', 'ㅅ'],
            'ㅉ': ['ㅈ', 'ㅈ']
        }
        
        # 자음군/복합 종성 분해 규칙
        self.COMPLEX_FINAL_RULES = {
            'ㄳ': ['ㄱ', 'ㅅ'],
            'ㄵ': ['ㄴ', 'ㅈ'],
            'ㄶ': ['ㄴ', 'ㅎ'],
            'ㄺ': ['ㄹ', 'ㄱ'],
            'ㄻ': ['ㄹ', 'ㅁ'],
            'ㄼ': ['ㄹ', 'ㅂ'],
            'ㄽ': ['ㄹ', 'ㅅ'],
            'ㄾ': ['ㄹ', 'ㅌ'],
            'ㄿ': ['ㄹ', 'ㅍ'],
            'ㅀ': ['ㄹ', 'ㅎ'],
            'ㅄ': ['ㅂ', 'ㅅ']
        }
    
    def decompose_hangul(self, word: str) -> List[str]:
        """
        한글 단어를 기본 자모음으로 분해
        - 복합 모음 → 기본 모음으로 분해
        - 쌍자음 → 기본 자음으로 분해  
        - 자음군(복합 종성) → 기본 자음으로 분해
        
        Args:
            word: 한글 단어 (예: '깎는')
            
        Returns:
            기본 자모음 리스트 (예: ['ㄱ', 'ㄱ', 'ㅏ', 'ㄱ', 'ㄴ', 'ㅡ', 'ㄴ'])
        """
        result = []
        
        for char in word:
            if '가' <= char <= '힣':
                # 한글 글자를 초성, 중성, 종성으로 분해
                code = ord(char) - ord('가')
                jong_idx = code % 28
                jung_idx = (code - jong_idx) // 28 % 21
                cho_idx = (code - jong_idx - jung_idx * 28) // 28 // 21
                
                # 1. 초성 처리 (쌍자음 분해)
                chosung = self.CHOSUNG[cho_idx]
                if chosung in self.DOUBLE_CONSONANTS:
                    # 쌍자음이면 기본 자음으로 분해
                    basic_consonants = self.DOUBLE_CONSONANT_RULES[chosung]
                    result.extend(basic_consonants)
                else:
                    # 기본 자음이면 그대로
                    result.append(chosung)
                
                # 2. 중성 처리 (복합 모음 분해)
                vowel = self.JUNGSUNG[jung_idx]
                if vowel in self.COMPLEX_VOWELS:
                    # 복합 모음이면 기본 모음으로 분해
                    basic_vowels = self.DECOMPOSE_RULES[vowel]
                    result.extend(basic_vowels)
                else:
                    # 기본 모음이면 그대로
                    result.append(vowel)
                
                # 3. 종성 처리 (자음군 분해)
                if jong_idx > 0:
                    jongsung = self.JONGSUNG[jong_idx]
                    
                    if jongsung in self.DOUBLE_CONSONANTS:
                        # 쌍자음이면 기본 자음으로 분해
                        basic_consonants = self.DOUBLE_CONSONANT_RULES[jongsung]
                        result.extend(basic_consonants)
                    elif jongsung in self.COMPLEX_FINALS:
                        # 자음군이면 기본 자음으로 분해
                        basic_consonants = self.COMPLEX_FINAL_RULES[jongsung]
                        result.extend(basic_consonants)
                    else:
                        # 기본 자음이면 그대로
                        result.append(jongsung)
        
        return result
    
    def decompose_to_string(self, word: str) -> str:
        """단어를 기본 자모음 문자열로 변환"""
        jamos = self.decompose_hangul(word)
        return ''.join(jamos)
    
    def create_word_data(self, word: str) -> Dict:
        """DB 저장용 단어 데이터 생성"""
        jamos = self.decompose_hangul(word)
        return {
            'word': word,
            'length': len(jamos),
            'jamos': ''.join(jamos)
        }
    
    def is_valid_hangul(self, word: str) -> bool:
        """한글로만 구성되어 있는지 확인"""
        return bool(re.match(r'^[가-힣]+$', word))
    
    def is_valid_length(self, word: str, min_length: int = 5, max_length: int = 7) -> bool:
        """기본 자모음 개수가 적절한 범위에 있는지 확인"""
        if not self.is_valid_hangul(word):
            return False
        jamos = self.decompose_hangul(word)
        return min_length <= len(jamos) <= max_length
    
    def is_valid_word(self, word: str, min_length: int = 5, max_length: int = 7) -> bool:
        """게임에 사용할 수 있는 유효한 단어인지 확인"""
        return self.is_valid_hangul(word) and self.is_valid_length(word, min_length, max_length)
    
    def clean_word(self, raw_word: str) -> str:
        """원본 단어에서 불필요한 부분 제거"""
        word = re.sub(r'\d+$', '', raw_word)  # 숫자 제거
        word = re.sub(r'[^\w가-힣]', '', word)  # 특수문자 제거
        return word.strip()
    
    def parse_text_file(self, file_path: str, encoding: str = 'utf-8') -> List[Dict]:
        """텍스트 파일에서 단어들을 읽어서 처리"""
        words_data = []
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                for line_num, line in enumerate(f, 1):
                    raw_word = line.strip()
                    if not raw_word:
                        continue
                    
                    clean_word = self.clean_word(raw_word)
                    if not clean_word:
                        continue
                    
                    if self.is_valid_word(clean_word):
                        word_data = self.create_word_data(clean_word)
                        word_data['source_line'] = line_num
                        word_data['raw_word'] = raw_word
                        words_data.append(word_data)
        
        except FileNotFoundError:
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        except Exception as e:
            raise Exception(f"파일 처리 중 오류 발생: {e}")
        
        return words_data
    
    def show_word_analysis(self, word: str) -> None:
        """단어 분석 결과 출력"""
        print(f"=== 단어 분석: {word} ===")
        
        if not self.is_valid_hangul(word):
            print("❌ 한글이 아닌 문자가 포함되어 있습니다.")
            return
        
        jamos = self.decompose_hangul(word)
        jamos_str = self.decompose_to_string(word)
        
        print(f"원본: {word}")
        print(f"기본 자모음 개수: {len(jamos)}개")
        print(f"자모음 문자열: {jamos_str}")
        print(f"게임 사용 가능: {'✅' if self.is_valid_word(word) else '❌'}")
        print("분해 결과:")
        for i, jamo in enumerate(jamos):
            print(f"  위치 {i}: {jamo}")
        
        # 분해 정보 표시
        decomposition_info = []
        
        for char in word:
            if '가' <= char <= '힣':
                code = ord(char) - ord('가')
                jong_idx = code % 28
                jung_idx = (code - jong_idx) // 28 % 21
                cho_idx = (code - jong_idx - jung_idx * 28) // 28 // 21
                
                chosung = self.CHOSUNG[cho_idx]
                vowel = self.JUNGSUNG[jung_idx]
                jongsung = self.JONGSUNG[jong_idx] if jong_idx > 0 else None
                
                # 초성 분해 정보
                if chosung in self.DOUBLE_CONSONANTS:
                    decomposed = ' + '.join(self.DOUBLE_CONSONANT_RULES[chosung])
                    decomposition_info.append(f"초성 {chosung} → {decomposed}")
                
                # 중성 분해 정보
                if vowel in self.COMPLEX_VOWELS:
                    decomposed = ' + '.join(self.DECOMPOSE_RULES[vowel])
                    decomposition_info.append(f"중성 {vowel} → {decomposed}")
                
                # 종성 분해 정보
                if jongsung:
                    if jongsung in self.DOUBLE_CONSONANTS:
                        decomposed = ' + '.join(self.DOUBLE_CONSONANT_RULES[jongsung])
                        decomposition_info.append(f"종성 {jongsung} → {decomposed}")
                    elif jongsung in self.COMPLEX_FINALS:
                        decomposed = ' + '.join(self.COMPLEX_FINAL_RULES[jongsung])
                        decomposition_info.append(f"종성 {jongsung} → {decomposed}")
        
        if decomposition_info:
            print("자모음 분해:")
            for info in decomposition_info:
                print(f"  {info}")
        else:
            print("💡 모든 자모음이 기본 자모음입니다.")

# 테스트 실행
if __name__ == "__main__":
    processor = WordProcessor()
    
    print("=== 자모음 분해 테스트 (모든 분해 규칙 포함) ===")
    test_words = ["개나리", "깎는", "앉다", "닭", "없어", "뜨거워", "싸움"]
    
    for word in test_words:
        processor.show_word_analysis(word)
        print()
    
    print("=== 분해 확인 ===")
    print(f"'개나리' 분해: {processor.decompose_hangul('개나리')}")
    print(f"'깎는' 분해: {processor.decompose_hangul('깎는')}")
    print(f"'앉다' 분해: {processor.decompose_hangul('앉다')}")
    print(f"'없어' 분해: {processor.decompose_hangul('없어')}")
    
    print("\n분해 규칙 적용 예시:")
    print("'깎는': ㄲ(ㄱ+ㄱ) + ㅏ + ㄱ + ㄱ + ㄴ + ㅡ + ㄴ")
    print("'앉다': ㅇ + ㅏ + ㄴ + ㅈ(ㄵ 분해) + ㄷ + ㅏ")
    print("'없어': ㅇ + ㅓ + ㅂ + ㅅ(ㅄ 분해) + ㅇ + ㅓ")