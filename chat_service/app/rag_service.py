# import os
# import logging
# from functools import lru_cache

# from langchain_ollama import OllamaLLM
# from langchain_core.prompts import PromptTemplate
# from langchain_core.output_parsers import StrOutputParser

# from .vector_store import search_knowledge

# logger = logging.getLogger(__name__)

# OLLAMA_URL  = os.getenv("OLLAMA_URL",  "http://ollama:11434")
# OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# # ---------------------------------------------------------------------------
# # Prompt
# # ---------------------------------------------------------------------------
# PROMPT_TEMPLATE = PromptTemplate(
#     input_variables=["context", "question"],
#     template="""You are a friendly and knowledgeable support assistant for Vestique,
# a fashion platform that connects customers, designers, boutique owners and tailors.

# Use ONLY the information in the context below to answer the question.
# If the context does not contain enough information to answer, say:
# "I'm sorry, I don't have that information right now. Please contact support@vestique.com."

# Do NOT make up information. Keep your answer concise and helpful.

# Context:
# {context}

# Customer question: {question}

# Answer:""",
# )

# # ---------------------------------------------------------------------------
# # Lazy-initialise the LLM chain so import errors don't crash the service
# # ---------------------------------------------------------------------------
# @lru_cache(maxsize=1)
# def _get_chain():
#     llm = OllamaLLM(
#         model=OLLAMA_MODEL,
#         base_url=OLLAMA_URL,
#         temperature=0.2,        # low temperature → more factual answers
#         num_predict=512,        # max tokens in reply
#     )
#     return PROMPT_TEMPLATE | llm | StrOutputParser()


# # ---------------------------------------------------------------------------
# # Public API
# # ---------------------------------------------------------------------------

# def get_rag_response(question: str, n_results: int = 3) -> str:
#     """
#     Full RAG pipeline:
#       1. Embed the question and retrieve the top-n relevant docs from ChromaDB.
#       2. Build a prompt with those docs as context.
#       3. Send to Ollama LLaMA3 and return the generated answer.
#     """
#     try:
#         docs = search_knowledge(question, n_results=n_results)

#         if docs:
#             context = "\n\n".join(f"- {doc}" for doc in docs)
#             logger.info(f"RAG: retrieved {len(docs)} docs for '{question}'")
#         else:
#             context = "No relevant information found."
#             logger.warning(f"RAG: no docs matched '{question}'")

#         chain = _get_chain()
#         answer = chain.invoke({"context": context, "question": question})
#         return answer.strip()

#     except Exception as e:
#         logger.error(f"RAG error: {e}", exc_info=True)
#         return (
#             "I'm having trouble processing your request right now. "
#             "Please try again or contact support@vestique.com."
#         )


import os
import logging
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .vector_store import search_knowledge

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are a friendly support assistant for Vestique,
a fashion platform connecting customers, designers, boutique owners and tailors.

Use ONLY the context below to answer. If not enough info, say:
"I'm sorry, I don't have that information. Please contact support@vestique.com."

Context:
{context}

Customer question: {question}

Answer:""",
)

def _get_chain():
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=GROQ_API_KEY,
        temperature=0.2,
        max_tokens=512,
    )
    return PROMPT_TEMPLATE | llm | StrOutputParser()

def get_rag_response(question: str, n_results: int = 3) -> str:
    try:
        docs = search_knowledge(question, n_results=n_results)
        context = "\n\n".join(f"- {doc}" for doc in docs) if docs else "No relevant information found."
        chain = _get_chain()
        answer = chain.invoke({"context": context, "question": question})
        return answer.strip()
    except Exception as e:
        logger.error(f"RAG error: {e}", exc_info=True)
        return "I'm having trouble right now. Please try again or contact support@vestique.com."