"""
TalentScout - AI-Powered Hiring Assistant Chatbot

CONVERSATION RULES:
- Ask one question at a time with clear guidance
- Collect 7 pieces of information sequentially
- Validate structured inputs (email, phone, years)
- Generate 3-5 technical questions based on declared tech stack only
- Never assume related technologies or libraries
- Support exit keywords: exit, quit, bye, stop

TECH STACK NORMALIZATION:
- Trim whitespace and remove duplicates
- Map common variants (e.g., "ml basics" → "Machine Learning")
- Validate and ignore unrecognized technologies
- Use ONLY normalized technologies for questions

QUESTION DISTRIBUTION:
- 1 technology: 2-3 questions
- 2 technologies: 1-2 questions each
- 3+ technologies: 1 question each
- Total: 3-5 questions maximum
"""

import streamlit as st
import re
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Recognized technologies for validation
RECOGNIZED_TECHNOLOGIES = {
    "python", "javascript", "java", "c++", "c#", "golang", "rust", "php",
    "ruby", "typescript", "kotlin", "swift", "r", "scala", "perl",
    "machine learning", "ml", "artificial intelligence", "ai",
    "data science", "data analysis", "analytics",
    "sql", "database", "postgresql", "mysql", "mongodb", "nosql",
    "react", "angular", "vue", "svelte", "html", "css",
    "nodejs", "express", "django", "flask", "spring", "fastapi",
    "docker", "kubernetes", "aws", "gcp", "azure", "devops",
    "git", "linux", "windows", "macos"
}

# Variant mappings for normalization
TECH_VARIANTS = {
    "ml basics": "Machine Learning",
    "ml fundamentals": "Machine Learning",
    "ml": "Machine Learning",
    "ai": "Artificial Intelligence",
    "ai basics": "Artificial Intelligence",
    "py": "Python",
    "sql": "SQL",
    "db": "Database",
    "frontend": "Frontend",
    "backend": "Backend",
    "fullstack": "Fullstack",
    "web": "Web Development",
    "mobile": "Mobile Development"
}
import re
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# LLM Configuration - Change this to use different providers
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # Options: openai, anthropic, gemini, ollama

# Initialize LLM clients based on provider
if LLM_PROVIDER == "openai":
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
elif LLM_PROVIDER == "anthropic":
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    except ImportError:
        raise ImportError("Please install anthropic: pip install anthropic")
elif LLM_PROVIDER == "gemini":
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        client = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))
        MODEL = None
    except ImportError:
        raise ImportError("Please install google-generativeai: pip install google-generativeai")
elif LLM_PROVIDER == "ollama":
    from openai import OpenAI
    # Ollama uses OpenAI-compatible API
    client = OpenAI(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        api_key="ollama"  # Ollama doesn't need API key
    )
    MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
else:
    raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")

# Initialize session state
def initialize_session_state():
    """Initialize all session state variables for conversation flow."""
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "stage" not in st.session_state:
        st.session_state.stage = "greeting"
    if "candidate_info" not in st.session_state:
        st.session_state.candidate_info = {
            "full_name": None,
            "email": None,
            "phone": None,
            "years_of_experience": None,
            "desired_position": None,
            "current_location": None,
            "tech_stack": None,
        }
    if "tech_stack_list" not in st.session_state:
        st.session_state.tech_stack_list = []
    if "questions_asked" not in st.session_state:
        st.session_state.questions_asked = 0
    if "generated_questions" not in st.session_state:
        st.session_state.generated_questions = []

