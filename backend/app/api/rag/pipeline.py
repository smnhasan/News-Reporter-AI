from .models.llm import LLM
from .prompts import get_chat_prompt, get_standalone_query_generation_prompt
from .retriever import Retriever


class Pipeline:
    def __init__(self):
        self.llm = LLM()
        self.retriever = Retriever()
        self.history = []

    def _generate_standalone_query(self, query: str) -> str:
        """Generate a standalone query if history exists, else return original query."""
        if not self.history:
            return query

        prompt = get_standalone_query_generation_prompt(query, history=self.history)
        standalone_query = self.llm.generate_response(prompt)
        print(f"Standalone Query: {standalone_query}")
        return standalone_query

    def _retrieve_context(self, standalone_query: str) -> str:
        """Retrieve context using the retriever."""
        context = self.retriever.retrieve(standalone_query)
        print(f"Retrieved context: {context}")
        return context

    def _generate_response(self, query: str, context: str) -> str:
        """Generate assistant response based on query, history, and retrieved context."""
        prompt = get_chat_prompt(query, history=self.history, context=context)
        print(f'PROMPT:>>>\n{prompt}\n')
        print('='*100)
        response = self.llm.generate_response(prompt)
        return response

    def _update_history(self, query: str, response: str) -> None:
        """Update conversation history with user query and assistant response."""
        self.history.extend([
            ("user", query),
            ("assistant", response),
        ])

    def run(self, query: str) -> str:
        """Run the full RAG pipeline for a given user query."""
        standalone_query = self._generate_standalone_query(query)
        context = self._retrieve_context(standalone_query)
        response = self._generate_response(query, context)
        self._update_history(query, response)
        return response

    def stream(self, query: str):
        """Run the full RAG pipeline and yield the response as a stream."""
        standalone_query = self._generate_standalone_query(query)
        context = self._retrieve_context(standalone_query)
        prompt = get_chat_prompt(query, history=self.history, context=context)
        
        full_response = ""
        for chunk in self.llm.stream_response(prompt):
            full_response += chunk
            yield chunk
            
        self._update_history(query, full_response)

