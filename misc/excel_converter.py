import pandas as pd
import os

def create_word_list():
    """
    NIADic.xlsx 파일에서 특정 조건에 맞는 단어를 추출하여
    korean_word_clean_list_big.txt 파일을 생성합니다.
    """
    # 현재 스크립트 파일의 디렉토리
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 프로젝트 루트 디렉토리 (misc 폴더의 상위)
    project_root = os.path.dirname(current_dir)
    
    # 입출력 파일 경로 설정
    input_path = os.path.join(project_root, 'data', 'NIADic.xlsx')
    output_path = os.path.join(project_root, 'data', 'korean_word_clean_list_big.txt')

    try:
        # 엑셀 파일 읽기 (openpyxl 엔진 사용)
        print(f"엑셀 파일을 읽는 중입니다: {input_path}")
        df = pd.read_excel(input_path, engine='openpyxl')

        # 디버깅을 위해 실제 엑셀 파일의 컬럼명 출력
        print(f"엑셀 파일에서 읽어온 컬럼: {df.columns.tolist()}")

        # 코드의 안정성을 위해 필요한 컬럼들이 있는지 먼저 확인합니다.
        required_columns = ['term', 'tag', 'category']
        if not all(col in df.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in df.columns]
            # 존재하지 않는 컬럼이 있을 경우, KeyError를 발생시켜 아래에서 처리하도록 합니다.
            raise KeyError(f"파일에 필요한 컬럼이 없습니다: {missing_cols}")

        # 1. 품사가 'ncn'인 단어 필터링
        df_ncn = df[df['tag'] == 'ncn'].copy()
        print(f"'ncn' 품사를 가진 단어 {len(df_ncn)}개를 찾았습니다.")

        # 2. 특정 분야 제외
        excluded_categories = ['brand_name', 'general_product', 'people_names', 'place_name']
        df_filtered = df_ncn[~df_ncn['category'].isin(excluded_categories)]
        print(f"특정 분야 제외 후 {len(df_filtered)}개의 단어가 남았습니다.")

        # 3. 'term' 열만 추출하여 txt 파일로 저장
        words = df_filtered['term']

        with open(output_path, 'w', encoding='utf-8') as f:
            for word in words:
                f.write(f"{word}\n")
        
        print(f"성공적으로 '{os.path.basename(output_path)}' 파일을 생성했습니다. (총 {len(words)}개 단어)")

    except FileNotFoundError:
        print(f"오류: 파일을 찾을 수 없습니다. '{os.path.abspath(input_path)}'")
        print("'data' 폴더에 'NIADic.xlsx' 파일이 있는지 확인해주세요.")
    except KeyError as e:
        print(f"오류: 엑셀 파일에서 필요한 컬럼을 찾을 수 없습니다. {e}")
        print("NIADic.xlsx 파일의 첫 행에 'term', 'tag', 'category' 컬럼명이 정확히 포함되어 있는지 확인해주세요.")
    except Exception as e:
        print(f"예상치 못한 오류가 발생했습니다: {e}")

if __name__ == '__main__':
    create_word_list()