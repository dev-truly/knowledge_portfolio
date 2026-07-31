from langchain_openai import ChatOpenAI
from app.core.config import settings

class LLMFactory:
    """공통 ChatOpenAI 초기화를 위한 Factory 클래스"""
    @staticmethod
    def get_default_llm(temperature: float = None, streaming: bool = True, verbose: bool = True) -> ChatOpenAI:
        kwargs = {
            "model": settings.openai_model,
            "api_key": settings.openai_api_key,
            "base_url": settings.openai_api_base,
            "streaming": streaming,
            "verbose": verbose
        }
        if temperature is not None:
            kwargs["temperature"] = temperature
            
        return ChatOpenAI(**kwargs)
        
    @staticmethod
    def get_structured_llm(model_class, method="function_calling", temperature: float = 0, streaming: bool = False, verbose: bool = False):
        llm = LLMFactory.get_default_llm(temperature=temperature, streaming=streaming, verbose=verbose)
        if method:
            return llm.with_structured_output(model_class, method=method)
        return llm.with_structured_output(model_class)
