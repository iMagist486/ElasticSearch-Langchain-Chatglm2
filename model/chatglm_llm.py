from typing import Optional, List
import torch
from transformers import AutoModel, AutoTokenizer, AutoModelForCausalLM
from langchain.llms.base import LLM
from model.base import AnswerResult
from configs.params import ModelParams

model_config = ModelParams()


class ChatLLM(LLM):
    max_token: int = 8192
    temperature: float = 0.95
    top_p = 0.8
    history_len = 10
    history = []
    model_type: str = "ChatGLM"
    model_path: str = model_config.llm_model
    tokenizer: object = None
    model: object = None

    def __init__(self):
        super().__init__()

    @property
    def _llm_type(self) -> str:
        return "ChatLLM"

    def load_llm(self):
        if 'internlm' in self.model_path.lower():
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path, device_map="auto", trust_remote_code=True,
                                                           torch_dtype=torch.float16)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_path, device_map="auto",
                                                              trust_remote_code=True,
                                                              torch_dtype=torch.float16)
            self.model = self.model.eval()
            self.model_type = "InternLM"
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path, trust_remote_code=True)
            self.model = AutoModel.from_pretrained(self.model_path, trust_remote_code=True).cuda()
            self.model = self.model.eval()

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
            if self.model_type == "InternLM":
                response = self.model.stream_chat(
                    self.tokenizer,
                    prompt,
                    history=history[-self.history_len:-1] if self.history_len > 1 else [],
                    max_new_tokens=self.max_token,
                    temperature=self.temperature,
                    top_p=self.top_p
                )
            else:
                response = self.model.stream_chat(
                    self.tokenizer,
                    prompt,
                    history=history[-self.history_len:-1] if self.history_len > 1 else [],
                    max_length=self.max_token,
                    temperature=self.temperature,
                    top_p=self.top_p
                )
            for inum, (stream_resp, _) in enumerate(response):
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
