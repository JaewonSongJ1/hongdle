import sqlite3
import json
import os
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from pathlib import Path

#How to use
#python src/word_database.py --input data/korean_word_clean_list.txt --output data/korean_words_full.db  

class WordDatabase:
    """한국어 단어 데이터베이스 관리 전용 클래스"""
    
    def __init__(self, db_path: str = None):
        """
        데이터베이스 초기화
        
        Args:
            db_path: 데이터베이스 파일 경로 (None이면 프로젝트 내 data 폴더 사용)
        """
        if db_path is None:
            # 현재 파일 기준으로 프로젝트 루트 찾기
            current_file = Path(__file__)
            project_root = current_file.parent.parent  # src -> hongdle
            data_dir = project_root / "data"
            data_dir.mkdir(exist_ok=True)  # data 폴더가 없으면 생성
            self.db_path = str(data_dir / "korean_words.db")
        else:
            self.db_path = db_path
            
        # 디렉토리가 없으면 생성
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """데이터베이스 테이블 생성 및 스키마 마이그레이션"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. words 테이블 생성 또는 마이그레이션
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='words'")
        table_exists = cursor.fetchone()

        if not table_exists:
            # 테이블이 없으면 최신 스키마로 새로 생성
            cursor.execute('''
                CREATE TABLE words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT UNIQUE NOT NULL,
                    length INTEGER NOT NULL,
                    jamos TEXT NOT NULL,
                    frequency INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        else:
            # 테이블이 있으면, 누락된 컬럼이 있는지 확인하고 추가 (간단한 스키마 마이그레이션)
            cursor.execute("PRAGMA table_info(words)")
            columns = [info[1] for info in cursor.fetchall()]
            
            # NOTE: NOT NULL 제약조건과 함께 컬럼을 추가하려면 DEFAULT 값이 필요합니다.
            # 이 값들은 데이터 재구축 시 올바르게 채워져야 합니다.
            if 'length' not in columns:
                print("INFO: 'words' 테이블에 'length' 컬럼을 추가합니다. 정확한 값을 위해서는 DB 재생성이 필요합니다.")
                cursor.execute('ALTER TABLE words ADD COLUMN length INTEGER NOT NULL DEFAULT 0')
            if 'jamos' not in columns:
                print("INFO: 'words' 테이블에 'jamos' 컬럼을 추가합니다. 정확한 값을 위해서는 DB 재생성이 필요합니다.")
                cursor.execute('ALTER TABLE words ADD COLUMN jamos TEXT NOT NULL DEFAULT ""')
            if 'frequency' not in columns:
                print("INFO: 'words' 테이블에 'frequency' 컬럼을 추가합니다.")
                cursor.execute('ALTER TABLE words ADD COLUMN frequency INTEGER NOT NULL DEFAULT 0')
        
        # 2. 메타데이터 테이블 생성 (DB 정보 저장용)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # 3. 인덱스 생성 (IF NOT EXISTS로 안전하게 실행)
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_length ON words(length)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_jamos ON words(jamos)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_frequency ON words(frequency DESC)')
        # 4. 메타데이터 초기화
        cursor.execute('''
            INSERT OR IGNORE INTO metadata (key, value) 
            VALUES ('db_version', '1.1')
        ''')
        cursor.execute('''
            INSERT OR IGNORE INTO metadata (key, value) 
            VALUES ('created_at', ?)
        ''', (datetime.now().isoformat(),))
        
        conn.commit()
        conn.close()
    
    def insert_word(self, word_data: Dict) -> bool:
        """
        단어 하나를 데이터베이스에 삽입
        
        Args:
            word_data: WordProcessor에서 생성한 단어 데이터 (frequency 포함)
            
        Returns:
            삽입 성공 여부
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO words (word, length, jamos, frequency)
                VALUES (?, ?, ?, ?)
            ''', (word_data['word'], word_data['length'], word_data['jamos'], word_data.get('frequency', 0)))
            
            success = cursor.rowcount > 0
            conn.commit()
        except Exception as e:
            print(f"단어 삽입 오류: {e}")
            success = False
        finally:
            conn.close()
        
        return success
    
    def bulk_insert(self, words_data: List[Dict]) -> Dict:
        """
        여러 단어를 한번에 데이터베이스에 삽입
        
        Args:
            words_data: WordProcessor에서 생성한 단어 데이터 리스트 (frequency 포함)
            
        Returns:
            삽입 결과 통계
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        inserted = 0
        duplicated = 0
        errors = 0
        
        try:
            for word_data in words_data:
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO words (word, length, jamos, frequency)
                        VALUES (?, ?, ?, ?)
                    ''', (word_data['word'], word_data['length'], word_data['jamos'], word_data.get('frequency', 0)))
                    
                    if cursor.rowcount > 0:
                        inserted += 1
                    else:
                        duplicated += 1
                        
                except Exception:
                    errors += 1
            
            conn.commit()
            
            # 메타데이터 업데이트
            cursor.execute('''
                INSERT OR REPLACE INTO metadata (key, value, updated_at) 
                VALUES ('last_bulk_insert', ?, ?)
            ''', (datetime.now().isoformat(), datetime.now().isoformat()))
            
            conn.commit()
            
        except Exception as e:
            print(f"일괄 삽입 오류: {e}")
        finally:
            conn.close()
        
        return {
            'inserted': inserted,
            'duplicated': duplicated,
            'errors': errors,
            'total_processed': len(words_data)
        }
    
    def get_word_by_id(self, word_id: int) -> Optional[Dict]:
        """ID로 단어 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, word, length, jamos, frequency FROM words WHERE id = ?', (word_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'word': result[1],
                'length': result[2],
                'jamos': result[3],
                'frequency': result[4]
            }
        return None
    
    def get_word_by_name(self, word: str) -> Optional[Dict]:
        """단어명으로 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, word, length, jamos, frequency FROM words WHERE word = ?', (word,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'word': result[1],
                'length': result[2],
                'jamos': result[3],
                'frequency': result[4]
            }
        return None
    
    def get_words_by_length(self, length: int) -> List[Dict]:
        """특정 길이의 모든 단어 조회 (빈도순 정렬)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, word, length, jamos, frequency FROM words WHERE length = ? ORDER BY frequency DESC, word', (length,))
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'word': row[1],
                'length': row[2],
                'jamos': row[3],
                'frequency': row[4]
            }
            for row in results
        ]
    
    def search_words_by_jamo_pattern(self, length: int, known_positions: Dict[int, str] = None, 
                                   excluded_jamos: List[str] = None) -> List[Dict]:
        """
        자모음 패턴으로 단어 검색 (Wordle 게임용, 빈도순 정렬)
        
        Args:
            length: 단어 길이
            known_positions: {위치: 자모음} - 확정된 자모음 위치
            excluded_jamos: 제외할 자모음 리스트
            
        Returns:
            조건에 맞는 단어 리스트
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 기본 쿼리
        query = "SELECT id, word, length, jamos, frequency FROM words WHERE length = ?"
        params = [length]
        
        # 확정된 위치 조건 추가
        if known_positions:
            for pos, jamo in known_positions.items():
                # SQLite의 substr 함수 사용 (1-based index)
                query += f" AND substr(jamos, {pos + 1}, 1) = ?"
                params.append(jamo)
        
        # 제외할 자모음 조건 추가
        if excluded_jamos:
            for jamo in excluded_jamos:
                query += f" AND jamos NOT LIKE ?"
                params.append(f"%{jamo}%")
        
        query += " ORDER BY frequency DESC, word"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'word': row[1],
                'length': row[2],
                'jamos': row[3],
                'frequency': row[4]
            }
            for row in results
        ]
    
    def get_jamo_frequency_by_position(self, length: int) -> Dict[int, Dict[str, int]]:
        """
        위치별 자모음 빈도 분석
        
        Args:
            length: 분석할 단어 길이
            
        Returns:
            {위치: {자모음: 개수}} 형태의 딕셔너리
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT jamos FROM words WHERE length = ?', (length,))
        words = cursor.fetchall()
        conn.close()
        
        position_freq = {}
        
        for word_tuple in words:
            jamos = word_tuple[0]
            for pos, jamo in enumerate(jamos):
                if pos not in position_freq:
                    position_freq[pos] = {}
                if jamo not in position_freq[pos]:
                    position_freq[pos][jamo] = 0
                position_freq[pos][jamo] += 1
        
        return position_freq
    
    def get_statistics(self) -> Dict:
        """데이터베이스 통계 정보"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 전체 단어 수
        cursor.execute('SELECT COUNT(*) FROM words')
        total_words = cursor.fetchone()[0]
        
        # 길이별 분포
        cursor.execute('SELECT length, COUNT(*) FROM words GROUP BY length ORDER BY length')
        length_dist = dict(cursor.fetchall())
        
        # 메타데이터
        cursor.execute('SELECT key, value FROM metadata')
        metadata = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_words': total_words,
            'length_distribution': length_dist,
            'metadata': metadata,
            'db_path': self.db_path,
            'db_size_mb': round(os.path.getsize(self.db_path) / 1024 / 1024, 2) if os.path.exists(self.db_path) else 0
        }
    
    def export_to_json(self, output_path: str, length: int = None) -> bool:
        """
        데이터를 JSON 파일로 내보내기
        
        Args:
            output_path: 출력 파일 경로
            length: 특정 길이만 내보내기 (None이면 전체)
            
        Returns:
            내보내기 성공 여부
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if length is not None:
                cursor.execute('SELECT word, length, jamos, frequency FROM words WHERE length = ? ORDER BY frequency DESC, word', (length,))
            else:
                cursor.execute('SELECT word, length, jamos, frequency FROM words ORDER BY length, frequency DESC, word')
            
            words = [
                {
                    'word': row[0],
                    'length': row[1],
                    'jamos': row[2],
                    'frequency': row[3]
                }
                for row in cursor.fetchall()
            ]
            
            conn.close()
            
            export_data = {
                'export_date': datetime.now().isoformat(),
                'total_words': len(words),
                'filter_length': length,
                'words': words
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"JSON 내보내기 오류: {e}")
            return False
    
    def export_to_sql(self, output_path: str) -> bool:
        """
        데이터베이스를 SQL 파일로 백업
        
        Args:
            output_path: 출력 SQL 파일 경로
            
        Returns:
            백업 성공 여부
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                # SQL 덤프 생성
                for line in conn.iterdump():
                    f.write(line + '\n')
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"SQL 백업 오류: {e}")
            return False
    
    def import_from_sql(self, sql_path: str) -> bool:
        """
        SQL 파일에서 데이터베이스 복원
        
        Args:
            sql_path: SQL 파일 경로
            
        Returns:
            복원 성공 여부
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            with open(sql_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
                conn.executescript(sql_script)
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"SQL 복원 오류: {e}")
            return False
    
    def clear_all_words(self) -> bool:
        """모든 단어 데이터 삭제 (주의!)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM words')
            cursor.execute('''
                INSERT OR REPLACE INTO metadata (key, value, updated_at) 
                VALUES ('last_clear', ?, ?)
            ''', (datetime.now().isoformat(), datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"데이터 삭제 오류: {e}")
            return False

# 사용 예시
if __name__ == "__main__":
    import argparse
    import sys
    from pathlib import Path

    # src 폴더에서 실행할 때를 대비해 경로 설정
    current_dir = Path(__file__).parent
    sys.path.append(str(current_dir))

    from word_processor import WordProcessor

    # 1. Command-line argument parser 설정
    parser = argparse.ArgumentParser(description="한국어 단어 사전을 위한 SQLite 데이터베이스를 생성합니다.")
    parser.add_argument(
        '--full',
        action='store_true',
        help="'korean_word_clean_list_big.txt'를 사용하여 빈도수 없는 전체 단어 DB('korean_words_full.db')를 생성합니다."
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help="기존 데이터베이스 파일이 있으면 덮어씁니다."
    )
    args = parser.parse_args()

    # 2. --full 플래그에 따라 입출력 파일 결정
    if args.full:
        # 빈도수 없는 전체 단어 DB 생성
        input_filename = "korean_word_clean_list_big.txt"
        output_filename = "korean_words_full.db"
        is_full_mode = True
        print("\n=== 전체 단어 DB (korean_words_full.db) 구축 모드 ===")
    else:
        # 빈도수 포함된 기본 단어 DB 생성
        input_filename = "korean_word_clean_list.txt"
        output_filename = "korean_words.db"
        is_full_mode = False
        print("\n=== 기본 단어 DB (korean_words.db) 구축 모드 ===")

    # 프로젝트 루트를 기준으로 상대 경로를 절대 경로로 변환
    project_root = Path(__file__).parent.parent
    input_file_path = project_root / "data" / input_filename
    output_db_path = project_root / "data" / output_filename

    # 3. 파일 존재 여부 확인
    if not input_file_path.exists():
        print(f"❌ 오류: 입력 파일 '{input_file_path}'를 찾을 수 없습니다.")
        sys.exit(1)

    if output_db_path.exists() and not args.force:
        overwrite = input(f"⚠️ 경고: 출력 파일 '{output_db_path}'가 이미 존재합니다. 덮어쓰시겠습니까? (y/n): ").lower()
        if overwrite != 'y':
            print("작업을 취소했습니다.")
            sys.exit(0)

    # 4. DB 구축 프로세스 실행
    print(f"📖 입력 파일: data/{input_filename}")
    print(f"💾 출력 DB:   data/{output_filename}")

    try:
        processor = WordProcessor()
        words_data = []

        print(f"\n📖 텍스트 파일 처리 중...")
        with open(input_file_path, 'r', encoding='utf-8') as f:
            if is_full_mode:
                # korean_word_clean_list_big.txt (단어만 있는 파일) 처리
                for line in f:
                    word = line.strip()
                    if word and processor.is_valid_hangul(word):
                        word_data = processor.create_word_data(word)
                        # frequency는 DB 스키마의 기본값 0으로 저장됨
                        words_data.append(word_data)
            else:
                # korean_word_clean_list.txt ('단어 빈도수' 형식) 처리
                for line in f:
                    parts = line.strip().split()
                    if len(parts) == 2:
                        word, freq_str = parts
                        try:
                            frequency = int(freq_str)
                            if processor.is_valid_hangul(word):
                                word_data = processor.create_word_data(word)
                                word_data['frequency'] = frequency
                                words_data.append(word_data)
                        except ValueError:
                            continue # 빈도 값이 숫자가 아니면 무시

        print(f"✅ {len(words_data)}개 유효 단어 처리 완료")

        db = WordDatabase(db_path=str(output_db_path))

        print("💾 기존 데이터 삭제 및 DB 초기화 중...")
        db.clear_all_words()

        print("💾 데이터베이스에 단어 삽입 중...")
        result = db.bulk_insert(words_data)

        print("\n🎉 DB 구축 완료!")
        print(f"  - 삽입된 단어: {result['inserted']}개")
        print(f"  - 중복 단어: {result['duplicated']}개 (무시됨)")
        print(f"  - 오류: {result['errors']}개")

        print("\n📊 최종 데이터베이스 통계:")
        stats = db.get_statistics()
        print(f"  - 총 단어 수: {stats['total_words']:,}개")
        print(f"  - DB 크기: {stats['db_size_mb']}MB")

    except Exception as e:
        print(f"\n❌ 처리 중 심각한 오류 발생: {e}")
        sys.exit(1)
