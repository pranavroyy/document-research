import json
from pathlib import Path

from app.models.document import Document
from app.models.chunk import Chunk
from app.db.database import SessionLocal
from app.services.hybrid_retrieval_service import hybrid_retrieve_chunks


PASS_THRESHOLD = 0.7


def load_questions():
    path = Path(__file__).parent / "questions.json"

    with open(path, "r") as file:
        return json.load(file)


def evaluate():
    db = SessionLocal()
    questions = load_questions()

    total = len(questions)
    passed = 0

    try:
        for item in questions:
            question = item["question"]
            expected_keywords = item["expected_keywords"]

            chunks = hybrid_retrieve_chunks(
                db=db,
                question=question,
                top_k=5,
                document_ids=None,
            )

            combined_text = "\n".join(chunk.content for chunk in chunks).lower()

            matched = []

            for keyword in expected_keywords:
                keyword_lower = keyword.lower()
                keyword_tokens = keyword_lower.replace("-", " ").split()

                exact_match = keyword_lower in combined_text

                token_match = (
                    len(keyword_tokens) > 1
                    and all(token in combined_text for token in keyword_tokens)
                )

                if exact_match or token_match:
                    matched.append(keyword)

            coverage = (
                len(matched) / len(expected_keywords)
                if expected_keywords
                else 0
            )

            success = coverage >= PASS_THRESHOLD

            if success:
                passed += 1

            print("=" * 80)
            print(f"Question: {question}")
            print(f"Expected: {expected_keywords}")
            print(f"Matched: {matched}")
            print(f"Coverage: {coverage:.2%}")
            print(f"Result: {'PASS' if success else 'FAIL'}")

            print("\nRetrieved chunks:")
            for i, chunk in enumerate(chunks, start=1):
                preview = chunk.content[:300].replace("\n", " ")
                print(
                    f"{i}. doc={chunk.document_id} "
                    f"page={chunk.page_number} "
                    f"chunk={chunk.chunk_index} "
                    f"preview={preview}"
                )

    finally:
        db.close()

    print("=" * 80)
    print(f"Score: {passed}/{total} passed")


if __name__ == "__main__":
    evaluate()
