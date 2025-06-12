#!/usr/bin/env python3
"""
한국어 Wordle (홍들) 게임 플레이어

사용법:
    python play_hongdle.py
"""

import sys
from pathlib import Path

# src 폴더의 모듈들 import
current_dir = Path(__file__).parent
src_dir = current_dir.parent / 'src'
sys.path.append(str(src_dir))

from game_engine import GameEngine

def play_cumulative_game():
    """누적 조건 게임 플레이"""
    print("🎮 한국어 Wordle (홍들) - 누적 게임")
    print("=" * 50)
    print("여러 턴에 걸쳐 조건을 누적해가며 정답을 찾는 모드입니다.")
    print("입력 형식: 단어 패턴 (예: 비상구 BYBBYBB)")
    print("패턴: B(Black/없음), Y(Yellow/위치틀림), G(Green/정확)")
    print("종료: 'quit' 입력")
    print("-" * 50)
    
    engine = GameEngine()
    
    while True:
        try:
            print(f"\n현재 턴: {len(engine.turns) + 1}")
            
            # 현재 상태 표시
            if engine.turns:
                candidates = engine.get_current_candidates()
                print(f"현재 후보: {len(candidates)}개")
            
            # 사용자 입력
            user_input = input("\n입력 (단어 패턴): ").strip()
            
            if user_input.lower() == 'quit':
                break
            
            # 입력 파싱
            parts = user_input.split()
            if len(parts) != 2:
                print("❌ 입력 형식이 잘못되었습니다. (예: 비상구 BYBBYBB)")
                continue
            
            word, pattern = parts
            
            # 패턴 검증
            if not all(c in 'BYG' for c in pattern):
                print("❌ 패턴은 B, Y, G만 사용 가능합니다.")
                continue
            
            # 턴 실행
            candidates = engine.add_turn(word, pattern)
            
            # 결과 확인
            if len(candidates) == 1:
                print(f"\n🎉 정답을 찾았습니다: {candidates[0]}")
                break
            elif len(candidates) == 0:
                print("\n❌ 조건에 맞는 단어가 없습니다. 입력을 확인해주세요.")
            
        except ValueError as e:
            print(f"❌ 오류: {e}")
        except KeyboardInterrupt:
            print("\n게임을 종료합니다.")
            break
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")
    
    # 게임 요약
    if engine.turns:
        engine.show_game_summary()

def play_single_analysis():
    """단일 턴 분석 모드"""
    print("🔍 한국어 Wordle (홍들) - 단일 분석")
    print("=" * 50)
    print("한 번의 입력으로 조건에 맞는 모든 후보를 찾는 모드입니다.")
    print("입력 형식: 단어 패턴 (예: 컴퓨터 BYBGYBY)")
    print("패턴: B(Black/없음), Y(Yellow/위치틀림), G(Green/정확)")
    print("종료: 'quit' 입력")
    print("-" * 50)
    
    engine = GameEngine()
    
    while True:
        try:
            # 사용자 입력
            user_input = input("\n입력 (단어 패턴): ").strip()
            
            if user_input.lower() == 'quit':
                break
            
            # 입력 파싱
            parts = user_input.split()
            if len(parts) != 2:
                print("❌ 입력 형식이 잘못되었습니다. (예: 컴퓨터 BYBGYBY)")
                continue
            
            word, pattern = parts
            
            # 패턴 검증
            if not all(c in 'BYG' for c in pattern):
                print("❌ 패턴은 B, Y, G만 사용 가능합니다.")
                continue
            
            # 분석 실행
            candidates = engine.single_turn_analysis(word, pattern)
            
            print(f"\n분석 완료: {len(candidates)}개 후보")
            
        except ValueError as e:
            print(f"❌ 오류: {e}")
        except KeyboardInterrupt:
            print("\n분석을 종료합니다.")
            break
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")

def play_demo():
    """데모 게임"""
    print("🎬 한국어 Wordle (홍들) - 데모")
    print("=" * 50)
    
    engine = GameEngine()
    
    print("데모 시나리오: 정답 단어를 '놀이터'라고 가정")
    print("플레이어가 다음과 같이 추측한다고 해봅시다:")
    print()
    
    # 데모 시나리오
    demo_turns = [
        ("비상구", "BYBBYBB", "첫 번째 추측"),
        ("놀이터", "BBBGGBY", "두 번째 추측"),
    ]
    
    for i, (word, pattern, description) in enumerate(demo_turns, 1):
        print(f"[ 턴 {i}: {description} ]")
        print(f"추측: {word}")
        print(f"결과: {pattern}")
        
        candidates = engine.add_turn(word, pattern)
        
        print(f"남은 후보: {len(candidates)}개")
        
        if len(candidates) <= 5:
            print("후보 단어들:")
            for j, candidate in enumerate(candidates, 1):
                print(f"  {j}. {candidate}")
        
        print("-" * 30)
    
    engine.show_game_summary()

def show_optimal_words():
    """최적 시작 단어 보기"""
    print("💡 최적 시작 단어 추천")
    print("=" * 50)
    
    data_dir = Path(__file__).parent.parent / 'data'
    
    for length in [5, 6, 7]:
        file_path = data_dir / f"optimal_words_{length}jamos.txt"
        
        if file_path.exists():
            print(f"\n[ {length}자모음 최적 단어 TOP 10 ]")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                # 헤더 건너뛰고 상위 10개만
                data_lines = [line for line in lines if not line.startswith('#') and line.strip()]
                
                for i, line in enumerate(data_lines[:10], 1):
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        word = parts[0]
                        jamos = parts[1]
                        print(f"  {i:2d}. {word:<8} → {jamos}")
                    
            except Exception as e:
                print(f"파일 읽기 오류: {e}")
        else:
            print(f"\n[ {length}자모음 ]: 파일이 없습니다 ({file_path})")
    
    print(f"\n💡 팁: 자모음이 중복되지 않는 단어가 가장 효율적입니다!")

def main():
    """메인 메뉴"""
    while True:
        print("\n" + "=" * 60)
        print("🎮 한국어 Wordle (홍들) 게임")
        print("=" * 60)
        print("1. 누적 게임 (여러 턴으로 정답 찾기)")
        print("2. 단일 분석 (한 번에 모든 후보 찾기)")
        print("3. 데모 게임 보기")
        print("4. 최적 시작 단어 추천")
        print("5. 종료")
        print("-" * 60)
        
        try:
            choice = input("선택 (1-5): ").strip()
            
            if choice == '1':
                play_cumulative_game()
            elif choice == '2':
                play_single_analysis()
            elif choice == '3':
                play_demo()
            elif choice == '4':
                show_optimal_words()
            elif choice == '5':
                print("게임을 종료합니다. 안녕히 가세요! 👋")
                break
            else:
                print("❌ 1-5 중에서 선택해주세요.")
                
        except KeyboardInterrupt:
            print("\n\n게임을 종료합니다. 안녕히 가세요! 👋")
            break
        except Exception as e:
            print(f"❌ 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()