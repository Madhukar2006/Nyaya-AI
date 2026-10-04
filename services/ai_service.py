import os
from groq import Groq
from config import Config

# Initialize Groq client — API key comes from environment, never hardcoded
def _get_client():
    api_key = Config.GROQ_API_KEY
    if not api_key or api_key == 'your_groq_api_key_here':
        return None, "GROQ_API_KEY is not configured. Please set it in your .env file."
    return Groq(api_key=api_key), None


SYSTEM_PROMPT = """You are NyayaAI, a helpful AI assistant specializing in general legal information for Indian law.

Your role:
- Provide clear, general legal information about Indian laws and legal processes
- Explain legal concepts in simple, easy-to-understand language
- Support queries in English, Hindi, and Hinglish — respond in the same language the user uses
- Always recommend consulting a qualified lawyer for serious or specific legal matters
- Mention clearly when you are uncertain about a specific legal detail
- Ask clarifying questions when important information is missing
- Give practical general information and explain possible next steps

You must NEVER:
- Claim to be a lawyer or provide formal legal advice
- Guarantee any specific legal outcome
- Invent laws, court cases, judgments, or legal sections that do not exist
- Fabricate citations, legal sources, or case references
- Provide instructions for any illegal activity

When answering:
- Keep responses clear, structured, and concise
- Use bullet points or numbered lists for steps and options
- Explain legal terms in simple language immediately after using them
- For emergencies or serious situations, recommend contacting appropriate authorities
- End serious matter responses with a reminder to consult a qualified legal professional

You cover topics including: criminal law, civil law, consumer rights, property law,
family law, employment law, cyber crime, contracts, RTI, and general legal procedures in India.

Always end relevant responses with:
"⚖️ NyayaAI provides general legal information only and is not a substitute for professional legal advice. Please consult a qualified lawyer for your specific situation."
"""


def get_ai_response(user_message, conversation_history=None):
    """
    Get a legal information response from Groq AI.
    Returns (response_text, error_message)
    """
    client, err = _get_client()
    if err:
        return None, err

    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add conversation history for context (last 10 messages for context window efficiency)
        if conversation_history:
            for msg in conversation_history:
                role = msg['role'] if msg['role'] in ('user', 'assistant') else 'user'
                messages.append({"role": role, "content": msg['content']})

        # Add the current user message
        messages.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=messages,
            max_tokens=1500,
            temperature=0.7
        )

        answer = response.choices[0].message.content
        return answer, None

    except Exception as e:
        error_str = str(e).lower()
        if 'rate limit' in error_str or 'rate_limit' in error_str:
            return None, "The AI service is temporarily rate-limited. Please wait a moment and try again."
        elif 'api key' in error_str or 'authentication' in error_str or 'invalid_api_key' in error_str:
            return None, "Invalid or missing GROQ_API_KEY. Please check your .env file."
        else:
            return None, "The AI service is temporarily unavailable. Please try again in a moment."


def analyze_document(document_text, analysis_type="full"):
    """
    Analyze a legal document using Groq AI.
    analysis_type: 'full' | 'summarize' | 'simple' | 'key_points' | 'dates' | 'legal_terms'
    Returns (result_text or analysis_dict, error_message)
    """
    client, err = _get_client()
    if err:
        return None, err

    try:
        if analysis_type == "summarize":
            prompt = f"""Summarize this document in 3-5 clear, simple sentences. Focus on the main purpose and key obligations.

Document:
{document_text[:8000]}

Note: This summary is for general informational purposes only, not legal advice."""

        elif analysis_type == "simple":
            prompt = f"""Explain this document in very simple language that anyone can understand, as if explaining to someone with no legal knowledge. What does it mean? What does it require? What rights and obligations does it create?

Document:
{document_text[:8000]}

Note: This explanation is for general informational purposes only, not legal advice."""

        elif analysis_type == "key_points":
            prompt = f"""List the most important points in this document using clear bullet points (- prefix). Focus on key obligations, rights, conditions, and consequences.

Document:
{document_text[:8000]}

Note: This analysis is for general informational purposes only, not legal advice."""

        elif analysis_type == "dates":
            prompt = f"""Identify and list all important dates, deadlines, and time periods mentioned in this document. For each, explain its significance clearly.

Document:
{document_text[:8000]}

Note: This analysis is for general informational purposes only, not legal advice."""

        elif analysis_type == "legal_terms":
            prompt = f"""Identify all difficult or technical legal terms in this document and explain each one in simple, plain language.

Document:
{document_text[:8000]}

Note: This explanation is for general informational purposes only, not legal advice."""

        else:  # full analysis
            prompt = f"""Analyze this legal document and provide a structured analysis with these four sections:

1. SUMMARY
Provide a brief 2-3 sentence summary of this document.

2. IMPORTANT POINTS
List the key important points (use bullet points with - prefix).

3. POSSIBLE CONCERNS
List any potential legal concerns or issues (use bullet points with - prefix).

4. QUESTIONS TO ASK A LAWYER
List 3-5 specific questions a person should ask their lawyer about this document (use bullet points with - prefix).

Document text:
{document_text[:8000]}

IMPORTANT: This analysis is for general informational purposes only and is not legal advice."""

        response = client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a legal document analyzer. Provide clear, structured information in plain text. Never fabricate legal citations, sections, or court cases. Always clarify that your analysis is for informational purposes only."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.5
        )

        answer = response.choices[0].message.content

        if analysis_type == "full":
            return _parse_document_analysis(answer), None
        else:
            return answer, None

    except Exception as e:
        error_str = str(e).lower()
        if 'rate limit' in error_str or 'rate_limit' in error_str:
            return None, "The AI service is temporarily rate-limited. Please wait a moment and try again."
        else:
            return None, "The AI service is temporarily unavailable. Please try again."


def _parse_document_analysis(text):
    """Parse the AI full-analysis response into sections."""
    sections = {
        'summary': '',
        'important_points': '',
        'possible_concerns': '',
        'questions_for_lawyer': ''
    }

    lines = text.split('\n')
    current_section = None
    current_content = []

    section_markers = {
        'SUMMARY': 'summary',
        'IMPORTANT POINTS': 'important_points',
        'POSSIBLE CONCERNS': 'possible_concerns',
        'QUESTIONS TO ASK A LAWYER': 'questions_for_lawyer'
    }

    for line in lines:
        line_upper = line.strip().upper()
        matched = False
        for marker, key in section_markers.items():
            if marker in line_upper and (
                line_upper.startswith(marker)
                or line_upper.startswith('1.')
                or line_upper.startswith('2.')
                or line_upper.startswith('3.')
                or line_upper.startswith('4.')
                or line_upper.startswith('**')
                or line_upper.startswith('#')
            ):
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = key
                current_content = []
                matched = True
                break
        if not matched and current_section:
            if line.strip():
                current_content.append(line)

    if current_section and current_content:
        sections[current_section] = '\n'.join(current_content).strip()

    # If parsing failed, put everything in summary
    if not any(sections.values()):
        sections['summary'] = text

    return sections
