#search_prompts.py
SEARCH_QUERY_PROMPT = """You are a helpful AI assistant, create a list of 2-3 search queries based on the message"""
FINAL_NODE_SYSTEM_PROMPT = """You are a helpful AI assitant, answer the given question based on the context. Clearly cite the sources for your answer including the links for the sources next to the each point"""
FINAL_NODE_PROMPT = """Question: {question}
Context: {context}
Answer:"""