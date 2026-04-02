import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from rag_core import get_retriever, get_llm, PROMPT_TEMPLATE

load_dotenv()


def format_history(history: list[dict]) -> str:
    """Convert list of {role, content} dicts to a readable string."""
    if not history:
        return "None"
    lines = []
    for msg in history[-6:]:       # keep last 3 turns
        label = "User" if msg["role"] == "user" else "Assistant"
        lines.append(f"{label}: {msg['content']}")
    return "\n".join(lines)


def ask(question: str, history: list[dict], retriever, llm) -> tuple[str, list[int]]:
    docs = retriever.invoke(question)
    context = "\n\n".join(doc.page_content for doc in docs)

    prompt = PromptTemplate(
        template=PROMPT_TEMPLATE,
        input_variables=["context", "history", "question"],
    )
    final_prompt = prompt.format(
        context=context,
        history=format_history(history),
        question=question,
    )
    response = llm.invoke(final_prompt)
    pages = sorted({doc.metadata.get("page", 0) + 1 for doc in docs})
    return response.content, pages


def main() -> None:
    print("🤖 UPSC RAG Assistant — type 'quit' to exit, 'clear' to reset history.\n")
    retriever = get_retriever(search_type="mmr")
    llm = get_llm()
    history: list[dict] = []

    while True:
        question = input("Your question: ").strip()

        if question.lower() in ("quit", "exit", "q"):
            break
        if question.lower() == "clear":
            history.clear()
            print("🗑️  Conversation history cleared.\n")
            continue
        if not question:
            continue

        answer, pages = ask(question, history, retriever, llm)

        # Update conversation history
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": answer})

        print(f"\n📌 Answer:\n{answer}")
        print(f"\n📄 Sources: Page(s) {pages}\n")
        print("─" * 50)


if __name__ == "__main__":
    main()
