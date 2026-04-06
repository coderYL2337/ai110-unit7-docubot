## Project Summary

This project centers on building a retrieval-augmented DocuBot that answers questions using project documentation. The core concept students needed to understand is how to design and implement a retrieval system that indexes, scores, and returns relevant document snippets, and how to integrate this with an LLM for grounded answers. Students are most likely to struggle with chunking documents effectively, tuning relevance scoring, and ensuring the system refuses to answer when evidence is lacking. AI was helpful for generating code templates, suggesting improvements, and explaining retrieval strategies, but could be misleading when it hallucinated answers or failed to respect evidence constraints. One way I would guide a student is by prompting them to test their system with edge cases and to reflect on why certain queries fail, rather than giving away the solution. This encourages deeper understanding of retrieval design and responsible use of LLMs. Overall, the project highlights the importance of evidence-based answers and the limitations of both retrieval and generative AI.

# DocuBot

DocuBot is a small documentation assistant that helps answer developer questions about a codebase.  
It can operate in three different modes:

1. **Naive LLM mode**  
   Sends the entire documentation corpus to a Gemini model and asks it to answer the question.

2. **Retrieval only mode**  
   Uses a simple indexing and scoring system to retrieve relevant snippets without calling an LLM.

3. **RAG mode (Retrieval Augmented Generation)**  
   Retrieves relevant snippets, then asks Gemini to answer using only those snippets.

The docs folder contains realistic developer documents (API reference, authentication notes, database notes), but these files are **just text**. They support retrieval experiments and do not require students to set up any backend systems.

---

## Setup

### 1. Install Python dependencies

    pip install -r requirements.txt

### 2. Configure environment variables

Copy the example file:

    cp .env.example .env

Then edit `.env` to include your Gemini API key:

    GEMINI_API_KEY=your_api_key_here

If you do not set a Gemini key, you can still run retrieval only mode.

---

## Running DocuBot

Start the program:

    python main.py

Choose a mode:

- **1**: Naive LLM (Gemini reads the full docs)  
- **2**: Retrieval only (no LLM)  
- **3**: RAG (retrieval + Gemini)

You can use built in sample queries or type your own.

---

## Running Retrieval Evaluation (optional)

    python evaluation.py

This prints simple retrieval hit rates for sample queries.

---

## Modifying the Project

You will primarily work in:

- `docubot.py`  
  Implement or improve the retrieval index, scoring, and snippet selection.

- `llm_client.py`  
  Adjust the prompts and behavior of LLM responses.

- `dataset.py`  
  Add or change sample queries for testing.

---

## Requirements

- Python 3.9+
- A Gemini API key for LLM features (only needed for modes 1 and 3)
- No database, no server setup, no external services besides LLM calls
