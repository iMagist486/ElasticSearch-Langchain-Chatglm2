from abc import ABC
from langchain.llms.base import LLM
from typing import Optional, List
from model.base import (BaseAnswer,
                        AnswerResult)
from transformers import AutoModel, AutoTokenizer


class ChatGLM(BaseAnswer, LLM, ABC):
    max_token: int = 8192
    temperature: float = 0.95
    top_p = 0.8
    history = []
    tokenizer: object = None
    model: object = None
    history_len = 10

    def __init__(self, model_path):
        super().__init__()
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        self.model = AutoModel.from_pretrained(model_path, trust_remote_code=True).cuda()
        self.model = self.model.eval()

    @property
    def _llm_type(self) -> str:
        return "ChatGLM"

    @property
    def _history_len(self) -> int:
        return self.history_len

    def set_history_len(self, history_len: int = 10) -> None:
        self.history_len = history_len

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        print(f"__call:{prompt}")
        response, _ = self.model.chat(
            self.tokenizer,
            prompt,
            history=[],
            max_length=self.max_token,
            temperature=self.temperature,
            top_p=self.top_p
        )
        print(f"response:{response}")
        print(f"+++++++++++++++++++++++++++++++++++")
        return response

    def generatorAnswer(self, prompt: str,
                        history: List[List[str]] = [],
                        streaming: bool = False):

        if streaming:
            history += [[]]
            for inum, (stream_resp, _) in enumerate(self.model.stream_chat(
                    self.tokenizer,
                    prompt,
                    history=history[-self.history_len:-1] if self.history_len > 1 else [],
                    max_length=self.max_token,
                    temperature=self.temperature,
                    top_p=self.top_p
            )):
                # self.checkPoint.clear_torch_cache()
                history[-1] = [prompt, stream_resp]
                answer_result = AnswerResult()
                answer_result.history = history
                answer_result.llm_output = {"answer": stream_resp}
                yield answer_result
        else:
            response, _ = self.model.chat(
                self.tokenizer,
                prompt,
                history=history[-self.history_len:] if self.history_len > 0 else [],
                max_length=self.max_token,
                temperature=self.temperature,
                top_p=self.top_p
            )
            self.clear_torch_cache()
            history += [[prompt, response]]
            answer_result = AnswerResult()
            answer_result.history = history
            answer_result.llm_output = {"answer": response}
            yield answer_result
