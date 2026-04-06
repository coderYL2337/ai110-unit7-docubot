"""
Core DocuBot class responsible for:
- Loading documents from the docs/ folder
- Building a simple retrieval index (Phase 1)
- Retrieving relevant snippets (Phase 1)
- Supporting retrieval only answers
- Supporting RAG answers when paired with Gemini (Phase 2)
"""

import os
import glob

class DocuBot:
    def __init__(self, docs_folder="docs", llm_client=None):
        """
        docs_folder: directory containing project documentation files
        llm_client: optional Gemini client for LLM based answers
        """
        self.docs_folder = docs_folder
        self.llm_client = llm_client

        # Load documents into memory as (filename, paragraph_text, paragraph_id)
        self.documents = self.load_documents()  # List of (filename, paragraph_text, paragraph_id)

        # Build a retrieval index (implemented in Phase 1)
        self.index = self.build_index(self.documents)

    # -----------------------------------------------------------
    # Document Loading
    # -----------------------------------------------------------

    def load_documents(self):
        """
        Loads all .md and .txt files inside docs_folder.
        Splits each file into sections by Markdown headers (lines starting with # or ##),
        then further splits each section into smaller chunks by paragraphs (double newlines)
        or by max 10 lines per chunk.
        Returns a list of (filename, chunk_text, chunk_id).
        """
        import re
        docs = []
        pattern = os.path.join(self.docs_folder, "*.*")
        for path in glob.glob(pattern):
            if path.endswith(".md") or path.endswith(".txt"):
                with open(path, "r", encoding="utf8") as f:
                    text = f.read()
                filename = os.path.basename(path)
                # Split by Markdown headers
                header_matches = list(re.finditer(r"^#{1,6} .+", text, re.MULTILINE))
                sections = []
                if header_matches:
                    for i, match in enumerate(header_matches):
                        start = match.start()
                        end = header_matches[i+1].start() if i+1 < len(header_matches) else len(text)
                        section = text[start:end].strip()
                        if section:
                            sections.append(section)
                else:
                    sections = [text.strip()]
                chunk_id = 0
                for section in sections:
                    # Further split section into paragraphs (double newlines)
                    paragraphs = [p.strip() for p in section.split("\n\n") if p.strip()]
                    for para in paragraphs:
                        # If paragraph is too long, split by max 10 lines
                        lines = para.splitlines()
                        for i in range(0, len(lines), 10):
                            chunk = "\n".join(lines[i:i+10]).strip()
                            if chunk:
                                docs.append((filename, chunk, chunk_id))
                                chunk_id += 1
        return docs

    # -----------------------------------------------------------
    # Index Construction (Phase 1)
    # -----------------------------------------------------------

    def build_index(self, documents):
        """
        Build a tiny inverted index mapping lowercase words to the (filename, paragraph_id) pairs they appear in.
        """
        import string
        index = {}
        for filename, text, para_id in documents:
            tokens = text.lower().translate(str.maketrans('', '', string.punctuation)).split()
            unique_tokens = set(tokens)
            for token in unique_tokens:
                if token not in index:
                    index[token] = []
                entry = (filename, para_id)
                if entry not in index[token]:
                    index[token].append(entry)
        return index

    # -----------------------------------------------------------
    # Scoring and Retrieval (Phase 1)
    # -----------------------------------------------------------

    def score_document(self, query, text):
        """
        Improved relevance scoring for API docs:
        - Counts overlapping words (as before)
        - Boosts score if query contains 'endpoint' and text contains an API path (e.g., /api/)
        - Handles simple synonyms (e.g., 'endpoint' ~ 'get', 'post', 'put', 'delete')
        """
        import string
        import re
        query_lc = query.lower()
        text_lc = text.lower()
        query_tokens = query_lc.translate(str.maketrans('', '', string.punctuation)).split()
        text_tokens = set(text_lc.translate(str.maketrans('', '', string.punctuation)).split())
        score = sum(1 for token in query_tokens if token in text_tokens)

        # Boost if query asks about endpoint and text contains an API path
        if 'endpoint' in query_tokens or 'route' in query_tokens:
            # Look for lines like 'get /api/...' or 'post /api/...'
            if re.search(r'\b(get|post|put|delete|patch)\s+/api/\S*', text_lc):
                score += 3
            # Or just any /api/ path
            elif '/api/' in text_lc:
                score += 2

        # Boost if query contains 'users' and text contains '/api/users'
        if 'users' in query_tokens and '/api/users' in text_lc:
            score += 2

        # Partial match: singular/plural
        if 'user' in query_tokens and 'users' in text_tokens:
            score += 1
        if 'users' in query_tokens and 'user' in text_tokens:
            score += 1

        return score

    def retrieve(self, query, top_k=8):
        """
        Use the index and scoring function to select top_k relevant document sections.
        Fallback to file-level retrieval if no relevant sections are found.
        Return a list of (filename, section_text, section_id) sorted by score descending.
        """
        scored = []
        for filename, section, section_id in self.documents:
            score = self.score_document(query, section)
            if score > 0:
                scored.append((filename, section, section_id, score))
        # Sort by score descending, then filename and section_id for tie-breaker
        scored.sort(key=lambda x: (-x[3], x[0], x[2]))
        results = [(filename, section, section_id) for filename, section, section_id, _ in scored][:top_k]
        # Fallback: if no relevant sections, return whole file(s) that contain any query token
        if not results:
            import string
            query_tokens = set(query.lower().translate(str.maketrans('', '', string.punctuation)).split())
            file_texts = {}
            for filename, section, _ in self.documents:
                if filename not in file_texts:
                    file_texts[filename] = []
                file_texts[filename].append(section)
            for filename, sections in file_texts.items():
                full_text = "\n\n".join(sections)
                text_tokens = set(full_text.lower().translate(str.maketrans('', '', string.punctuation)).split())
                if any(token in text_tokens for token in query_tokens):
                    results.append((filename, full_text, 0))
        return results[:top_k]

    # -----------------------------------------------------------
    # Answering Modes
    # -----------------------------------------------------------

    def answer_retrieval_only(self, query, top_k=8):
        """
        Retrieval only mode.
        Returns relevant sections and filenames (with section number) with no LLM involved.
        Refuses to answer if no chunk contains at least 2 query tokens or a minimum score threshold.
        """
        snippets = self.retrieve(query, top_k=top_k)

        # Guardrail: require at least one chunk with 2+ query tokens matched or score >= 2
        import string
        query_tokens = set(query.lower().translate(str.maketrans('', '', string.punctuation)).split())
        found_evidence = False
        for filename, section, section_id in snippets:
            section_tokens = set(section.lower().translate(str.maketrans('', '', string.punctuation)).split())
            overlap = len(query_tokens & section_tokens)
            score = self.score_document(query, section)
            if overlap >= 2 or score >= 2:
                found_evidence = True
                break
        if not found_evidence:
            return "I do not know based on these docs."

        formatted = []
        for filename, section, section_id in snippets:
            formatted.append(f"[{filename} - section {section_id+1}]\n{section}\n")

        return "\n---\n".join(formatted)

    def answer_rag(self, query, top_k=8):
        """
        RAG mode.
        Uses student retrieval to select snippets, then asks Gemini
        to generate an answer using only those snippets.
        Refuses to answer if no chunk contains at least 2 query tokens or a minimum score threshold.
        """
        if self.llm_client is None:
            raise RuntimeError(
                "RAG mode requires an LLM client. Provide a GeminiClient instance."
            )

        snippets = self.retrieve(query, top_k=top_k)

        # Guardrail: require at least one chunk with 2+ query tokens matched or score >= 2
        import string
        query_tokens = set(query.lower().translate(str.maketrans('', '', string.punctuation)).split())
        found_evidence = False
        for filename, section, section_id in snippets:
            section_tokens = set(section.lower().translate(str.maketrans('', '', string.punctuation)).split())
            overlap = len(query_tokens & section_tokens)
            score = self.score_document(query, section)
            if overlap >= 2 or score >= 2:
                found_evidence = True
                break
        if not found_evidence:
            return "I do not know based on these docs."

        # Pass only the section text and filename to the LLM client
        return self.llm_client.answer_from_snippets(query, [(filename, section) for filename, section, _ in snippets])

    # -----------------------------------------------------------
    # Bonus Helper: concatenated docs for naive generation mode
    # -----------------------------------------------------------

    def full_corpus_text(self):
        """
        Returns all paragraphs concatenated into a single string.
        This is used in Phase 0 for naive 'generation only' baselines.
        """
        return "\n\n".join(para for _, para, _ in self.documents)
