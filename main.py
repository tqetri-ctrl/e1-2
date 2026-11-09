"""퀴즈 게임 도메인 모델 및 실행 엔트리포인트."""

from __future__ import annotations
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


if __name__ == "__main__":
    # Quiz 클래스 단위 동작 검증
    sample_quiz = Quiz(
        question="파이썬에서 불변(immutable) 시퀀스 자료형은?",
        choices=["list", "tuple", "set", "dict"],
        answer=2,
        hint="소괄호 '()'로 정의하며 요소를 수정할 수 없습니다.",
    )
    sample_quiz.display(index=1)
    print(sample_quiz.get_hint())
    assert sample_quiz.is_correct(2) is True
    assert sample_quiz.is_correct(1) is False
    quiz_dict = sample_quiz.to_dict()
    restored_quiz = Quiz.from_dict(quiz_dict)
    assert restored_quiz.question == sample_quiz.question
    assert restored_quiz.choices == sample_quiz.choices
    assert restored_quiz.answer == sample_quiz.answer
    assert restored_quiz.hint == sample_quiz.hint
    print("✅ Quiz 클래스 단위 테스트 통과!")
