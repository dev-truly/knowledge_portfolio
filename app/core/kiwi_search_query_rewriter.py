class KiwiSearchQueryRewriter:
    def __init__(self, *args, **kwargs):
        pass
        
    def rewrite(self, question: str) -> str:
        """ [Redacted] NLP NLP Rules & Regex """
        return question

    def extract_with_tags(self, question: str) -> list[tuple[str, str]]:
        return []

    def add_user_word(self, word: str, *, tag: str = "NNP", score: float = 0.0) -> None:
        pass\n