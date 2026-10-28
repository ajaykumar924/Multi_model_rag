
from backend.rag_chain import ask_question

result = ask_question(
    "What information is available in my documents?"
)

print("\nANSWER:")
print(result["answer"])

print("\nSOURCES:")
for source in result["sources"]:
    print(source)
