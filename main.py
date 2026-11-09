"""퀴즈 게임 도메인 모델, 영속성 관리 및 실행 엔트리포인트."""

from __future__ import annotations

import json
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Any


class Quiz:
    """개별 퀴즈를 표현하는 클래스.

    Attributes:
        question: 문제 질문 문구
        choices: 4개의 보기 목록 (문자열 리스트)
        answer: 정답 번호 (1 ~ 4)
        hint: 힌트 문구 (보너스 기능)
    """

    def __init__(
        self,
        question: str,
        choices: list[str],
        answer: int,
        hint: str = "",
    ) -> None:
        if not isinstance(choices, list) or len(choices) != 4:
            raise ValueError("선택지는 정확히 4개여야 합니다.")
        if not (1 <= answer <= 4):
            raise ValueError("정답 번호는 1에서 4 사이의 정수여야 합니다.")

        self.question = question.strip()
        self.choices = [str(c).strip() for c in choices]
        self.answer = int(answer)
        self.hint = hint.strip()

    def display(self, index: int | None = None) -> None:
        """문제와 선택지 목록을 포맷팅하여 콘솔에 출력합니다."""
        header = f"[문제 {index}]" if index is not None else "[문제]"
        print(f"\n{header} {self.question}")
        for i, choice in enumerate(self.choices, start=1):
            print(f"  {i}. {choice}")

    def get_hint(self) -> str:
        """등록된 힌트 문구를 반환합니다. 힌트가 없을 경우 기본 안내 문구를 반환합니다."""
        if self.hint:
            return f"💡 [힌트] {self.hint}"
        return "💡 이 문제에는 등록된 힌트가 없습니다."

    def is_correct(self, user_choice: int) -> bool:
        """사용자가 입력한 번호가 정답과 일치하는지 확인합니다."""
        return user_choice == self.answer

    def to_dict(self) -> dict[str, Any]:
        """JSON 저장을 위해 Quiz 객체를 딕셔너리로 변환합니다."""
        return {
            "question": self.question,
            "choices": self.choices,
            "answer": self.answer,
            "hint": self.hint,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Quiz:
        """딕셔너리 데이터로부터 Quiz 객체를 생성하여 반환합니다."""
        return cls(
            question=data.get("question", ""),
            choices=data.get("choices", []),
            answer=int(data.get("answer", 1)),
            hint=data.get("hint", ""),
        )

    def __repr__(self) -> str:
        return f"<Quiz question={self.question!r} answer={self.answer}>"


def get_default_quizzes() -> list[Quiz]:
    """초기 실행 또는 복구 시 제공되는 기본 퀴즈 5문항을 반환합니다."""
    return [
        Quiz(
            question="파이썬에서 불변(immutable) 시퀀스 자료형은 무엇인가요?",
            choices=["list", "tuple", "set", "dict"],
            answer=2,
            hint="소괄호 '()'로 정의하며 한 번 생성되면 요소를 수정하거나 삭제할 수 없습니다.",
        ),
        Quiz(
            question="파이썬에서 리스트의 맨 끝에 새로운 요소를 추가하는 메서드는?",
            choices=["append()", "push()", "add()", "insert()"],
            answer=1,
            hint="JavaScript의 push()와 유사하며 단일 항목을 끝에 덧붙입니다.",
        ),
        Quiz(
            question="두 변수가 메모리 상에서 동일한 객체를 가리키고 있는지 비교하는 연산자는?",
            choices=["==", "equals", "is", "match"],
            answer=3,
            hint="값(동등성) 비교가 아닌 고유 id(동일성)를 비교하는 키워드입니다.",
        ),
        Quiz(
            question="다음 중 파이썬에서 참(True)으로 평가되는(Truthy) 값은?",
            choices=["0", "[] (빈 리스트)", "\"\" (빈 문자열)", "[0] (원소가 0인 리스트)"],
            answer=4,
            hint="비어있지 않은 컨테이너 객체는 내부 원소 값과 무관하게 참으로 평가됩니다.",
        ),
        Quiz(
            question="파이썬 함수에서 명시적인 return 문이 없을 때 기본으로 반환되는 객체는?",
            choices=["0", "False", "None", "undefined"],
            answer=3,
            hint="파이썬에서 '값이 없음'을 나타내는 유일한 싱글톤 객체입니다.",
        ),
    ]


class QuizGame:
    """퀴즈 게임의 상태 관리, 사용자 인터랙션 및 전반적인 게임 진행을 담당하는 클래스."""

    def __init__(self, state_file: str | Path = "state.json") -> None:
        self.state_file = Path(state_file)
        self.quizzes: list[Quiz] = []
        self.best_score: int = 0
        self.history: list[dict[str, Any]] = []

    # -------------------------------------------------------------------------
    # 영속성 (state.json) 관리 메서드
    # -------------------------------------------------------------------------
    def load_state(self) -> None:
        """state.json 파일에서 퀴즈와 게임 기록을 불러옵니다.

        파일이 없거나 손상되었을 경우 기본 퀴즈 데이터로 복구 및 초기화합니다.
        """
        if not self.state_file.exists():
            print("📂 저장된 데이터 파일이 없습니다. 기본 퀴즈 데이터를 로드합니다.")
            self.reset_to_default_state()
            self.save_state()
            return

        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            raw_quizzes = data.get("quizzes", [])
            loaded_quizzes = [Quiz.from_dict(q) for q in raw_quizzes]

            if not loaded_quizzes:
                self.quizzes = get_default_quizzes()
            else:
                self.quizzes = loaded_quizzes

            self.best_score = int(data.get("best_score", 0))
            self.history = list(data.get("history", []))
            print(
                f"📂 저장된 데이터를 불러왔습니다. "
                f"(퀴즈 {len(self.quizzes)}개, 최고점수 {self.best_score}점)"
            )

        except (json.JSONDecodeError, UnicodeDecodeError, ValueError, KeyError) as e:
            print(f"⚠️ 데이터 파일이 손상되었거나 형식이 올바르지 않습니다: {e}")
            print("🔄 기본 퀴즈 데이터로 복구합니다.")
            self.reset_to_default_state()
            self.save_state()
        except OSError as e:
            print(f"⚠️ 데이터 파일을 읽는 중 오류가 발생했습니다: {e}")
            self.reset_to_default_state()

    def save_state(self) -> bool:
        """현재 퀴즈 목록, 최고 점수 및 히스토리를 state.json에 UTF-8로 안전하게 저장합니다.

        원자적 파일 쓰기(atomic write)를 적용하여 저장 중 강제 중단 시에도 파일 손상을 방지합니다.
        """
        data = {
            "best_score": self.best_score,
            "quizzes": [q.to_dict() for q in self.quizzes],
            "history": self.history,
        }
        temp_file = self.state_file.with_suffix(".tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            temp_file.replace(self.state_file)
            return True
        except OSError as e:
            print(f"⚠️ 데이터 파일 저장 중 오류가 발생했습니다: {e}")
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass
            return False

    def reset_to_default_state(self) -> None:
        """상태를 기본 퀴즈 5문항 및 점수 0으로 초기화합니다."""
        self.quizzes = get_default_quizzes()
        self.best_score = 0
        self.history = []

    # -------------------------------------------------------------------------
    # 공통 입력 검증 헬퍼 메서드
    # -------------------------------------------------------------------------
    @staticmethod
    def prompt_text(prompt_msg: str, allow_empty: bool = False) -> str:
        """사용자로부터 텍스트 입력을 받아 앞뒤 공백을 제거한 후 반환합니다."""
        while True:
            user_input = input(prompt_msg).strip()
            if not user_input and not allow_empty:
                print("⚠️ 입력값이 비어 있습니다. 내용을 입력해주세요.")
                continue
            return user_input

    @staticmethod
    def prompt_int(
        prompt_msg: str,
        min_val: int | None = None,
        max_val: int | None = None,
    ) -> int:
        """사용자로부터 정수를 입력받아 범위 및 타입을 엄격하게 검증합니다."""
        range_guide = f"{min_val}-{max_val}" if (min_val is not None and max_val is not None) else "정수"
        while True:
            raw_input = input(prompt_msg).strip()
            if not raw_input:
                print("⚠️ 입력값이 비어 있습니다. 숫자를 입력해주세요.")
                continue

            try:
                val = int(raw_input)
            except ValueError:
                print(f"⚠️ 잘못된 입력입니다. {range_guide} 사이의 숫자를 입력하세요.")
                continue

            if (min_val is not None and val < min_val) or (max_val is not None and val > max_val):
                print(f"⚠️ 잘못된 입력입니다. {range_guide} 사이의 숫자를 입력하세요.")
                continue

            return val

    # -------------------------------------------------------------------------
    # 메뉴 UI 및 메인 루프
    # -------------------------------------------------------------------------
    def display_menu(self) -> None:
        """메인 메뉴 화면을 콘솔에 출력합니다."""
        print("\n" + "=" * 40)
        print("        🎯 나만의 퀴즈 게임 🎯        ")
        print("=" * 40)
        print("  1. 퀴즈 풀기")
        print("  2. 퀴즈 추가")
        print("  3. 퀴즈 목록")
        print("  4. 퀴즈 삭제 (보너스)")
        print("  5. 점수 및 기록 확인 (보너스)")
        print("  6. 종료")
        print("=" * 40)

    def play_quiz(self) -> None:
        """저장된 퀴즈를 출제하고 채점 및 결과를 표시합니다.

        보너스 기능 지원:
        - 문제 수 선택 (1 ~ 전체 퀴즈 수)
        - random 모듈을 통한 랜덤 출제
        - 문항별 힌트 조회('H') 및 힌트 사용 시 점수 차감(50%)
        - 게임 플레이 히스토리 기록
        """
        if not self.quizzes:
            print("\n⚠️ 등록된 퀴즈가 없습니다. 먼저 퀴즈를 추가해주세요.")
            return

        total_available = len(self.quizzes)
        print("\n" + "-" * 40)
        print(f"📋 현재 등록된 퀴즈는 총 {total_available}개입니다.")
        num_to_solve = self.prompt_int(
            f"풀이할 문제 수를 선택하세요 (1 ~ {total_available}): ",
            min_val=1,
            max_val=total_available,
        )

        # 보너스 1: random 모듈을 활용한 랜덤 추출
        selected_quizzes = random.sample(self.quizzes, num_to_solve)

        print("\n" + "-" * 40)
        print(f"📝 퀴즈를 시작합니다! (총 {num_to_solve}문제)")
        print("💡 힌트를 보려면 정답 입력 시 'H'를 입력하세요 (힌트 사용 시 점수 50% 감점).")
        print("-" * 40)

        points_per_question = 100.0 / num_to_solve
        total_earned_score = 0.0
        correct_count = 0
        total_hints_used = 0

        for idx, quiz in enumerate(selected_quizzes, start=1):
            quiz.display(index=idx)
            hint_used = False

            while True:
                user_input = self.prompt_text("정답 입력 (1-4, 힌트보기: H): ").upper()
                if user_input in ("H", "HINT", "0"):
                    if not hint_used:
                        print(quiz.get_hint())
                        hint_used = True
                        total_hints_used += 1
                    else:
                        print("⚠️ 이미 힌트를 확인한 문제입니다.")
                    continue

                if user_input in ("1", "2", "3", "4"):
                    choice = int(user_input)
                    break
                else:
                    print("⚠️ 잘못된 입력입니다. 1-4 사이의 번호 또는 힌트(H)를 입력하세요.")

            if quiz.is_correct(choice):
                if hint_used:
                    earned = points_per_question * 0.5
                    print(f"✅ 정답입니다! (힌트 사용으로 {earned:.1f}점 획득)")
                else:
                    earned = points_per_question
                    print(f"✅ 정답입니다! ({earned:.1f}점 획득)")
                total_earned_score += earned
                correct_count += 1
            else:
                correct_answer_text = quiz.choices[quiz.answer - 1]
                print(f"❌ 틀렸습니다. 정답은 {quiz.answer}번 ({correct_answer_text})입니다.")

        # 최종 점수 계산 (반올림 정수)
        final_score = int(round(total_earned_score))
        print("\n" + "=" * 40)
        print(f"🏆 결과: {num_to_solve}문제 중 {correct_count}문제 정답! ({final_score}점)")
        if total_hints_used > 0:
            print(f"💡 사용한 힌트 수: {total_hints_used}회")

        if final_score > self.best_score:
            print(f"🎉 새로운 최고 점수입니다! ({self.best_score}점 -> {final_score}점)")
            self.best_score = final_score

        # 보너스 5: 히스토리 기록
        record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_questions": num_to_solve,
            "correct_count": correct_count,
            "hints_used": total_hints_used,
            "final_score": final_score,
        }
        self.history.append(record)
        self.save_state()
        print("=" * 40)

    def add_quiz(self) -> None:
        """새로운 퀴즈 정보를 사용자로부터 입력받아 목록 및 state.json에 등록합니다."""
        print("\n" + "=" * 40)
        print("📌 새로운 퀴즈를 추가합니다.")
        print("=" * 40)

        question = self.prompt_text("문제를 입력하세요: ")

        choices: list[str] = []
        for i in range(1, 5):
            choice_text = self.prompt_text(f"선택지 {i}: ")
            choices.append(choice_text)

        answer = self.prompt_int("정답 번호 (1-4): ", min_val=1, max_val=4)
        hint = self.prompt_text(
            "힌트를 입력하세요 (선택 사항, 없으면 Enter): ",
            allow_empty=True,
        )

        new_quiz = Quiz(
            question=question,
            choices=choices,
            answer=answer,
            hint=hint,
        )

        self.quizzes.append(new_quiz)
        if self.save_state():
            print(f"\n✅ 퀴즈가 성공적으로 추가되었습니다! (현재 등록된 퀴즈: 총 {len(self.quizzes)}개)")
        else:
            print("\n⚠️ 퀴즈 추가 중 파일 저장에 실패했습니다.")

    def list_quizzes(self) -> None:
        """현재 등록된 모든 퀴즈 목록을 콘솔에 출력합니다."""
        if not self.quizzes:
            print("\n⚠️ 등록된 퀴즈가 없습니다. 먼저 퀴즈를 추가해주세요.")
            return

        print("\n" + "=" * 50)
        print(f"📋 등록된 퀴즈 목록 (총 {len(self.quizzes)}개)")
        print("-" * 50)
        for idx, quiz in enumerate(self.quizzes, start=1):
            hint_badge = " [💡힌트]" if quiz.hint else ""
            print(f"[{idx}] {quiz.question}{hint_badge}")
        print("=" * 50)

    def delete_quiz(self) -> None:
        """사용자가 선택한 번호의 퀴즈를 목록 및 state.json에서 삭제합니다. (보너스 기능)"""
        if not self.quizzes:
            print("\n⚠️ 삭제할 퀴즈가 없습니다.")
            return

        self.list_quizzes()
        print("\n🗑️ 삭제할 퀴즈의 번호를 입력하세요. (취소하려면 0을 입력)")
        choice = self.prompt_int(
            f"삭제할 번호 (1-{len(self.quizzes)}, 취소: 0): ",
            min_val=0,
            max_val=len(self.quizzes),
        )

        if choice == 0:
            print("삭제 작업을 취소했습니다.")
            return

        target_quiz = self.quizzes[choice - 1]
        print(f"\n선택한 문제: [{choice}] {target_quiz.question}")
        confirm = self.prompt_text("정말 이 퀴즈를 삭제하시겠습니까? (y/n): ").lower()

        if confirm in ("y", "yes"):
            deleted = self.quizzes.pop(choice - 1)
            if self.save_state():
                print(f"\n✅ [{choice}]번 퀴즈 '{deleted.question}'가 성공적으로 삭제되었습니다.")
                print(f"현재 남은 퀴즈: 총 {len(self.quizzes)}개")
            else:
                print("\n⚠️ 퀴즈 삭제 후 파일 저장에 실패했습니다.")
        else:
            print("삭제가 취소되었습니다.")

    def view_scores(self) -> None:
        """역대 최고 점수와 게임 플레이 히스토리 통계를 출력합니다. (보너스 기능 포함)"""
        print("\n" + "=" * 60)
        print("          🏆 점수 및 게임 플레이 기록          ")
        print("=" * 60)

        if not self.history and self.best_score == 0:
            print("⚠️ 아직 퀴즈를 플레이한 기록이 없습니다.")
            print("💡 메뉴에서 '1. 퀴즈 풀기'를 선택하여 게임을 즐겨보세요!")
            print("=" * 60)
            return

        print(f"🥇 역대 최고 점수: {self.best_score}점")

        if self.history:
            print(f"\n📜 게임 플레이 히스토리 (총 {len(self.history)}회 기록)")
            print("-" * 60)
            print(f"{'회차':<4} | {'일시':<19} | {'문제수':<4} | {'정답':<4} | {'힌트':<4} | {'최종점수':<6}")
            print("-" * 60)
            for idx, record in enumerate(self.history, start=1):
                timestamp = record.get("timestamp", "-")
                total_q = record.get("total_questions", 0)
                correct = record.get("correct_count", 0)
                hints = record.get("hints_used", 0)
                score = record.get("final_score", 0)
                print(
                    f"{idx:<4} | {timestamp:<19} | {total_q:<6} | {correct:<4} | {hints:<4} | {score}점"
                )
            print("-" * 60)

            total_plays = len(self.history)
            avg_score = sum(r.get("final_score", 0) for r in self.history) / total_plays
            print(f"📊 통계: 총 {total_plays}회 플레이 | 평균 점수: {avg_score:.1f}점")

        print("=" * 60)

    def run(self) -> None:
        """게임을 시작하고 사용자 입력을 처리하는 메인 이벤트 루프."""
        print("🚀 퀴즈 게임 프로그램을 시작합니다.")
        self.load_state()

        menu_actions = {
            1: self.play_quiz,
            2: self.add_quiz,
            3: self.list_quizzes,
            4: self.delete_quiz,
            5: self.view_scores,
        }

        try:
            while True:
                self.display_menu()
                choice = self.prompt_int("선택: ", min_val=1, max_val=6)

                if choice == 6:
                    print("\n💾 데이터를 저장하고 프로그램을 종료합니다.")
                    self.save_state()
                    print("👋 이용해 주셔서 감사합니다. 안녕히 가세요!")
                    break

                action = menu_actions.get(choice)
                if action:
                    action()

        except (KeyboardInterrupt, EOFError):
            print("\n\n⚠️ 프로그램 강제 중단 신호(Ctrl+C/EOF)가 감지되었습니다.")
            print("💾 변경사항을 안전하게 저장한 뒤 종료합니다...")
            self.save_state()
            print("👋 프로그램이 안전하게 종료되었습니다.")


if __name__ == "__main__":
    game = QuizGame()
    game.run()
