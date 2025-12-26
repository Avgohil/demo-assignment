# TalentScout – AI-Powered Hiring Assistant Chatbot

## Project Overview

TalentScout is a production-ready, privacy-first conversational AI chatbot built with Streamlit for conducting initial candidate screening interviews in technical roles. The system uses a locally hosted Large Language Model (LLM) via Ollama, ensuring complete data privacy and eliminating dependency on external cloud APIs.

The chatbot conducts structured interviews by collecting candidate information sequentially, validating inputs, and generating role-specific technical questions based strictly on the candidate's declared technology stack. All conversation state is maintained in-memory using Streamlit's session management, with no data persistence to disk or external services.

This project demonstrates practical application of LLM prompt engineering, state management, and production-ready software design patterns for AI-powered recruitment workflows.

---

## Key Features

- **Privacy-First Architecture**: All LLM inference runs locally via Ollama—no data leaves the machine
- **Structured Conversation Flow**: Guided, sequential information collection with one question at a time
- **Intelligent Input Validation**: Field-specific validation for email, phone, and numeric inputs
- **Contextual Technical Questioning**: Generates questions strictly from declared technologies without assumptions
- **Session-Based State Management**: All data stored in Streamlit session state (volatile, no persistence)
- **Graceful Exit Handling**: Exit keywords allow candidates to terminate the interview at any point
- **Fallback Response Handling**: Polite redirection for unclear or off-topic user inputs
- **Personalized Interaction**: Uses candidate's first name throughout the conversation
- **Zero External Dependencies**: No cloud APIs, databases, or third-party services required

---

## Tech Stack

**Core Framework:**
- Python 3.8+
- Streamlit (web interface and session management)

**LLM Infrastructure:**
- Ollama (local LLM runtime)
- Llama 3.2 / Mistral / Phi-3 (recommended models)

**Additional Libraries:**
- python-dotenv (environment variable management)
- re (input validation via regex)

**Why Ollama?**
- Complete data privacy (no external API calls)
- Cost-effective (no per-token pricing)
- Low latency for local inference
- Full control over model selection and parameters
- Compliance-friendly for sensitive recruitment data

---

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- 8GB+ RAM (16GB recommended for larger models)
- Windows, macOS, or Linux

### Step 1: Install Ollama

**Windows:**
```bash
winget install Ollama.Ollama
```

**macOS:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Verify installation:
```bash
ollama --version
```

### Step 2: Pull a Language Model

```bash
ollama pull llama3.2:1b
```

**Model Recommendations:**
- `llama3.2:1b` (1.3GB) - Fastest, suitable for most screening tasks
- `llama3.2` (3GB) - Balanced performance
- `mistral` (4GB) - Higher quality responses
- `phi3` (2.3GB) - Efficient for CPU-only systems

### Step 3: Clone and Set Up the Project

```bash
git clone <repository-url>
cd talentscout
```

Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

Install dependencies:
```bash
pip install streamlit python-dotenv
```

### Step 4: Configure Environment Variables

Copy the example configuration:
```bash
copy .env.example .env  # Windows
cp .env.example .env    # macOS/Linux
```

Edit `.env` to set your LLM provider:
```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.2:1b
```

### Step 5: Run the Application

```bash
streamlit run app.py
```

The application will launch in your browser at `http://localhost:8501`.

---

## Usage Guide

### Starting the Interview

1. Launch the application using `streamlit run app.py`
2. The chatbot greets the candidate and requests their full name
3. Answer each question as it appears in the chat interface

### Information Collection Flow

The chatbot collects information in strict sequential order:

1. **Full Name** - No validation, accepts any text
2. **Email Address** - Validated via regex pattern
3. **Phone Number** - Minimum 10 digits required
4. **Years of Experience** - Numeric range 0-70
5. **Desired Position** - Open text field
6. **Current Location** - Open text field
7. **Tech Stack** - Comma-separated list (max 5 technologies)

After each valid input, the chatbot:
- Acknowledges the response
- Immediately prompts for the next required field
- Uses the candidate's first name for personalization

### Technical Questions Phase

Once the tech stack is provided:
1. The LLM generates one question per declared technology (max 5)
2. Questions are presented sequentially, one at a time
3. The chatbot tracks progress (e.g., "Question 2/3")
4. After all questions are answered, the interview concludes

### Exit Handling

Type any of these commands (case-insensitive) to exit gracefully:
- `exit`
- `quit`
- `bye`
- `stop`

The chatbot will acknowledge the exit and display a closing message.

---

## Prompt Design Explanation

### Information Collection Prompts

The chatbot uses direct, single-field prompts with built-in validation:

```
"Ankita, what's your email address?"
```

**Design Rationale:**
- One question per turn eliminates ambiguity
- Personalization (first name) increases engagement
- Validation feedback is immediate and specific
- No assumptions about user intent

