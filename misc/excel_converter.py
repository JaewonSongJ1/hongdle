import pandas as pd
import re
from typing import Set, List

class ExcelToTextConverter:
    """엑셀 파일의 한국어 단어를 텍스트 파일로 변환하는 클래스"""
    
    def __init__(self):
        pass
    
    def clean_korean_word(self, word: str) -> str:
        """
        한국어 단어 정제
        - 숫자 제거 (예: "가게03" -> "가게")
        - 특수문자 제거
        - 공백 제거
        """
        if not isinstance(word, str):
            return ""
        
        # 숫자 제거 (끝에 붙은 숫자들)
        cleaned = re.sub(r'\d+$', '', word)
        
        # 특수문자 제거 (한글과 일부 기호만 유지)
        cleaned = re.sub(r'[^\w가-힣\-]', '', cleaned)
        
        # 공백 제거
        cleaned = cleaned.strip()
        
        return cleaned
    
    def is_valid_korean_word(self, word: str) -> bool:
        """
        유효한 한국어 단어인지 확인
        - 한글로만 구성
        - 길이가 적절함 (1자 이상)
        """
        if not word:
            return False
        
        # 한글만 포함하는지 확인
        if not re.match(r'^[가-힣]+$', word):
            return False
        
        # 길이 확인 (너무 짧거나 긴 단어 제외)
        if len(word) < 1 or len(word) > 10:
            return False
        
        return True
    
    def convert_excel_to_text(self, excel_path: str, output_path: str, 
                             word_column: str = 'B', sheet_name: int = 0) -> dict:
        """
        엑셀 파일을 텍스트 파일로 변환
        
        Args:
            excel_path: 엑셀 파일 경로
            output_path: 출력 텍스트 파일 경로
            word_column: 단어가 있는 컬럼 (예: 'B')
            sheet_name: 시트 번호 또는 이름
            
        Returns:
            변환 결과 통계
        """
        try:
            # 엑셀 파일 읽기
            print(f"엑셀 파일 읽는 중: {excel_path}")
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            
            # 컬럼명 확인
            print(f"컬럼들: {list(df.columns)}")
            
            # B열 인덱스 찾기 (0-based)
            if word_column == 'B':
                word_col_idx = 1  # B열은 인덱스 1
            else:
                # 다른 컬럼명이 지정된 경우
                if word_column not in df.columns:
                    raise ValueError(f"컬럼 '{word_column}'을 찾을 수 없습니다.")
                word_col_idx = df.columns.get_loc(word_column)
            
            # 단어 컬럼 데이터 가져오기
            word_column_name = df.columns[word_col_idx]
            words_raw = df[word_column_name].dropna().tolist()
            
            print(f"원본 데이터 {len(words_raw)}개 읽음")
            
            # 단어 정제 및 중복 제거
            cleaned_words = set()  # 중복 제거를 위해 set 사용
            invalid_words = []
            
            for raw_word in words_raw:
                cleaned_word = self.clean_korean_word(str(raw_word))
                
                if self.is_valid_korean_word(cleaned_word):
                    cleaned_words.add(cleaned_word)
                else:
                    invalid_words.append(str(raw_word))
            
            # 정렬된 리스트로 변환
            final_words = sorted(list(cleaned_words))
            
            # 텍스트 파일로 저장
            with open(output_path, 'w', encoding='utf-8') as f:
                for word in final_words:
                    f.write(word + '\n')
            
            # 결과 통계
            result = {
                'total_raw': len(words_raw),
                'valid_words': len(final_words),
                'invalid_words': len(invalid_words),
                'duplicates_removed': len(words_raw) - len(invalid_words) - len(final_words),
                'output_file': output_path
            }
            
            return result
            
        except Exception as e:
            print(f"변환 중 오류 발생: {e}")
            return None
    
    def analyze_excel_structure(self, excel_path: str, sheet_name: int = 0) -> None:
        """
        엑셀 파일 구조 분석 (디버깅용)
        """
        try:
            print(f"=== 엑셀 파일 구조 분석: {excel_path} ===")
            
            # 엑셀 파일 읽기
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            
            print(f"행 수: {len(df)}")
            print(f"열 수: {len(df.columns)}")
            print(f"컬럼명: {list(df.columns)}")
            
            # 각 컬럼의 샘플 데이터 보기
            for i, col in enumerate(df.columns):
                print(f"\n컬럼 {chr(65+i)} ({col}):")
                sample_data = df[col].dropna().head(5).tolist()
                for j, data in enumerate(sample_data):
                    print(f"  {j+1}: {data}")
            
            # B열 데이터 타입 분석
            if len(df.columns) > 1:
                b_col = df.columns[1]
                b_data = df[b_col].dropna()
                print(f"\nB열 ({b_col}) 상세 분석:")
                print(f"  총 데이터 수: {len(b_data)}")
                print(f"  데이터 타입: {b_data.dtype}")
                
                # 숫자가 붙은 단어 패턴 분석
                words_with_numbers = []
                for item in b_data.head(20):
                    if re.search(r'\d+$', str(item)):
                        words_with_numbers.append(str(item))
                
                if words_with_numbers:
                    print(f"  숫자가 붙은 단어 예시: {words_with_numbers[:5]}")
            
        except Exception as e:
            print(f"분석 중 오류 발생: {e}")
    
    def convert_with_preview(self, excel_path: str, output_path: str, 
                           preview_count: int = 10) -> dict:
        """
        변환 과정을 미리보기와 함께 실행
        """
        print("=== 변환 미리보기 ===")
        
        # 엑셀 파일 구조 분석
        self.analyze_excel_structure(excel_path)
        
        print(f"\n=== 변환 실행 ===")
        
        # 실제 변환
        result = self.convert_excel_to_text(excel_path, output_path)
        
        if result:
            print(f"\n=== 변환 결과 ===")
            print(f"원본 데이터: {result['total_raw']}개")
            print(f"유효한 단어: {result['valid_words']}개")
            print(f"무효한 단어: {result['invalid_words']}개")
            print(f"중복 제거: {result['duplicates_removed']}개")
            print(f"출력 파일: {result['output_file']}")
            
            # 결과 파일 미리보기
            print(f"\n=== 출력 파일 미리보기 (상위 {preview_count}개) ===")
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f):
                        if i >= preview_count:
                            break
                        print(f"{i+1:3d}: {line.strip()}")
            except Exception as e:
                print(f"미리보기 오류: {e}")
        
        return result

