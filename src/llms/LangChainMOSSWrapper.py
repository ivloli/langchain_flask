from typing import Any, List, Mapping, Optional
from utils import JsonObj

from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class LangChainMOSSWrapper(LLM):
    path: str | None
    args: JsonObj | None
    meta_instruction: str | None
    tokenizer: Any
    model: Any

    def __init__(self, path: str, args: JsonObj=None):
        super().__init__()
        args = args or {}
        self.path = path
        self.args = dict(
            max_length=2048, 
            do_sample=True, 
            top_k=40, 
            top_p=0.8, 
            temperature=0.7,
            repetition_penalty=1.02,
            num_return_sequences=1, 
            eos_token_id=106068,
        )
        self.args.update(args)
        self.tokenizer = AutoTokenizer.from_pretrained(self.path, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(self.path, trust_remote_code=True).half().cuda()
        self.meta_instruction = "You are an AI assistant whose name is MOSS."

    @property
    def _llm_type(self) -> str:
        return "moss"

    def _call(
        self,
        query: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
    ) -> str:
        prompt = self.meta_instruction + '<|Human|>: ' + query + '<eoh>'
        inputs = self.tokenizer(prompt, return_tensors="pt")
        with torch.no_grad():
            outputs = self.model.generate(
                inputs.input_ids.cuda(), 
                attention_mask=inputs.attention_mask.cuda(), 
                max_length=self.args['max_length'], 
                do_sample=self.args['do_sample'], 
                top_k=self.args['top_k'], 
                top_p=self.args['top_p'], 
                temperature=self.args['temperature'],
                repetition_penalty=self.args['repetition_penalty'],
                num_return_sequences=self.args['num_return_sequences'], 
                eos_token_id=self.args['eos_token_id'],
                pad_token_id=self.tokenizer.pad_token_id)
            response = self.tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
            # prompt += response
            return response.lstrip('\n')
    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {
            "path": self.path, 
            "args": self.args, 
            "meta_instruction": self.meta_instruction,
        }