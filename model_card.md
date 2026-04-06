# DocuBot Model Card

This model card is a short reflection on your DocuBot system. Fill it out after you have implemented retrieval and experimented with all three modes:

1. Naive LLM over full docs  
2. Retrieval only  
3. RAG (retrieval plus LLM)

Use clear, honest descriptions. It is fine if your system is imperfect.

---

## 1. System Overview


**What is DocuBot trying to do?**  
DocuBot is designed to help users find accurate answers to questions about a codebase or project documentation. It retrieves relevant information from Markdown and text files and can optionally use an LLM to generate more natural answers grounded in the docs.


**What inputs does DocuBot take?**  
DocuBot takes user questions as input, along with documentation files from a specified folder.


**What outputs does DocuBot produce?**
It produces either raw text snippets from the docs, or synthesized answers (in RAG mode), and always cites the source file and section.

---

## 2. Retrieval Design


**How does your retrieval system work?**  
Documents are split by Markdown headers, then further into smaller chunks by paragraphs or max 10 lines. An inverted index maps words to (filename, chunk_id) pairs. Relevance is scored by keyword overlap, with boosts for API path matches and synonyms. The top-k highest scoring chunks are returned.


**What tradeoffs did you make?**  
The system favors simplicity and speed over deep semantic understanding. Chunking by section/paragraph improves focus but may miss context spread across sections.

---

## 3. Use of the LLM (Gemini)


**When does DocuBot call the LLM and when does it not?**  
- Naive LLM mode: The LLM is given the full concatenated docs and answers freely.
- Retrieval only mode: No LLM is used; only raw snippets are returned.
- RAG mode: The LLM is only given the top retrieved snippets and must answer using only those.


**What instructions do you give the LLM to keep it grounded?**
The LLM is instructed to only use the provided snippets, to say “I do not know” if the answer is not present, and to cite the source file.

---

## 4. Experiments and Comparisons

Run the **same set of queries** in all three modes. Fill in the table with short notes.

You can reuse or adapt the queries from `dataset.py`.


| Query | Naive LLM: helpful or harmful? | Retrieval only: helpful or harmful? | RAG: helpful or harmful? | Notes |
|------|---------------------------------|--------------------------------------|---------------------------|-------|
| Where is the auth token generated? | Sometimes helpful, may hallucinate | Helpful | Helpful | RAG and retrieval both accurate |
| How do I connect to the database? | May hallucinate | Helpful | Helpful | Retrieval and RAG cite correct section |
| Which endpoint lists all users? | May guess, not cite | Helpful | Helpful | Retrieval and RAG cite correct endpoint |
| How does a client refresh an access token? | May be verbose or imprecise | Helpful | Helpful | Retrieval and RAG concise and accurate |


**What patterns did you notice?**  
Naive LLM can sound confident but may invent details. Retrieval only is precise but less readable. RAG combines accuracy with clarity.

---

## 5. Failure Cases and Guardrails


**Describe at least two concrete failure cases you observed.**  
Failure case 1: Asked about a feature not in docs; naive LLM hallucinated, retrieval and RAG correctly refused.

Failure case 2: Query used synonyms not present in docs; retrieval missed, RAG also failed.


**When should DocuBot say “I do not know based on the docs I have”?**  
- When no chunk contains at least 2 query tokens or a minimum score.
- When the answer is not present in any documentation file.


**What guardrails did you implement?**  
- Refusal to answer if no strong evidence is found.
- Minimum overlap/score threshold for retrieval and RAG.
- LLM instructed to say “I do not know” if unsure.

---

## 6. Limitations and Future Improvements


**Current limitations**  
1. May miss answers if phrasing differs from docs.
2. Does not handle code or tables well.
3. Retrieval is based on simple keyword overlap, not deep semantics.


**Future improvements**  
1. Use embeddings for semantic search.
2. Smarter chunking (e.g., by semantic units or code blocks).
3. Better handling of synonyms and paraphrases.

---

## 7. Responsible Use


**Where could this system cause real world harm if used carelessly?**  
If users trust answers without checking sources, they may act on incorrect or incomplete information.


**What instructions would you give real developers who want to use DocuBot safely?**  
- Always check the cited source for critical answers.
- Treat “I do not know” as a sign to review the docs manually.
- Do not use for legal, security, or safety-critical decisions.

---
