from fastapi import HTTPException
from typing import List, Dict
import logging

from langchain.schema import BaseMessage
import re, json

from langchain_ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain.chains.llm import LLMChain
from langchain.chains.conversation.base import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.output_parsers import PydanticOutputParser

from ..config.config import Config
from ..model.eval_metrics import EvalMetrics
from ..constant.prompt_constants import DEFAULT_AGENT_INSTRUCTIONS, DEFAULT_INITIAL_GREETING

logger = logging.getLogger("testing-service")
logging.basicConfig(level=logging.INFO)

class TestingService:
    def __init__(self):
        self.config = Config()

        self.llm = ChatOllama(
            model=self.config.MODEL_NAME,  
            base_url="http://localhost:11434/",
            temperature=0.4,
        )

        self.parser = PydanticOutputParser(pydantic_object=EvalMetrics)
        self.eval_prompt = PromptTemplate(
            template="""
        You are an evaluator. Analyze the following transcript and return structured evaluation.

        Give the response in a proper json format only without any additional text.
        Ignore the properties, required and description fields in the schema and give the rest as json.

        Transcript:
        {transcript}

        {format_instructions}
        """,
            input_variables=["transcript"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
        )
        self.eval_chain = self.eval_prompt | self.llm


        self.rewrite_prompt = PromptTemplate.from_template("""
        Rewrite the following base agent prompt:

        {base_prompt}

        Incorporating these improvements:
        {edits}

        Return a single coherent, concise, professional, empathetic, and legally compliant prompt.
        """)
        self.rewrite_chain = self.rewrite_prompt | self.llm

    def build_agent_chain(self, base_prompt: str):
        agent_prompt = ChatPromptTemplate.from_messages([
            ("system", base_prompt),
            ("human", "{history}\n\nHuman: {input}\nAssistant:")
        ])
        memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="history"
        )
        return ConversationChain(
            llm=self.llm,
            prompt=agent_prompt,
            memory=memory,
            input_key="input" 
        )

    def build_persona_chain(self, persona_prompt: str):
        persona_template = ChatPromptTemplate.from_messages([
            ("system", persona_prompt),
            ("human", "{history}\n\nHuman: {input}\nAssistant:")
        ])
        memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="history"
        )
        return ConversationChain(
            llm=self.llm,
            prompt=persona_template,
            memory=memory,
            input_key="input" 
        )

    async def run_simulation(self, base_agent_prompt: str, persona_prompt: str, max_turns: int):
        transcript: List[Dict[str, str]] = []

        agent_chain = self.build_agent_chain(base_agent_prompt or DEFAULT_AGENT_INSTRUCTIONS)
        persona_chain = self.build_persona_chain(persona_prompt)

        # Agent opens the conversation
        agent_msg = await agent_chain.apredict(input=DEFAULT_INITIAL_GREETING)
        transcript.append({"role": "agent", "text": agent_msg})

        for _ in range(max_turns):
            persona_msg = await persona_chain.apredict(input=agent_msg)
            transcript.append({"role": "persona", "text": persona_msg})

            if any(kw in persona_msg.lower() for kw in ["i'll pay", "i will pay", "i agree", "schedule payment", "pay today", "make a payment", "pay now", "i can pay"]):
                break

            agent_msg = await agent_chain.apredict(input=persona_msg)
            transcript.append({"role": "agent", "text": agent_msg})

        return transcript

    async def evaluate_conversation(self, transcript: List[Dict[str, str]]):
        convo_text = "\n".join([f"{m['role'].upper()}: {m['text']}" for m in transcript])
        raw = await self.eval_chain.ainvoke(input={"transcript": convo_text})
        try:
            metrics = self.extract_recommendations(raw)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Eval parse failed: {e}. Raw: {raw}")
        return metrics

    async def rewrite_prompt_text(self, base_prompt: str, edits: List[str]):
        if not edits:
            return base_prompt
        edits_text = "\n".join([f"- {e}" for e in edits])
        return await self.rewrite_chain.ainvoke(input={"base_prompt": base_prompt, "edits": edits_text})
    
    def extract_recommendations(self, raw: BaseMessage) -> dict:
        import json
        text = raw.content
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            print("Invalid JSON:", text)
            data = {}
        return data