### Technical Question Generation Prompt

```
You are a technical interviewer.

The candidate has explicitly declared the following tech stack:
Python, ML, SQL

Position: AI Engineer

ABSOLUTE RULES (NO EXCEPTIONS):
1. Generate questions ONLY from the exact technologies listed.
2. If the stack contains ONLY "Python":
   - Ask ONLY core Python questions (syntax, data types, functions, OOP).
   - Do NOT mention or assume ML, NLP, AI, data science, or libraries.
3. Do NOT introduce any tools, frameworks, or libraries unless explicitly provided.
4. Generate exactly ONE question per technology.
5. Do NOT add explanations, assumptions, or extra context.
6. Questions must be practical and role-relevant.

OUTPUT FORMAT (MANDATORY):
Question 1 (Python):
<Question>

Question 2 (ML):
<Question>

Only output the questions. Nothing else.
```

**Design Rationale:**
- Explicit constraints prevent LLM hallucination
- Technology-specific rules (e.g., "Python" ≠ "Django") avoid assumptions
- Numbered format enables reliable parsing
- Single API call reduces latency
- Temperature 0.7 balances creativity and consistency

### Fallback Handling

When input is unclear or validation fails:
- Re-state the current question clearly
- Provide example format (e.g., "john@example.com")
- Do not advance to the next field
- Do not assume user intent

---

## Architecture Decisions

### 1. Local LLM via Ollama

**Decision:** Use Ollama for all LLM inference instead of cloud APIs.

**Reasoning:**
- **Privacy Compliance**: Recruitment data never leaves the local machine
- **Cost Control**: No per-token pricing or rate limits
- **Reliability**: No internet dependency for core functionality
- **Customization**: Full control over model selection and parameters
- **Latency**: Local inference is faster than API round-trips for small models

**Trade-offs:**
- Requires local compute resources (CPU/GPU)
- Model quality depends on hardware capabilities
- Initial setup complexity (model download)

### 2. Session State Management

**Decision:** Store all conversation data in `st.session_state` with no persistence.

**Reasoning:**
- Streamlit's native state management integrates seamlessly
- Volatile storage aligns with privacy-first design
- No database overhead or configuration
- Session isolation prevents data leakage between users

**Implementation:**
```python
st.session_state.candidate_info = {
    "full_name": None,
    "email": None,
    "phone": None,
    ...
}
```

### 3. Modular Code Structure

**Functions:**
- `initialize_session_state()`: Sets up conversation state on first load
- `call_llm()`: Centralized LLM API wrapper with error handling
- `process_user_input()`: Input validation and state updates
- `generate_technical_questions()`: LLM prompt construction and parsing
- `display_chat_interface()`: UI rendering and user interaction loop

**Benefits:**
- Testable components
- Easy to extend (e.g., add new LLM providers)
- Clear separation of concerns

### 4. Conversation Flow States

```
greeting → information_gathering → technical_questions → answering_questions → completed
```

**State Transitions:**
- `greeting`: Display welcome message
- `information_gathering`: Collect 7 fields sequentially
- `technical_questions`: Generate questions from tech stack
- `answering_questions`: Present questions one by one
- `completed`: Display final message and disable input

**Benefits:**
- Prevents question repetition
- Handles Streamlit's rerun model correctly
- Easy to debug conversation flow

### 5. Validation Strategy

