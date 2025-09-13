# AI-Powered Credit Default & Late Payment Check Service 🤖

This project provides a robust **FastAPI service** for an AI agent to proactively check on credit card defaults and late payments. It leverages a combination of technologies for real-time communication, speech-to-text (STT), text-to-speech (TTS), and local large language model (LLM) processing. Additionally, it includes a simulation service to test and refine the agent's conversational prompts.

-----

## Features ✨

  * **Automated Call Initiation:** An endpoint to start a call to a specified number, connecting it to the AI agent.
  * **Real-time Communication:** Utilizes LiveKit for audio rooms and Twilio for telephony to handle live calls.
  * **Advanced Speech Processing:**
      * **Deepgram** for highly accurate Speech-to-Text (STT) transcription.
      * **ElevenLabs** for natural and high-quality Text-to-Speech (TTS) generation.
  * **Local LLM Processing:** Employs **Ollama CLI** to run **Llama 3.1:8B** locally, ensuring low latency and data privacy for all LLM-related tasks.
  * **Call and Room Status Monitoring:** Endpoints to check the live status of active calls and LiveKit rooms.
  * **Post-Call Analytics:**
      * Saves raw call transcripts locally after each call.
      * An endpoint to analyze transcripts, providing insights and categorizing risk (**LOW**, **MEDIUM**, **HIGH**) based on the conversation.
      * Saves these insights as JSON files for easy access and review.
  * **Agent Prompt Simulation & Refinement:** A dedicated service and endpoint for testing the agent's base prompt against various "defaulter" personas. It simulates conversations, collects metrics, and suggests a refined prompt.

-----

## Setup and Installation 🛠️

### Prerequisites

  * **Python 3.11**
  * **Ollama CLI:** Follow the official [Ollama installation guide](https://ollama.com/download) to install and set up the command-line interface.
  * **Llama 3.1:8B Model:** You need to pull the Llama 3.1:8B model using Ollama.
    ```bash
    ollama pull llama3.1:8B
    ```
  * **API Keys:** You'll need API keys for the following services:
      * **Twilio:** For call initiation.
      * **LiveKit:** For creating and managing audio rooms.
      * **Deepgram:** For STT.
      * **ElevenLabs:** For TTS.

### Local Environment Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/AK-Zero/mini-tely-agent.git
    cd mini-river-agent
    ```

2.  **Create a virtual environment and activate it:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the required dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Create a `.env` file in the root directory of your project referring `.env.example`

-----

## Usage 🚀

### Running the Services

Run the FastAPI service:

```bash
uvicorn main:app --reload
```

The service will be accessible at `http://127.0.0.1:8000`. You can view the interactive API documentation at `http://127.0.0.1:8000/docs`.

### API Endpoints 🌐

  * **Initiate a Call**

      * `POST /api/initiate/call`
      * **Description:** Starts a call to the specified phone number, connecting it to the AI agent.
      * **Request Body Example:**
        ```json
            {
            "phone_number": "+919043925960",
            "customer_name": "Abhinav",
            "amount_due": 1970,
            "card_number_ending": "1342",
            "agent_instructions": "OPTIONAL PROMPT FOR THE AGENT"
            }
        ```

  * **Check Call Status**

      * `GET /api/call-status/{room_name}`
      * **Description:** Retrieves the current status of a call using its `room_name`.

  * **Analyze Transcripts**

      * `GET /api/generate/insights`
      * **Description:** Processes all raw call transcripts saved on the machine, generating insights and assigning a risk category (**LOW**, **MEDIUM**, **HIGH**). The results are saved as a JSON file.

  * **Simulate Agent Conversation**

      * `POST /testing/train/prompt`
      * **Description:** Runs a simulation to test and refine the agent's prompt with custom persona.
      * **Request Body Example:**
        ```json
        {
        "base_agent_prompt": "string",
        "personas": [
            {
            "name": "Angry User",
            "persona_prompt": "You are a person with anger issues and have defaulted on your credit card for over 25000 dollars, and you dont plan on paying it back."
            }
        ],
        "max_turns": 8
        }
        ```
      * **Response:** Returns the final ratings and the refined prompt after the simulation.

  * **Simulate Agent Conversation**

      * `POST /testing/train/prompt/auto`
      * **Description:** Runs a simulation to test and refine the agent's prompt with persona generation,
      * **Request Body Example:**
        ```json
        {
        "base_agent_prompt": "string",
        "persona_names": [
            "Laid off executive"
        ],
        "max_turns": 8
        }
        ```
      * **Response:** Returns the final ratings and the refined prompt after the simulation.

-----

## Contributing 🤝

Feel free to open issues or submit pull requests to improve the project.