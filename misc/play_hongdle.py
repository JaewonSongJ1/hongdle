#!/usr/bin/env python3
"""
한국어 Wordle (홍들) 게임 플레이어 - 간소화 버전 (누적 게임 전용)

사용법:
    python hongdle_game.py
"""

import sys
from pathlib import Path

# src 폴더의 모듈들 import
current_dir = Path(__file__).parent
src_dir = current_dir.parent / 'src'
sys.path.append(str(src_dir))

from game_engine import GameEngine

def play_hongdle_game():
    """한국어 Wordle 누적 게임"""
    print("🎮 한국어 Wordle (홍들)")
    print("=" * 50)
    print("여러 턴에 걸쳐 조건을 누적해가며 정답을 찾는 게임입니다.")
    print()
    print("📋 입력 형식: 단어 패턴")
    print("   예시: 세제 GYBBBG")
    print()
    print("🎨 패턴 설명:")
    print("   B(Black): 등장하지 않음")
    print("   Y(Yellow): 등장하지만 위치 틀림") 
    print("   G(Green): 등장하고 위치 정확")
    print()
    print("💡 핵심 규칙:")
    print("   - Y와 B가 같이 나타나면 정확한 개수가 확정됩니다")
    print("   - 예: ㅓ가 Y 1개 + B 1개 = ㅓ는 정확히 1개만 존재")
    print()
    print("종료: 'quit' 또는 'q' 입력")
    print("-" * 50)
    
    engine = GameEngine()
    
    # DB 상태 확인
    stats = engine.db.get_statistics()
    print(f"📚 데이터베이스: 총 {stats['total_words']:,}개 단어 준비완료")
    
    if stats['total_words'] == 0:
        print("❌ 데이터베이스가 비어있습니다.")
        return
    
    while True:
        try:
            print(f"\n🎯 현재 턴: {len(engine.turns) + 1}")
            
            # 현재 상태 표시
            if engine.turns:
                candidates = engine.get_current_candidates()
                print(f"📊 현재 후보: {len(candidates):,}개")
                
                # 후보가 적으면 일부 표시
                if 1 <= len(candidates) <= 5:
                    print("🎪 남은 후보들:")
                    for i, word in enumerate(candidates, 1):
                        jamos = engine.processor.decompose_to_string(word)
                        print(f"   {i}. {word} ({' '.join(list(jamos))})")
            
            # 사용자 입력
            user_input = input("\n✏️  입력 (단어 패턴): ").strip()
            
            if user_input.lower() in ['quit', 'q']:
                break
            
            # 빈 입력 처리
            if not user_input:
                print("💭 도움말을 보려면 'help'를 입력하세요.")
                continue
            
            # 도움말
            if user_input.lower() == 'help':
                print("\n📖 도움말:")
                print("   입력 형식: [단어] [패턴]")
                print("   예시: 세제 GYBBBG")
                print("   패턴: G(정확) Y(위치틀림) B(없음)")
                print("   종료: quit 또는 q")
                continue
            
            # 입력 파싱
            parts = user_input.split()
            if len(parts) != 2:
                print("❌ 입력 형식이 잘못되었습니다.")
                print("   올바른 형식: 세제 GYBBBG")
                continue
            
            word, pattern = parts
            
            # 패턴 검증
            if not all(c.upper() in 'BYG' for c in pattern):
                print("❌ 패턴은 B, Y, G만 사용 가능합니다.")
                continue
            
            pattern = pattern.upper()  # 대문자로 변환
            
            # 턴 실행
            candidates = engine.add_turn(word, pattern)
            
            # 결과 확인
            if len(candidates) == 1:
                print(f"\n🎉 정답을 찾았습니다: {candidates[0]}")
                jamos = engine.processor.decompose_to_string(candidates[0])
                print(f"🔤 자모음 분해: {' '.join(list(jamos))}")
                
                play_again = input("\n🔄 다시 플레이하시겠습니까? (y/n): ").strip().lower()
                if play_again in ['y', 'yes', '네', 'ㅇ']:
                    engine.reset_game()
                    print("\n🆕 새 게임을 시작합니다!")
                    continue
                else:
                    break
                    
            elif len(candidates) == 0:
                print("\n❌ 조건에 맞는 단어가 없습니다!")
                print("🤔 입력을 다시 확인해주세요.")
                
                retry = input("   마지막 턴을 되돌리시겠습니까? (y/n): ").strip().lower()
                if retry in ['y', 'yes', '네', 'ㅇ']:
                    if engine.turns:
                        engine.turns.pop()  # 마지막 턴 제거
                        engine.reset_game()  # 조건 재계산
                        for turn in engine.turns:
                            engine._update_conditions(turn['jamos'], turn['pattern'])
                        print("↩️  마지막 턴이 취소되었습니다.")
                    else:
                        print("취소할 턴이 없습니다.")
            
            elif len(candidates) <= 10:
                print(f"\n🎯 후보가 {len(candidates)}개로 줄어들었습니다!")
                
            elif len(candidates) >= 1000:
                print(f"\n📈 아직 후보가 {len(candidates):,}개나 남았습니다.")
                print("💡 더 구체적인 조건이 필요해요!")
            
        except ValueError as e:
            print(f"❌ 오류: {e}")
            print("💡 단어와 패턴의 길이가 일치하는지 확인해주세요.")
        except KeyboardInterrupt:
            print("\n\n👋 게임을 종료합니다.")
            break
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")
            print("🔧 오류가 지속되면 개발자에게 문의해주세요.")
    
    # 게임 종료 시 요약
    if engine.turns:
        print("\n" + "="*50)
        engine.show_game_summary()
        print("="*50)
    
    print("\n🎮 한국어 Wordle을 플레이해주셔서 감사합니다!")
    print("👋 또 만나요!")

def main():
    """메인 함수"""
    try:
        play_hongdle_game()
    except KeyboardInterrupt:
        print("\n\n👋 게임을 종료합니다. 안녕히 가세요!")
    except Exception as e:
        print(f"\n❌ 게임 실행 중 오류가 발생했습니다: {e}")
        print("🔧 문제가 지속되면 개발자에게 문의해주세요.")

if __name__ == "__main__":
    main()