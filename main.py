"""퀴즈 게임 도메인 모델, 영속성 관리 및 실행 엔트리포인트."""

from __future__ import annotations

import json
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
    """퀴즈 게임의 상태 관리, 영속성 및 전반적인 게임 로직을 담당하는 클래스."""

    def __init__(self, state_file: str | Path = "state.json") -> None:
        self.state_file = Path(state_file)
        self.quizzes: list[Quiz] = []
        self.best_score: int = 0
        self.history: list[dict[str, Any]] = []

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
                # 퀴즈 목록이 비어있는 경우 기본 퀴즈 사용
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
        """현재 퀴즈 목록, 최고 점수 및 히스토리를 state.json에 UTF-8로 저장합니다."""
        data = {
            "best_score": self.best_score,
            "quizzes": [q.to_dict() for q in self.quizzes],
            "history": self.history,
        }
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except OSError as e:
            print(f"⚠️ 데이터 파일 저장 중 오류가 발생했습니다: {e}")
            return False

    def reset_to_default_state(self) -> None:
        """상태를 기본 퀴즈 5문항 및 점수 0으로 초기화합니다."""
        self.quizzes = get_default_quizzes()
        self.best_score = 0
        self.history = []


if __name__ == "__main__":
    import tempfile

    print("=== QuizGame 영속성 및 복구 단위 테스트 ===")

    # 임시 파일을 통한 영속성 및 손상 복구 테스트
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_file = Path(tmp_dir) / "test_state.json"

        # 1. 파일 부재 시 기본값 로드 및 생성 테스트
        game = QuizGame(state_file=test_file)
        game.load_state()
        assert len(game.quizzes) == 5, "기본 퀴즈는 5개여야 합니다."
        assert test_file.exists(), "load_state 후 파일이 자동 생성되어야 합니다."

        # 2. 저장 및 재로드 테스트
        game.best_score = 100
        game.history.append({"test": "ok"})
        game.save_state()

        game_reloaded = QuizGame(state_file=test_file)
        game_reloaded.load_state()
        assert game_reloaded.best_score == 100
        assert len(game_reloaded.history) == 1
        assert len(game_reloaded.quizzes) == 5

        # 3. 손상된 JSON 복구 테스트
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("INVALID JSON CONTENT {{{")

        game_corrupted = QuizGame(state_file=test_file)
        game_corrupted.load_state()
        assert len(game_corrupted.quizzes) == 5, "손상 시 기본 5개 퀴즈로 복구되어야 합니다."
        assert game_corrupted.best_score == 0

    print("✅ 기본 퀴즈 데이터 및 state.json 입출력/예외 복구 테스트 통과!")
