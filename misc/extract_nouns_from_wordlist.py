import re
from pathlib import Path
from typing import Set
import argparse
import sys

class NounExtractor:
    """
    '한국어 학습용 어휘 목록' 형식의 파일에서 명사를 추출하고 정제하는 클래스.
    """
    def __init__(self):
        pass

    def clean_word(self, word: str) -> str:
        """
        단어에서 숫자와 불필요한 문자를 제거합니다.
        - "가격03" -> "가격"
        - "가-닿다" -> "가닿다"
        """
        if not isinstance(word, str):
            return ""
        # 단어 끝에 붙은 숫자 제거
        cleaned = re.sub(r'\d+$', '', word)
        # 한글이 아닌 문자 제거 (하이픈은 허용 후 제거)
        cleaned = cleaned.replace('-', '')
        cleaned = re.sub(r'[^가-힣]', '', cleaned)
        return cleaned.strip()

    def extract_nouns(self, input_file: str, output_file: str):
        """
        파일을 읽어 '명사' 품사의 단어만 추출하고 정제하여 저장합니다.
        """
        input_path = Path(input_file)
        if not input_path.exists():
            print(f"❌ 오류: 입력 파일 '{input_path}'를 찾을 수 없습니다.")
            sys.exit(1)

        print(f"📖 입력 파일: {input_path}")
        
        nouns: Set[str] = set()
        total_lines = 0
        noun_lines = 0

        # Windows에서 생성된 한글 텍스트 파일은 'cp949' 인코딩인 경우가 많습니다.
        with open(input_path, 'r', encoding='cp949') as f:
            # 헤더 라인 건너뛰기
            next(f, None)
            
            for line in f:
                total_lines += 1
                # 탭 또는 여러 공백으로 분리
                parts = re.split(r'\s+', line.strip())
                
                if len(parts) < 3:
                    continue
                
                word_raw = parts[1]
                pos = parts[2]

                if pos == '명':
                    noun_lines += 1
                    cleaned_word = self.clean_word(word_raw)
                    if cleaned_word:
                        nouns.add(cleaned_word)

        sorted_nouns = sorted(list(nouns))
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            for noun in sorted_nouns:
                f.write(f"{noun}\n")

        print("\n🎉 정제 완료!")
        print(f"  - 총 라인 수: {total_lines:,}개")
        print(f"  - '명사' 품사 라인: {noun_lines:,}개")
        print(f"  - 추출된 고유 명사: {len(sorted_nouns):,}개")
        print(f"💾 출력 파일: {output_path}")

def main():
    extractor = NounExtractor()
    project_root = Path(__file__).parent.parent
    input_file_path = project_root / 'data' / 'korean_study_word_list.txt'
    output_file_path = project_root / 'data' / 'korean_word_clean.txt'
    extractor.extract_nouns(str(input_file_path), str(output_file_path))

if __name__ == '__main__':
    main()