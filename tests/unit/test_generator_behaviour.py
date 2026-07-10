from src.backend.rag import generator
from src.backend.rag.retriever import RetrievedChunk


def make_test_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="python_loops.txt_chunk_001",
        source="python_loops.txt",
        text=(
            "An accumulator starts with an initial value "
            "and updates during each loop iteration."
        ),
        distance=0.20,
        similarity_score=0.80,
    )


def test_auto_mode_detects_natural_language_hint_request():
    mode = generator.resolve_response_mode(
        query=(
            "Help me calculate a total, but do not give me "
            "the full answer immediately."
        ),
        response_mode="auto",
    )

    assert mode == "hint"


def test_detect_out_of_scope_medical_question():
    domain = generator.detect_out_of_scope_domain(
        "Can you give me medical advice about a headache?"
    )

    assert domain == "medical"

    in_scope_domain = generator.detect_out_of_scope_domain(
        "What is a variable in Python?"
    )

    assert in_scope_domain is None


def test_level_one_hint_prompt_prevents_complete_solution():
    prompt = generator.build_grounded_prompt(
        query="Give me a hint for summing a list.",
        chunks=[make_test_chunk()],
        response_mode="hint",
        hint_level=1,
    )

    assert "one high-level conceptual clue" in prompt
    assert "Do not provide complete working code" in prompt
    assert "Do not reveal the final key expression" in prompt
    assert "under 80 words" in prompt


def test_answer_prompt_requires_precise_python_terminology():
    prompt = generator.build_grounded_prompt(
        query="What does SyntaxError: expected ':' mean?",
        chunks=[make_test_chunk()],
        response_mode="answer",
    )

    assert (
        "Do not describe def, for, and while "
        "as conditional statements"
    ) in prompt

    assert (
        "preserve syntactically correct indentation"
        in prompt
    )


def test_out_of_scope_response_skips_retrieval(monkeypatch):
    def fail_if_retrieval_runs(*args, **kwargs):
        raise AssertionError(
            "Retrieval must not run for an out-of-scope request."
        )

    monkeypatch.setattr(
        generator,
        "retrieve_relevant_chunks",
        fail_if_retrieval_runs,
    )

    result = generator.generate_source_grounded_answer(
        query="Can you give me medical advice about a headache?"
    )

    assert result.answer_status == "out_of_scope"
    assert "outside the scope" in result.answer
    assert "medical advice" in result.answer
    assert result.sources == []


def test_level_one_hint_generation_skips_ollama(
    monkeypatch,
):
    def fake_retrieve_relevant_chunks(
        query,
        top_k=None,
        min_similarity_score=None,
    ):
        return [make_test_chunk()]

    def fail_if_ollama_runs(*args, **kwargs):
        raise AssertionError(
            "Ollama must not run for a level-1 hint."
        )

    monkeypatch.setattr(
        generator,
        "retrieve_relevant_chunks",
        fake_retrieve_relevant_chunks,
    )

    monkeypatch.setattr(
        generator,
        "generate_with_ollama",
        fail_if_ollama_runs,
    )

    result = generator.generate_source_grounded_answer(
        query=(
            "I need help writing a loop to calculate the sum "
            "of numbers in a list, but do not give me the "
            "full answer immediately."
        ),
        response_mode="auto",
        hint_level=1,
    )

    assert result.answer_status == "hint"
    assert len(result.sources) == 1
    assert "[S1]" in result.answer
    assert "running value" in result.answer.lower()
    assert "total = total + number" not in result.answer
    assert "complete working code" not in result.answer

