import re
from pathlib import Path
import sys
from collections import Counter

class NounFrequencyExtractor:
    """
    '한국어 어휘 목록'에서 명사와 빈도를 추출하고 정제하는 클래스.
    동일한 단어(예: 가01, 가07 -> 가)의 빈도를 합산합니다.
    """
    def __init__(self):
        pass

    def clean_word(self, word: str) -> str:
        """단어에서 숫자와 불필요한 문자를 제거합니다."""
        if not isinstance(word, str):
            return ""
        # 단어 끝에 붙은 숫자 제거
        cleaned = re.sub(r'\d+$', '', word)
        # 한글이 아닌 문자 제거
        cleaned = re.sub(r'[^가-힣]', '', cleaned)
        return cleaned.strip()

    def extract(self, input_file: str, output_file: str):
        """파일을 읽어 명사와 빈도를 추출하고 정제하여 저장합니다."""
        input_path = Path(input_file)
        if not input_path.exists():
            print(f"❌ 오류: 입력 파일 '{input_path}'를 찾을 수 없습니다.")
            sys.exit(1)

        print(f"📖 입력 파일: {input_path}")
        
        noun_freqs = Counter()
        total_lines = 0
        noun_lines = 0

        # Windows 환경의 텍스트 파일 인코딩(cp949)을 고려합니다.
        # 디코딩 오류가 발생하는 문자는 무시하고 진행합니다.
        with open(input_path, 'r', encoding='cp949', errors='ignore') as f:
            # 헤더 라인(첫 줄)을 읽어 컬럼 인덱스를 찾습니다.
            header_line = f.readline().strip()
            header = re.split(r'\s+', header_line)
            
            try:
                word_idx = header.index('항목')
                pos_idx = header.index('품사')
                freq_idx = header.index('빈도')
            except ValueError as e:
                print(f"❌ 오류: 헤더에서 필수 컬럼을 찾을 수 없습니다: {e}")
                print(f"   찾은 헤더: {header}")
                sys.exit(1)

            # 데이터 라인을 처리합니다.
            for line in f:
                total_lines += 1
                parts = re.split(r'\s+', line.strip())
                
                if len(parts) <= max(word_idx, pos_idx, freq_idx):
                    continue

                if parts[pos_idx].strip() == '명':
                    noun_lines += 1
                    cleaned_word = self.clean_word(parts[word_idx])
                    try:
                        frequency = int(parts[freq_idx].strip())
                        if cleaned_word:
                            noun_freqs[cleaned_word] += frequency
                    except (ValueError, IndexError):
                        continue # 빈도 값이 숫자가 아니면 무시
        
        # 빈도순으로 내림차순 정렬합니다.
        sorted_nouns = sorted(noun_freqs.items(), key=lambda item: item[1], reverse=True)

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            for word, freq in sorted_nouns:
                f.write(f"{word} {freq}\n")

        print("\n🎉 정제 완료!")
        print(f"  - 총 {noun_lines:,}개의 명사 항목 처리")
        print(f"  - 고유 명사 수: {len(sorted_nouns):,}개")
        print(f"💾 출력 파일: {output_path}")

def main():
    """메인 실행 함수"""
    extractor = NounFrequencyExtractor()
    project_root = Path(__file__).parent.parent
    input_file_path = project_root / 'data' / 'korean_word_list.txt'
    output_file_path = project_root / 'data' / 'korean_word_clean_list.txt' # 요청하신 파일명
    extractor.extract(str(input_file_path), str(output_file_path))

if __name__ == '__main__':
    main()