def call_llm(prompt: str) -> str:
    """Call configured LLM with structured prompt."""
    try:
        if LLM_PROVIDER == "openai" or LLM_PROVIDER == "ollama":
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500,
            )
            return response.choices[0].message.content.strip()
        
        elif LLM_PROVIDER == "anthropic":
            response = client.messages.create(
                model=MODEL,
                max_tokens=500,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
        
        elif LLM_PROVIDER == "gemini":
            response = client.generate_content(
                prompt,
                generation_config={"temperature": 0.7, "max_output_tokens": 500}
            )
            return response.text.strip()
        
    except Exception as e:
        st.error(f"Error calling {LLM_PROVIDER.upper()} LLM: {e}")
        return "I encountered an error. Please try again."

def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """Validate phone number (basic check for digits and length)."""
    digits = re.sub(r"\D", "", phone)
    return len(digits) >= 10

def validate_years_of_experience(years: str) -> bool:
    """Validate years of experience is a positive number."""
    try:
        num = float(years)
        return 0 <= num <= 70
    except ValueError:
        return False

def parse_tech_stack(tech_stack_str: str) -> tuple[list, list]:
    """
    Parse and normalize tech stack with variant mapping.
    Returns: (normalized_techs, ignored_techs)
    """
    techs = [tech.strip() for tech in tech_stack_str.split(",") if tech.strip()]
    
    normalized = []
    ignored = []
    seen = set()
    
    for tech in techs:
        tech_lower = tech.lower()
        
        # Check variant mappings first
        if tech_lower in TECH_VARIANTS:
            mapped = TECH_VARIANTS[tech_lower]
            if mapped.lower() not in seen:
                normalized.append(mapped)
                seen.add(mapped.lower())
        # Check recognized technologies
        elif tech_lower in RECOGNIZED_TECHNOLOGIES:
            title_case = tech.title()
            if title_case.lower() not in seen:
                normalized.append(title_case)
                seen.add(title_case.lower())
        else:
            # Unrecognized technology
            ignored.append(tech)
    
    return normalized[:5], ignored  # Limit to 5 technologies


def get_first_name() -> str:
    """Return the first name if available, otherwise a friendly fallback."""
    full_name = st.session_state.candidate_info.get("full_name") if "candidate_info" in st.session_state else None
    return full_name.strip().split()[0] if full_name else "there"

def generate_technical_questions(tech_stack: list, position: str) -> list:
    """
    Generate technical questions based on tech stack and position.
    
    Question Distribution Logic:
    - 1 technology → 2-3 questions
    - 2 technologies → 1-2 questions per technology
    - 3+ technologies → 1 question per technology
    - Total: 3-5 questions maximum
    """
    if not tech_stack:
        return []
    
    tech_list_str = ", ".join(tech_stack)
    num_techs = len(tech_stack)
    
    # Determine number of questions
    if num_techs == 1:
        num_questions = "2 to 3"
    elif num_techs == 2:
        num_questions = "1 to 2 per technology (total 2-4)"
    else:
        num_questions = "exactly 1 per technology"
    
    prompt = f"""You are a technical interviewer conducting an initial screening.

The candidate has declared the following tech stack:
{tech_list_str}

Position: {position}

STRICT RULES (NON-NEGOTIABLE):
1. Generate {num_questions} questions ONLY from the technologies listed above.
2. Total questions must be BETWEEN 3 and 5.
3. Do NOT assume related domains, tools, or libraries:
   - "Machine Learning" does NOT include NLP, LLMs, chatbots, or AI.
   - "Python" means core Python only (syntax, data structures, OOP).
   - "SQL" means database queries only (no specific DBMS features).
4. Questions must be practical, beginner-friendly, and screening-level.
5. Do NOT evaluate, judge, or add explanations.
6. Do NOT introduce technologies not listed.

OUTPUT FORMAT (MANDATORY):

Question 1 ({tech_stack[0]}):
<Question text here>

Question 2 ({tech_stack[1] if num_techs > 1 else tech_stack[0]}):
<Question text here>

Continue for all questions.

IMPORTANT: Output ONLY the numbered questions. Nothing else."""
    
    response = call_llm(prompt)
    
    # Parse response into individual questions
    questions = []
    for line in response.split("\n"):
        line = line.strip()
        if line and re.match(r"^Question\s+\d+", line):
            # Remove the "Question N (Tech):" prefix and keep just the question
            cleaned = re.sub(r"^Question\s+\d+\s*(\([^)]+\))?\s*[:.]\s*", "", line)
            if cleaned:
                questions.append(cleaned)
    
    # Ensure we return 3-5 questions
    if len(questions) < 3:
        return questions  # Return what we have if less than 3
    return questions[:5]  # Cap at 5
    return questions[:5]  # Ensure max 5 questions

def get_greeting_message() -> str:
    """Generate greeting message."""
    return """👋 Welcome to **TalentScout** – Your AI-Powered Hiring Assistant!

I'm here to conduct your initial screening interview. This will take about 5-10 minutes.

I'll ask you some questions about your background and technical skills. Please answer naturally, and feel free to type **exit**, **quit**, **bye**, or **stop** at any time to end the conversation.

Let's get started! 🚀

What's your full name?"""

def get_next_question() -> str:
    """Get the next question based on current stage."""
    info = st.session_state.candidate_info
    name = get_first_name()
    
    if info["full_name"] is None:
        return "What's your full name?"
    elif info["email"] is None:
        return f"{name}, what's your email address?"
    elif info["phone"] is None:
        return f"{name}, what's your phone number?"
    elif info["years_of_experience"] is None:
        return f"{name}, how many years of professional experience do you have?"
    elif info["desired_position"] is None:
        return f"{name}, what position are you applying for?"
    elif info["current_location"] is None:
        return f"{name}, what's your current location?"
    elif info["tech_stack"] is None:
        return f"{name}, what technologies are you proficient in? (Please provide a comma-separated list, e.g., Python, React, PostgreSQL)"
    else:
        return None

def process_user_input(user_input: str) -> str:
    """Process user input and update candidate info."""
    user_input = user_input.strip()
    
    # Check for exit commands
    if user_input.lower() in ["exit", "quit", "bye", "stop"]:
        st.session_state.stage = "exit"
        return "Thank you for your time! The recruitment team will review your information and follow up with you soon. Goodbye! 👋"
    
    info = st.session_state.candidate_info
    
    # Process based on current stage
    if info["full_name"] is None:
        st.session_state.candidate_info["full_name"] = user_input
        return f"Nice to meet you, {user_input}! 😊"
    
    elif info["email"] is None:
        if not validate_email(user_input):
            return "That doesn't look like a valid email address. Please provide a valid email (e.g., john@example.com)."
        st.session_state.candidate_info["email"] = user_input
        return "Great! Email saved."
    
    elif info["phone"] is None:
        if not validate_phone(user_input):
            return "That doesn't look like a valid phone number. Please provide a phone number with at least 10 digits."
        st.session_state.candidate_info["phone"] = user_input
        return "Perfect! Phone number saved."
    
    elif info["years_of_experience"] is None:
        if not validate_years_of_experience(user_input):
            return "Please provide a valid number of years (0-70)."
        st.session_state.candidate_info["years_of_experience"] = float(user_input)
        return f"Excellent! {user_input} years of experience noted."
    
    elif info["desired_position"] is None:
        st.session_state.candidate_info["desired_position"] = user_input
        return f"Interesting! {user_input} is a great role."
    
    elif info["current_location"] is None:
        st.session_state.candidate_info["current_location"] = user_input
        return f"Got it! You're based in {user_input}."
    
    elif info["tech_stack"] is None:
        normalized_stack, ignored = parse_tech_stack(user_input)
        if not normalized_stack and not ignored:
            return "Please provide at least one technology. For example: Python, JavaScript, SQL."
        elif not normalized_stack and ignored:
            # All technologies were unrecognized
            return f"I didn't recognize those technologies. Please provide at least one. Examples: Python, JavaScript, SQL, Machine Learning."
        else:
            # We have recognized technologies
            st.session_state.candidate_info["tech_stack"] = user_input
            st.session_state.tech_stack_list = normalized_stack
            st.session_state.stage = "technical_questions"
            
            response = f"Great! I've noted your tech stack: {', '.join(normalized_stack)}."
            
            # Notify if some technologies were ignored
            if ignored:
                response += f"\n\n(I noticed some unrecognized technologies: {', '.join(ignored)}. I'll proceed with the recognized ones.)"
            
            response += "\n\nLet's begin your technical questions."
            return response
    
    return "I didn't quite understand that. Could you please rephrase?"

def display_chat_interface():
    """Display the chat interface."""
    st.set_page_config(page_title="TalentScout", layout="centered")
    st.markdown("""
    <style>
    .chat-message {
        padding: 1rem;
        margin-bottom: 1rem;
        border-radius: 0.5rem;
    }
    .assistant {
        background-color: #e3f2fd;
        color: #1565c0;
    }
    .user {
        background-color: #f3e5f5;
        color: #6a1b9a;
        text-align: right;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("TalentScout 🤖")
    
    # Display conversation history
    for message in st.session_state.conversation_history:
        if message["role"] == "assistant":
            st.markdown(f'<div class="chat-message assistant">{message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-message user">{message["content"]}</div>', unsafe_allow_html=True)
    
    # Input handling
    if st.session_state.stage != "exit" and st.session_state.stage != "completed":
        user_input = st.chat_input("Your response:")
        
        if user_input:
            # Add user message to history
            st.session_state.conversation_history.append({"role": "user", "content": user_input})
            
            # Process input
            if st.session_state.stage == "greeting":
                response = process_user_input(user_input)
                st.session_state.stage = "information_gathering"
                next_q = get_next_question()
                if next_q:
                    response = f"{response}\n\n{next_q}"

            elif st.session_state.stage == "information_gathering":
                response = process_user_input(user_input)
                if st.session_state.stage == "exit":
                    pass
                elif st.session_state.stage == "technical_questions":
                    # Generate technical questions and move to answering
                    questions = generate_technical_questions(
                        st.session_state.tech_stack_list,
                        st.session_state.candidate_info["desired_position"]
                    )
                    st.session_state.generated_questions = questions
                    st.session_state.questions_asked = 0
                    if questions:
                        first_q = questions[0]
                        total = len(questions)
                        response += (
                            "\n\nThanks! I've noted your tech stack."\
                            "\n\nNow let's begin your technical questions."\
                            f"\n\nQuestion 1/{total}: {first_q}"\
                            "\n\nPlease provide your answer to this question."
                        )
                    else:
                        response += "\n\n(No technical questions generated—please check your tech stack.)"
                    st.session_state.stage = "answering_questions"
                else:
                    # Stay on information_gathering; always prompt the current required field
                    next_q = get_next_question()
                    if next_q:
                        response = f"{response}\n\n{next_q}"

            elif st.session_state.stage == "technical_questions":
                # Safety net in case the stage was left at technical_questions after a rerun
                questions = generate_technical_questions(
                    st.session_state.tech_stack_list,
                    st.session_state.candidate_info.get("desired_position", "the role")
                )
                st.session_state.generated_questions = questions
                response = "Here are your technical questions based on your tech stack:\n\n"
                if questions:
                    response += "\n\n".join(questions)
                else:
                    response += "(No technical questions generated—please provide your tech stack again.)"
                response += "\n\n---\n\nPlease provide your answers to these questions. You can answer them one by one or all at once."
                st.session_state.stage = "answering_questions"

            elif st.session_state.stage == "answering_questions":
                st.session_state.questions_asked += 1
                total = len(st.session_state.generated_questions)
                if total == 0:
                    response = "Thanks! I don't have recorded questions to track—let's consider the Q&A complete."
                    st.session_state.stage = "completed"
                elif st.session_state.questions_asked >= total:
                    response = "Thank you for answering all the questions! 🎉\n\nYour screening interview is complete. The recruitment team will review your responses and follow up with you soon at the email and phone number you provided.\n\nThank you for your time!"
                    st.session_state.stage = "completed"
                else:
                    idx = st.session_state.questions_asked
                    next_q = st.session_state.generated_questions[idx]
                    response = (
                        "Thank you for that answer!"\
                        f"\n\nQuestion {idx + 1}/{total}: {next_q}"\
                        "\n\nPlease provide your answer to this question."
                    )

            elif st.session_state.stage == "exit":
                response = "Thank you for your time! The recruitment team will review your information and follow up with you soon. Goodbye! 👋"
            
            # Add assistant response to history
            st.session_state.conversation_history.append({"role": "assistant", "content": response})
            st.rerun()
    
    elif st.session_state.stage == "completed":
        st.markdown("""
        <div class="chat-message assistant">
        Thank you for completing your screening interview! 🎉
        
        The recruitment team will review your responses and follow up with you soon.
        </div>
        """, unsafe_allow_html=True)
    
    elif st.session_state.stage == "exit":
        st.markdown("""
        <div class="chat-message assistant">
        Thank you for your time! The recruitment team will review your information and follow up with you soon. Goodbye! 👋
        </div>
        """, unsafe_allow_html=True)

def main():
    """Main application entry point."""
    initialize_session_state()
    
    # Display greeting on first load
    if not st.session_state.conversation_history:
        greeting = get_greeting_message()
        st.session_state.conversation_history.append({"role": "assistant", "content": greeting})
    
    display_chat_interface()

if __name__ == "__main__":
    main()
