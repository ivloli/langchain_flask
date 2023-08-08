from langchain.llms import OpenAI
from langchain import LLMChain, PromptTemplate, FewShotPromptTemplate

def generate_response(input_text,key):
    llm = OpenAI(temperature=0.1, openai_api_key=key)
    return llm(input_text)

def generate_prompt_template(template):
    return PromptTemplate.from_template(template)

def generate_few_prompt_template(examples, template, suffix, prefix="", seperator="\n"):
    example_prompt = PromptTemplate.from_template(template)
    suffix_prompt = PromptTemplate.from_template(suffix)
    input_variables = suffix_prompt.input_variables

    few_shot_prompt = FewShotPromptTemplate(
        examples=examples,
        example_prompt=example_prompt,
        prefix=str(prefix),
        suffix=str(suffix),
        input_variables=input_variables,
        example_separator=str(seperator),
    )
    return few_shot_prompt

def generate_none_prompt_template():
    return PromptTemplate.from_template("{question}")

def generate_chain(inputllm, template):
    return LLMChain(
            llm=inputllm,
            prompt=template,
            )
