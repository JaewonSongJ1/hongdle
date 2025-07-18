"""
홍들(Wordle) 최적의 시작 단어 탐색기

기능:
1. 지정된 자모음 길이에 해당하는 단어를 DB에서 조회합니다.
2. 각 단어의 자모음이 중복되지 않는 단어만 필터링합니다. (최적의 시작 단어 조건)
3. 필터링된 단어들을 빈도수(frequency) 기준으로 정렬합니다.
4. 결과를 텍스트 파일로 저장하며, 상세 정보(빈도, 자모음) 포함 여부를 선택할 수 있습니다.
"""

import sys
from pathlib import Path
import argparse

# --- 경로 설정 ---
# 이 스크립트는 'misc' 폴더에 있으므로, 'src' 폴더를 경로에 추가해야
# WordDatabase 같은 모듈을 임포트할 수 있습니다.
current_dir = Path(__file__).parent
project_root = current_dir.parent
src_dir = project_root / 'src'
sys.path.append(str(src_dir))

# 이제 src 폴더의 모듈을 임포트할 수 있습니다.
from word_database import WordDatabase

def find_optimal_starting_words(lengths: list[int], output_dir: Path, include_details: bool):
    """
    빈도수가 높고 자모음이 중복되지 않는 최적의 시작 단어를 찾아 파일로 저장합니다.
    """
    print("🚀 최적의 시작 단어 찾기를 시작합니다...")

    # 1. 데이터베이스 경로 설정
    db_path = project_root / 'data' / 'korean_words_full.db'
    
    if not db_path.exists():
        print(f"❌ 오류: 데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        return

    db = WordDatabase(str(db_path))
    stats = db.get_statistics()
    print(f"📚 데이터베이스 로드 완료: 총 {stats['total_words']:,}개 단어")

    # 출력 디렉토리 생성
    output_dir.mkdir(parents=True, exist_ok=True)

    # 2. 각 목표 길이에 대해 분석
    for length in lengths:
        print(f"\n🔍 [{length}자모음 단어 분석 중...]")
        
        # 3. 해당 길이의 모든 단어 가져오기
        # get_words_by_length는 이미 빈도순으로 정렬되어 있습니다.
        all_words_at_length = db.get_words_by_length(length)
        if not all_words_at_length:
            print(f"  - {length}자모음 단어가 데이터베이스에 없습니다.")
            continue
        
        print(f"  - 총 {len(all_words_at_length):,}개의 단어 발견.")

        # 4. 자모음이 중복되지 않는 단어만 필터링
        unique_jamo_words = [
            word_info for word_info in all_words_at_length
            if len(word_info['jamos']) == len(set(word_info['jamos']))
        ]
        print(f"  - 자모음이 중복되지 않는 단어: {len(unique_jamo_words):,}개")

        # 5. 파일로 저장
        output_filename = f"initial_test_{length}jamo.txt"
        output_path = output_dir / output_filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# {length}자모음 최적 시작 단어 후보 (빈도순)\n")
            f.write(f"# 총 {len(unique_jamo_words)}개 단어\n")
            f.write("# ------------------------------------\n")
            for word_info in unique_jamo_words:
                if include_details:
                    # 상세 정보 포함하여 저장
                    line = f"{word_info['word']:<6} (빈도: {word_info['frequency']:<5}) | 자모: {word_info['jamos']}"
                else:
                    # 단어만 저장
                    line = word_info['word']
                f.write(f"{line}\n")
        
        print(f"✅ 결과 저장 완료: {output_path.relative_to(project_root)}")

    print("\n🎉 모든 작업이 완료되었습니다.")

def main():
    parser = argparse.ArgumentParser(
        description="홍들(Wordle) 최적의 시작 단어를 찾아 파일로 저장합니다.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '-l', '--lengths',
        nargs='+',
        type=int,
        default=[5, 6, 7],
        help="분석할 자모음 길이를 공백으로 구분하여 입력합니다. (기본값: 5 6 7)"
    )
    parser.add_argument(
        '-o', '--output_dir',
        type=str,
        default=str(project_root / 'data'),
        help=f"결과 파일을 저장할 디렉토리입니다. (기본값: data/)"
    )
    parser.add_argument(
        '--details',
        action='store_true',
        help="출력 파일에 단어의 빈도수와 자모음 정보를 포함합니다."
    )
    
    args = parser.parse_args()
    
    find_optimal_starting_words(
        lengths=args.lengths,
        output_dir=Path(args.output_dir),
        include_details=args.details
    )

if __name__ == "__main__":
    main()