import gradio as gr
import io
import re
from collections import Counter

# TEXT EXTRACTION (PDF or DOCX)

def extract_text_from_any(file_bytes: bytes):
    """
    Accepts raw bytes (from gr.File with type='binary') and returns plain text.
    Tries PDF first, then DOCX. Returns (text, error_message).
    If everything fails, text = "" and error_message is non-empty.
    """
    if file_bytes is None or len(file_bytes) == 0:
        return "", "Please upload a file."

    text = ""

    # Try PDF first
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        pages = []
        for page in reader.pages:
            try:
                t = page.extract_text() or ""
            except Exception:
                t = ""
            pages.append(t)
        text = "\n".join(pages)
        if text.strip():
            return text, ""
    except Exception:
        # Ignore and try DOCX
        pass

    # Try DOCX
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs]
        text = "\n".join(paragraphs)
        if text.strip():
            return text, ""
    except Exception:
        pass

    return "", "Could not read this file. Make sure it is a PDF or DOCX and that PyPDF2/python-docx are installed."


# SIMPLE KEYWORD TOKENIZATION
STOPWORDS = {
    "the","and","for","with","you","your","from","that","this","are","was","were",
    "have","has","had","will","would","shall","can","could","may","might",
    "a","an","in","on","at","of","to","as","by","or","if","it","its","is","be",
    "our","we","they","their","them","us","i"
}

def tokenize(text: str):
    text = text.lower()
    words = re.findall(r"[a-z0-9]+", text)
    return [w for w in words if len(w) > 2 and w not in STOPWORDS]


# MATCH SCORE (PERCENT)
def compute_match_score(resume_text: str, jd_text: str):
    """
    Very simple "AI-style" match score based on keyword overlap.
    - Tokenize resume and job description.
    - Count frequency of each word in job description.
    - Score = (sum of frequencies of words that also appear in resume)
              / (total job description word frequency) * 100.
    Returns (score_percent, top_overlapping_keywords).
    """
    resume_tokens = tokenize(resume_text)
    jd_tokens = tokenize(jd_text)

    if not jd_tokens or not resume_tokens:
        return 0.0, []

    resume_set = set(resume_tokens)
    jd_counts = Counter(jd_tokens)

    overlap_tokens = [w for w in jd_counts if w in resume_set]
    if not overlap_tokens:
        return 0.0, []

    raw_score = sum(jd_counts[w] for w in overlap_tokens)
    max_score = sum(jd_counts.values())
    if max_score == 0:
        return 0.0, []

    score = (raw_score / max_score) * 100.0

    # Top overlapping keywords, sorted by importance in JD
    top_overlapping = sorted(overlap_tokens, key=lambda w: jd_counts[w], reverse=True)[:15]

    return round(score, 1), top_overlapping


