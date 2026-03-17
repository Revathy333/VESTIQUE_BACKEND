import os
import logging
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .vector_store import search_knowledge
from .vector_store import search_collection


logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are a friendly support assistant for Vestique,
a fashion platform connecting customers, designers, boutique owners and tailors.

Use ONLY the context below to answer. Be specific — mention actual names,
ratings and reviews from the context when available.

If the context does not contain enough information to answer, say:
"I'm sorry, I don't have that information. Please contact support@vestique.com."

Do NOT make up any names, ratings or information.

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


# def get_rag_response(question: str, n_results: int = 5) -> str:
#     """
#     Pure semantic RAG pipeline:
#     1. Embed the question
#     2. ChromaDB finds top-n semantically similar docs
#        (includes FAQs + designers + reviews + posts — all indexed)
#     3. Send to Groq as context
#     """
#     try:
#         docs = search_knowledge(question, n_results=n_results)

#         if docs:
#             context = "\n\n".join(f"- {doc}" for doc in docs)
#             logger.info(f"RAG: {len(docs)} docs matched for '{question}'")
#         else:
#             context = "No relevant information found."
#             logger.warning(f"RAG: no docs matched '{question}'")

#         chain = _get_chain()
#         answer = chain.invoke({"context": context, "question": question})
#         return answer.strip()

#     except Exception as e:
#         logger.error(f"RAG error: {e}", exc_info=True)
#         return "I'm having trouble right now. Please try again or contact support@vestique.com."




def get_rag_response(question: str) -> str:
    try:
        context_parts = []

        categories = [
            ("creators",        "=== Designers & Tailors ===",       3),
            ("profile_reviews", "=== Customer Profile Reviews ===",  3),
            ("general_reviews", "=== Platform Reviews ===",          2),
            ("posts",           "=== Designer Posts & Work ===",     2),
            ("faq",             "=== Platform Info ===",             2),
        ]

        for collection, heading, n in categories:
            docs = search_collection(collection, question, n_results=n)
            if docs:
                context_parts.append(heading + "\n" + "\n".join(f"- {d}" for d in docs))

        context = "\n\n".join(context_parts) if context_parts else "No relevant information found."

        chain = _get_chain()
        answer = chain.invoke({"context": context, "question": question})
        return answer.strip()

    except Exception as e:
        logger.error(f"RAG error: {e}", exc_info=True)
        return "I'm having trouble right now. Please try again or contact support@vestique.com."