# 사용 예시 및 실행 코드
if __name__ == "__main__":
    converter = ExcelToTextConverter()
    
    # 사용법 예시
    excel_file = "C:/Users/Jaewon Song/Downloads/61d37dd1-b91c-4666-a217-d74e5f938526/한국어 학습용 어휘 목록.xlsx"  # 실제 파일명으로 변경
    output_file = "C:/Users/Jaewon Song/Documents/Development/hongdle/data/korean_words_clean.txt"
    
    print("한국어 학습용 어휘 엑셀 파일 변환기")
    print("=" * 50)
    
    # 파일이 존재하는지 확인
    import os
    
    print("현재 작업 디렉토리:", os.getcwd())
    print("파일 목록:", os.listdir('.'))
    if os.path.exists(excel_file):
        print(f"파일 발견: {excel_file}")
        
        # 미리보기와 함께 변환
        result = converter.convert_with_preview(excel_file, output_file)
        
        if result:
            print(f"\n✅ 변환 완료!")
            print(f"📁 출력 파일: {output_file}")
            print(f"📊 총 {result['valid_words']}개의 깨끗한 한국어 단어가 저장되었습니다.")
            
            # WordProcessor와 연동 가능 확인
            print(f"\n다음 단계: WordProcessor로 DB화")
            print(f"processor.parse_text_file('{output_file}')")
        else:
            print("❌ 변환 실패")
    else:
        print(f"❌ 파일을 찾을 수 없습니다: {excel_file}")
        print("실제 엑셀 파일 경로를 확인해주세요.")
        
        # 분석만 실행하고 싶은 경우
        print("\n파일 구조만 분석하려면:")
        print("converter.analyze_excel_structure('파일경로.xlsx')")