| Field | Validation Method | Example Failure |
|-------|------------------|-----------------|
| Email | Regex: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$` | "invalid@" |
| Phone | Minimum 10 digits (ignores formatting) | "123456" |
| Years | Numeric range 0-70 | "abc" or "100" |
| Tech Stack | Comma-separated, max 5 items | "" (empty) |

**Trade-offs:**
- Phone validation is permissive (allows international formats)
- Email regex is basic (doesn't catch all edge cases)
- Years range assumes typical career span

---

## Data Privacy Notes

### What This System Does NOT Do

- Does NOT send data to external APIs
- Does NOT persist data to disk, databases, or logs
- Does NOT use cookies or browser tracking
- Does NOT share data across sessions

### What This System DOES Do

- Stores data temporarily in Streamlit session state (RAM only)
- Processes all LLM inference locally via Ollama
- Clears all data when the browser tab is closed
- Isolates each session's data from other concurrent users

### Privacy Advantages of Local LLM

1. **No Data Transmission**: Candidate information never leaves the machine
2. **GDPR Compliance**: No third-party data processors involved
3. **Audit Trail Control**: Complete visibility into data handling
4. **Air-Gapped Deployment**: Can run on isolated networks

### Production Considerations

For real-world deployment:
- Add explicit consent forms before data collection
- Implement session timeout mechanisms
- Consider encrypting session state for multi-tenant deployments
- Log only anonymized metadata (e.g., session start/end times)

---

## Challenges & Solutions

### Challenge 1: Controlling LLM Hallucination

**Problem:** LLMs may generate questions about technologies not declared by the candidate (e.g., asking about Django when only "Python" was mentioned).

**Solution:**
- Use explicit, rule-based prompts with negative constraints
- Include examples of prohibited behavior in the prompt
- Parse LLM output with regex to validate question format
- Limit max tokens to 500 to prevent verbose, off-topic responses

**Result:** Question generation stays strictly within declared tech stack.

### Challenge 2: Streamlit Rerun Model

**Problem:** Streamlit reruns the entire script on every user interaction, which can cause:
- Question repetition
- State inconsistencies
- UI flicker

**Solution:**
- Track conversation stage in `st.session_state.stage`
- Check if data fields are `None` before prompting
- Use `st.rerun()` only after state updates
- Maintain conversation history to display past messages

**Result:** Smooth, chat-like UX without repetition.

### Challenge 3: Unclear User Intent

**Problem:** Users might provide vague responses (e.g., "next?" instead of answering the question).

**Solution:**
- After each acknowledgment, immediately display the next question
- Use the candidate's first name for clarity
- Provide example formats for validated fields
- Never assume what the user meant

**Result:** Users are always guided to provide the expected input.

### Challenge 4: Technical Question Relevance

**Problem:** Generated questions might be too generic or assume advanced knowledge.

**Solution:**
- Include the candidate's position in the LLM prompt
- Specify "practical and role-relevant" in the prompt constraints
- Use temperature 0.7 for balanced creativity
- Limit to 1 question per technology to maintain focus

**Result:** Questions are concise, relevant, and tied to declared skills.

### Challenge 5: Parsing LLM Output

**Problem:** LLM output format may vary (e.g., "1.", "Question 1:", "Q1:").

**Solution:**
- Enforce strict output format in the prompt
- Use regex pattern `^Question\s+\d+` to parse responses
- Strip prefixes to extract clean question text
- Fallback to empty list if parsing fails

**Result:** Reliable extraction of questions for display.

---

## File Structure

```
talentscout/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── .env.example          # Environment variable template
└── .env                  # User configuration (not in version control)
```

### Key Files

**app.py**: Contains all application logic including:
- LLM client initialization (supports OpenAI, Anthropic, Gemini, Ollama)
- Session state management functions
- Input validation and processing
- Conversation flow control
- UI rendering

**requirements.txt**: Minimal dependencies for production deployment.

**.env**: Configuration for LLM provider, model selection, and API endpoints.

---

## Future Enhancements

### Short-Term Improvements
- Add input sanitization for XSS prevention
- Implement session timeout after inactivity
- Add unit tests for validation functions
- Support multi-language interfaces

### Long-Term Features
- Resume parsing and skills extraction
- Candidate scoring based on responses
- Email notifications to recruiters
- Integration with Applicant Tracking Systems (ATS)
- Voice interface for accessibility
- Question difficulty adjustment based on experience level

### Infrastructure Enhancements
- Docker containerization for easy deployment
- Support for GPU acceleration (CUDA/ROCm)
- Model quantization for faster inference
- Load balancing for concurrent sessions

---

## Troubleshooting

### Issue: "Ollama connection refused"
**Cause**: Ollama service is not running.
**Solution**: Start Ollama with `ollama serve` or restart the Ollama application.

### Issue: "Model not found"
**Cause**: Specified model has not been pulled.
**Solution**: Run `ollama pull <model-name>` before launching the app.

### Issue: "Slow question generation"
**Cause**: Large model or CPU-only inference.
**Solution**: Switch to a smaller model (e.g., `llama3.2:1b`) or enable GPU support.

### Issue: "Conversation state lost on refresh"
**Cause**: Browser tab was closed or page was hard-refreshed.
**Solution**: This is expected behavior. Session state is volatile by design.

### Issue: "Technical questions include unrelated technologies"
**Cause**: LLM hallucination despite prompt constraints.
**Solution**: Reduce temperature to 0.5 or switch to a more instruction-following model (e.g., Mistral).

---

## License

This project is provided as-is for educational and demonstration purposes. Free to use, modify, and distribute for non-commercial applications.

For commercial deployment, ensure compliance with:
- Data protection regulations (GDPR, CCPA, etc.)
- Ollama model licenses (check individual model terms)
- Employment screening laws in your jurisdiction

---

## Acknowledgments

- **Ollama**: For providing an excellent local LLM runtime
- **Streamlit**: For the intuitive web framework
- **Meta AI / Mistral AI**: For open-source language models

---

## Contact

For questions, issues, or contributions, please open an issue in the repository or contact the maintainer.

**Built for privacy, designed for efficiency, optimized for recruitment workflows.**
