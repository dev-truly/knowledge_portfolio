import csv
import json
import logging
import random
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/questions",
    tags=["questions"],
)

CSV_DIR = Path("/Users/youngminhan/Desktop/dev-truly/work/chatbot-ui/src/assets/test")
RESULTS_FILE = Path("/Users/youngminhan/Desktop/dev-truly/work/python/knowledge/data/test_results.json")

class QuestionEvalRequest(BaseModel):
    question: str
    answer: str
    golden_set: str

class QuestionEvalResponse(BaseModel):
    score: int = Field(description="Score out of 100")
    is_correct: bool = Field(description="Whether the answer is considered a Pass (True) or Fail (False)")
    reason: str = Field(description="Brief reason for the score")

@router.get("/results")
async def get_test_results() -> dict:
    """
    Returns the saved test results from the JSON file.
    """
    if not RESULTS_FILE.exists():
        return {}
    try:
        with open(RESULTS_FILE, mode="r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load test results: {e}")
        return {}

@router.get("/examples")
async def get_example_questions(limit: int = 5) -> dict:
    """
    Returns a random sample of example questions from the test CSV files.
    """
    try:
        all_questions = []
        if not CSV_DIR.exists():
            logger.warning(f"CSV directory not found: {CSV_DIR}")
            return {"questions": []}

        for csv_path in CSV_DIR.glob("*.csv"):
            try:
                with open(csv_path, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        question = row.get("질문")
                        test_type = row.get("테스트 유형") or row.get("질문 유형") or "일반"
                        golden_set = row.get("기대 답변") or row.get("정답") or ""
                        remark = row.get("비고") or ""
                        if question:
                            all_questions.append({
                                "text": question.strip(),
                                "type": test_type.strip(),
                                "golden_set": golden_set.strip(),
                                "remark": remark.strip()
                            })
            except Exception as e:
                logger.error(f"Error reading CSV {csv_path}: {e}")

        if not all_questions:
            return {"questions": []}

        # Select a random sample, or return all if limit is 0
        if limit == 0:
            return {"questions": all_questions}
            
        sample_size = min(limit, len(all_questions))
        sampled_questions = random.sample(all_questions, sample_size)
        
        return {"questions": sampled_questions}
    except Exception as e:
        logger.exception("Failed to get example questions")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/evaluate", response_model=QuestionEvalResponse)
async def evaluate_answer(req: QuestionEvalRequest):
    """
    Evaluates the chatbot's answer against a golden set using LLM.
    """
    try:
        llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key.get_secret_value() if hasattr(settings.openai_api_key, 'get_secret_value') else settings.openai_api_key,
            base_url=settings.openai_api_base,
            temperature=0
        ).with_structured_output(QuestionEvalResponse)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert evaluator assessing AI chatbot responses in Korean. "
                       "Compare the 'Generated Answer' with the 'Golden Set' for the given 'Question'. "
                       "Assign a score (0-100) based on accuracy, completeness, and lack of hallucinations. "
                       "If the score is 80 or above, mark is_correct as true. "
                       "Provide a very brief reason (1-2 sentences in Korean)."),
            ("user", "Question: {question}\n\nGolden Set: {golden_set}\n\nGenerated Answer: {answer}")
        ])
        
        chain = prompt | llm
        result = await chain.ainvoke({
            "question": req.question,
            "golden_set": req.golden_set,
            "answer": req.answer
        })
        
        # Save result to JSON file
        try:
            results_data = {}
            if RESULTS_FILE.exists():
                with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                    try:
                        results_data = json.load(f)
                    except json.JSONDecodeError:
                        results_data = {}
            
            results_data[req.question] = {
                "score": result.score,
                "is_correct": result.is_correct,
                "reason": result.reason
            }
            
            RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(RESULTS_FILE, "w", encoding="utf-8") as f:
                json.dump(results_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save test result: {e}")
            
        return result
    except Exception as e:
        logger.exception("Failed to evaluate answer")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
