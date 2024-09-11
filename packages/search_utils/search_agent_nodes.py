#search_agent_nodes.py
from langgraph.prebuilt import ToolInvocation
import asyncio
import os
import json
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    ChatMessage,
    FunctionMessage,
    HumanMessage,
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_structured_output_runnable
from langchain.agents.agent_types import AgentType
from typing import TypedDict, Annotated, Sequence, List
from langchain_core.pydantic_v1 import BaseModel, Field
import operator
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langgraph.constants import Send
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import Html2TextTransformer
from .search_prompts import SEARCH_QUERY_PROMPT, FINAL_NODE_SYSTEM_PROMPT, FINAL_NODE_PROMPT
from .duckduckgo_utils import search

#model = ChatMistralAI(api_key=os.environ.get('MISTRAL_API_KEY'),model="mistral-large-latest",temperature=0)
model = ChatMistralAI(api_key=os.environ.get('MISTRAL_API_KEY'),model="open-mistral-nemo-2407",temperature=0)
#model = ChatAnthropic(temperature=0, model_name="claude-3-haiku-20240307", max_tokens=4096)
final_model = ChatAnthropic(temperature=0, model_name="claude-3-5-sonnet-20240620", max_tokens=4096)
#model = ChatOpenAI(model="gpt-4o-mini",temperature=0, streaming=True)

class Queries(BaseModel):
    """List of search queries"""
    queries: List[str] = Field(
        description="List of the generated search queries"
    )

class SummaryState(TypedDict):
    content: str
    query: str

class OverallState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    search_queries: list[str]
    search_results: list[str]
    page_content: list[str]
    page_summaries: Annotated[list, operator.add]

    @classmethod
    def search_query_node(cls,state):
      messages = state['messages']
      last_message = messages[-1]

      prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    SEARCH_QUERY_PROMPT,
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
      chain = prompt | model.with_structured_output(Queries)
      result = chain.invoke(messages)
      queries = result.queries
      return {"search_queries":queries}

    @classmethod
    def search_results_node(cls,state):
      queries = state['search_queries']
      results = asyncio.run(search(queries))
      return {"search_results":results}

    @classmethod
    def web_scape_node(cls,state):
      search_results = state['search_results']
      #urls = [result['href'] for result in results[0]]
      urls = [result['href'] for search_result in search_results for result in search_result]
      print(urls)
      loader = AsyncHtmlLoader(urls)
      docs = loader.load()
      html2text = Html2TextTransformer()
      docs_transformed = html2text.transform_documents(docs)
      return {"page_content":docs_transformed}

    @classmethod
    def generate_summary(cls,state: SummaryState):
      content = state['content'].page_content
      source = state['content'].metadata['source']
      query = state['query']
      prompt = f"Summarize the following content to answer the question: {query}, mention the source: {source}   \n\n <content> {content} </content>"
      page_summary = model.invoke(prompt)
      return {"page_summaries":[page_summary.content]}

    @classmethod
    def continue_to_summarise_node(cls,state):
      return [Send("Generate Summary", {"content": p, "query": state['messages'][0].content}) for p in state['page_content']]

    @classmethod
    def final_result_node(cls,state):
      messages = state['messages']
      question = messages[-1]
      context = state['page_summaries']
      prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    FINAL_NODE_SYSTEM_PROMPT,
                ),
                (
                    "human",
                    FINAL_NODE_PROMPT,
                ),
            ]
        )
      input = {"question":messages[-1],"context":context}
      formatted_prompt = prompt.format_messages(**input)
      response = final_model.invoke(formatted_prompt)
      #result = AIMessage(content = response.content)
      #return {"messages":[response.content]}
      return {"messages":[response]}