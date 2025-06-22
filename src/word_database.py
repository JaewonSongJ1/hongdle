import sqlite3
import json
import os
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from pathlib import Path

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
        """데이터베이스 테이블 생성 및 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # words 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT UNIQUE NOT NULL,
                length INTEGER NOT NULL,
                jamos TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 메타데이터 테이블 생성 (DB 정보 저장용)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 인덱스 생성
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_length ON words(length)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_jamos ON words(jamos)')
        
        # 메타데이터 초기화
        cursor.execute('''
            INSERT OR IGNORE INTO metadata (key, value) 
            VALUES ('db_version', '1.0')
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
            word_data: WordProcessor에서 생성한 단어 데이터
            
        Returns:
            삽입 성공 여부
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO words (word, length, jamos)
                VALUES (?, ?, ?)
            ''', (word_data['word'], word_data['length'], word_data['jamos']))
            
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
            words_data: WordProcessor에서 생성한 단어 데이터 리스트
            
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
                        INSERT OR IGNORE INTO words (word, length, jamos)
                        VALUES (?, ?, ?)
                    ''', (word_data['word'], word_data['length'], word_data['jamos']))
                    
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
        
        cursor.execute('SELECT id, word, length, jamos FROM words WHERE id = ?', (word_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'word': result[1],
                'length': result[2],
                'jamos': result[3]
            }
        return None
    
    def get_word_by_name(self, word: str) -> Optional[Dict]:
        """단어명으로 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, word, length, jamos FROM words WHERE word = ?', (word,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'word': result[1],
                'length': result[2],
                'jamos': result[3]
            }
        return None
    
    def get_words_by_length(self, length: int) -> List[Dict]:
        """특정 길이의 모든 단어 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, word, length, jamos FROM words WHERE length = ? ORDER BY word', (length,))
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'word': row[1],
                'length': row[2],
                'jamos': row[3]
            }
            for row in results
        ]
    
    def search_words_by_jamo_pattern(self, length: int, known_positions: Dict[int, str] = None, 
                                   excluded_jamos: List[str] = None) -> List[Dict]:
        """
        자모음 패턴으로 단어 검색 (Wordle 게임용)
        
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
        query = "SELECT id, word, length, jamos FROM words WHERE length = ?"
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
        
        query += " ORDER BY word"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'word': row[1],
                'length': row[2],
                'jamos': row[3]
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
                cursor.execute('SELECT word, length, jamos FROM words WHERE length = ? ORDER BY word', (length,))
            else:
                cursor.execute('SELECT word, length, jamos FROM words ORDER BY length, word')
            
            words = [
                {
                    'word': row[0],
                    'length': row[1],
                    'jamos': row[2]
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
    import sys
    from pathlib import Path
    
    # src 폴더에서 실행할 때를 대비해 경로 설정
    current_dir = Path(__file__).parent
    sys.path.append(str(current_dir))
    
    from word_processor import WordProcessor
    
    print("=== 한국어 단어 DB 구축 및 테스트 ===")
    
    # 초기화 (자동으로 프로젝트의 data 폴더 사용)
    processor = WordProcessor()
    db = WordDatabase()
    
    # 텍스트 파일 경로 (상대경로로 변경)
    project_root = Path(__file__).parent.parent
    text_file_path = project_root / "data" / "korean_words_clean_v2.txt"
    
    # 파일 존재 확인
    if text_file_path.exists():
        print(f"📖 텍스트 파일 처리 중: {text_file_path}")
        
        try:
            # 텍스트 파일에서 단어 데이터 처리
            words_data = processor.parse_text_file(str(text_file_path))
            print(f"✅ {len(words_data)}개 단어 처리 완료")
            
            # 기존 데이터 삭제 후 새로 구축
            print("💾 기존 데이터 삭제 중...")
            db.clear_all_words()
            
            # DB에 일괄 삽입
            print("💾 데이터베이스 구축 중...")
            result = db.bulk_insert(words_data)
            
            print(f"✅ DB 구축 완료!")
            print(f"  - 삽입된 단어: {result['inserted']}개")
            print(f"  - 중복 단어: {result['duplicated']}개")
            print(f"  - 오류: {result['errors']}개")
            
        except Exception as e:
            print(f"❌ 처리 중 오류: {e}")
            # 샘플 단어로 테스트
            print("📝 샘플 단어로 테스트 진행...")
            sample_words = ["개나리", "클로드", "안녕하세요", "프로그램", "컴퓨터"]
            
            for word in sample_words:
                if processor.is_valid_word(word):
                    word_data = processor.create_word_data(word)
                    success = db.insert_word(word_data)
                    print(f"  {word}: {'저장됨' if success else '실패 또는 중복'}")
    else:
        print(f"❌ 텍스트 파일을 찾을 수 없습니다: {text_file_path}")
        print("📝 샘플 단어로 테스트 진행...")
        
        # 샘플 단어들로 테스트
        sample_words = ["개나리", "클로드", "안녕하세요", "프로그램", "컴퓨터", "데이터베이스"]
        
        for word in sample_words:
            if processor.is_valid_word(word):
                word_data = processor.create_word_data(word)
                success = db.insert_word(word_data)
                print(f"  {word}: {'저장됨' if success else '실패 또는 중복'}")
    
    # 데이터베이스 통계 및 테스트
    print("\n📊 데이터베이스 통계:")
    stats = db.get_statistics()
    print(f"  총 단어 수: {stats['total_words']:,}개")
    print(f"  DB 크기: {stats['db_size_mb']}MB")
    print(f"  DB 위치: {stats['db_path']}")
    
    if stats['length_distribution']:
        print(f"  길이별 분포:")
        for length, count in sorted(stats['length_distribution'].items()):
            print(f"    {length}자모음: {count:,}개")
    
    # 샘플 검색 테스트
    if stats['total_words'] > 0:
        print("\n🔍 검색 테스트:")
        
        # 6자모음 단어 조회
        words_6 = db.get_words_by_length(6)
        if words_6:
            print(f"  6자모음 단어 (상위 5개):")
            for i, word_info in enumerate(words_6[:5]):
                print(f"    {i+1}. {word_info['word']} -> {word_info['jamos']}")
        
        # 게임용 패턴 검색 테스트
        search_result = db.search_words_by_jamo_pattern(
            length=6,
            known_positions={1: 'ㅐ'}  # 2번째 자리에 'ㅐ'
        )
        
        if search_result:
            print(f"  2번째 자리에 'ㅐ'가 있는 6자모음 단어: {len(search_result)}개")
            for i, word_info in enumerate(search_result[:3]):
                print(f"    {i+1}. {word_info['word']} -> {word_info['jamos']}")
    
    print(f"\n🎉 테스트 완료!")
    print(f"✅ DB 파일: {db.db_path}")
    print(f"이제 이 DB를 사용해서 게임 로직을 개발할 수 있습니다!")