import sqlite3
import os
import argparse
from collections import Counter

def get_project_root():
    """현재 스크립트의 상위 디렉토리(프로젝트 루트)를 반환합니다."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def create_db_with_frequency(project_root):
    """
    korean_word_clean_list.txt를 읽어 단어와 사용 빈도를 korean_words.db에 저장합니다.
    (사용 빈도는 텍스트 파일 내 단어의 출현 횟수를 카운트하는 간단한 예시입니다.)
    """
    input_path = os.path.join(project_root, 'data', 'korean_word_clean_list.txt')
    db_path = os.path.join(project_root, 'data', 'korean_words.db')

    print(f"시작: '{os.path.basename(input_path)}' -> '{os.path.basename(db_path)}' (단어 빈도 포함)")

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            # 공백 라인을 제외하고 단어를 읽어옵니다.
            words = [line.strip() for line in f if line.strip()]
        
        if not words:
            print(f"경고: '{os.path.basename(input_path)}' 파일이 비어있습니다.")
            return

        # 단어의 출현 빈도를 계산합니다.
        word_counts = Counter(words)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS words")
        cursor.execute("CREATE TABLE words (word TEXT PRIMARY KEY, frequency INTEGER NOT NULL)")

        # (word, frequency) 쌍을 데이터베이스에 삽입합니다.
        cursor.executemany("INSERT OR IGNORE INTO words (word, frequency) VALUES (?, ?)", word_counts.items())

        conn.commit()
        conn.close()

        print(f"성공: '{os.path.basename(db_path)}' 생성 완료 (고유 단어 {len(word_counts)}개)")

    except FileNotFoundError:
        print(f"오류: 입력 파일 '{input_path}'를 찾을 수 없습니다.")
    except Exception as e:
        print(f"오류: DB 생성 중 예외 발생 - {e}")

def create_full_db_simple(project_root):
    """
    korean_word_clean_list_big.txt를 읽어 단어 목록만 korean_words_full.db에 저장합니다.
    """
    input_path = os.path.join(project_root, 'data', 'korean_word_clean_list_big.txt')
    db_path = os.path.join(project_root, 'data', 'korean_words_full.db')

    print(f"시작: '{os.path.basename(input_path)}' -> '{os.path.basename(db_path)}' (단어 목록만)")

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            words = {line.strip() for line in f if line.strip()} # 중복을 제거하기 위해 set 사용

        if not words:
            print(f"경고: '{os.path.basename(input_path)}' 파일이 비어있습니다.")
            return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS words")
        cursor.execute("CREATE TABLE words (word TEXT PRIMARY KEY)")

        # (word,) 형태의 튜플 리스트로 만들어 데이터베이스에 삽입합니다.
        cursor.executemany("INSERT OR IGNORE INTO words (word) VALUES (?)", [(word,) for word in sorted(list(words))])

        conn.commit()
        conn.close()

        print(f"성공: '{os.path.basename(db_path)}' 생성 완료 (고유 단어 {len(words)}개)")

    except FileNotFoundError:
        print(f"오류: 입력 파일 '{input_path}'를 찾을 수 없습니다.")
    except Exception as e:
        print(f"오류: DB 생성 중 예외 발생 - {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="한국어 단어 사전을 위한 SQLite 데이터베이스를 생성합니다.")
    parser.add_argument(
        '--full',
        action='store_true',
        help="'korean_word_clean_list_big.txt'를 사용하여 빈도수 없는 전체 단어 DB('korean_words_full.db')를 생성합니다."
    )
    args = parser.parse_args()
    
    root = get_project_root()
    if args.full:
        create_full_db_simple(root)
    else:
        # 기본 동작: 빈도수 포함 DB 생성
        create_db_with_frequency(root)