# MAIN HANDLER
def analyze_fit(resume_bytes, jd_bytes, extra_keywords_text: str):
    """
    Main function: reads files, computes match score, and reports details.
    extra_keywords_text is an optional comma separated list of keywords
    the user wants to track explicitly.
    """
    # Check both files
    if resume_bytes is None and jd_bytes is None:
        return "0 %", "Please upload both a resume and a job description."
    if resume_bytes is None:
        return "0 %", "Please upload a resume file."
    if jd_bytes is None:
        return "0 %", "Please upload a job description file."

    # Extract text
    resume_text, err_resume = extract_text_from_any(resume_bytes)
    if err_resume:
        return "0 %", f"Resume error: {err_resume}"

    jd_text, err_jd = extract_text_from_any(jd_bytes)
    if err_jd:
        return "0 %", f"Job description error: {err_jd}"

    if not resume_text.strip():
        return "0 %", "Could not read any text from the resume. It may be scanned or image-only."
    if not jd_text.strip():
        return "0 %", "Could not read any text from the job description. It may be scanned or image-only."

    # Compute score
    score, top_keywords = compute_match_score(resume_text, jd_text)

    # Token sets for extra keyword checking
    resume_token_set = set(tokenize(resume_text))

    # Parse extra keywords (comma separated)
    extra_keywords_text = extra_keywords_text or ""
    raw_extra_keywords = [kw.strip().lower() for kw in extra_keywords_text.split(",") if kw.strip()]
    matched_extra = []
    missing_extra = []

    if raw_extra_keywords:
        for kw in raw_extra_keywords:
            if kw in resume_token_set:
                matched_extra.append(kw)
            else:
                missing_extra.append(kw)

    # Build details text
    details_lines = []
    details_lines.append(f"Estimated AI match score: {score} %")
    details_lines.append("")
    if top_keywords:
        details_lines.append("Top overlapping keywords between resume and job description:")
        for kw in top_keywords:
            details_lines.append(f"- {kw}")
    else:
        details_lines.append("No strong keyword overlap found. The resume might be too generic or not aligned with this job description.")

    # Extra keyword section
    if raw_extra_keywords:
        details_lines.append("")
        details_lines.append("Additional keywords you asked to track (comma separated input):")
        if matched_extra:
            details_lines.append("Present in the resume:")
            for kw in matched_extra:
                details_lines.append(f"- {kw}")
        if missing_extra:
            details_lines.append("Missing from the resume:")
            for kw in missing_extra:
                details_lines.append(f"- {kw}")

    details_lines.append("")
    details_lines.append("Important:")
    details_lines.append("- This is a simple keyword-based resume analyzer, not a full assessment of a candidate.")
    details_lines.append("- Humans are better at evaluating experience, context and potential.")
    details_lines.append("- Use this score as a rough signal only, never as the sole basis for hiring decisions.")

    return f"{score} %", "\n".join(details_lines)


# -----------------------------------
# GRADIO UI
# -----------------------------------
with gr.Blocks() as demo:
    gr.Markdown("## AI Resume vs Job Description Match (Keyword-Based)")

    gr.Markdown(
        """
This simple AI-assisted tool compares a **resume** to a **job description** using keyword overlap  
and estimates a rough “fit” score in **percent**.
**How to use**
1. Upload the candidate’s **resume** (PDF or Word DOCX) in the left box.  
2. Upload the **job description** (PDF or Word DOCX) in the right box.  
3. (Optional) Type **additional keywords** you want to track, separated by commas  
   (for example: `python, sql, tableau`).  
4. Click **Analyze**.  
5. Review:
   - The **Estimated Match score (%)**  
   - The list of **top overlapping keywords** between the resume and the job description.  
   - A breakdown of your **additional keywords** that are present or missing in the resume.
**Important note**
- This is a **basic, keyword-based analyzing tool**.  
- It does **not** understand context, quality of experience or potential.  
- **Humans are better** at evaluating candidates. Do not fully rely on this score for hiring decisions.  
- Treat this as a quick screening aid, not a final decision-maker.
        """
    )

    with gr.Row():
        resume_file = gr.File(
            label="Upload Resume (PDF or DOCX)",
            file_types=[".pdf", ".docx"],
            type="binary"
        )
        jd_file = gr.File(
            label="Upload Job Description (PDF or DOCX)",
            file_types=[".pdf", ".docx"],
            type="binary"
        )

    # New textbox for additional keywords
    extra_keywords_input = gr.Textbox(
        label="Additional keywords to track (optional)",
        placeholder="e.g. Excel, python, tableau....."
    )

    analyze_button = gr.Button("Analyze")

    score_output = gr.Textbox(
        label="Estimated Matching Score (%)",
        interactive=False
    )

    details_output = gr.Textbox(
        label="Details",
        lines=18,
        interactive=False
    )

    analyze_button.click(
        fn=analyze_fit,
        inputs=[resume_file, jd_file, extra_keywords_input],
        outputs=[score_output, details_output]
    )

if __name__ == "__main__":
    demo.launch()
