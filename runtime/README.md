# Bot Builder Runtime — LangGraph Dialog Engine

A separate FastAPI service that executes dialog flows built in the Bot Builder as interactive, multi-turn chatbot conversations.

## How It Works

1. A flow (nodes + edges) is loaded from the same MongoDB used by the backend.
2. The flow is compiled into a **LangGraph** `StateGraph` — each node type becomes a graph node function.
3. Entity and Confirmation nodes use LangGraph's `interrupt()` to pause execution and wait for user input.
4. Session state is persisted per conversation via a `MemorySaver` checkpointer (in-memory; swap for a persistent store in production).
5. When the user responds, execution resumes with `Command(resume=text)` and continues until the next interrupt or the End node.

## Tech

- FastAPI (async)
- LangGraph + LangChain Core
- Motor (MongoDB async driver)
- sentence-transformers (entity extraction / semantic matching)
- numpy

## Local Setup

```bash
cd runtime
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env if needed (same MongoDB as the backend)
```

## Run

```bash
uvicorn runtime.main:app --reload --port 8001
```

Or from the project root:

```bash
uvicorn runtime.main:app --reload --port 8001
```

## API Endpoints

### `POST /api/sessions`

Start a new conversation session for a flow.

```json
{ "flow_id": "<mongo ObjectId>" }
```

**Response** (`201`):

```json
{
  "session_id": "abc123",
  "messages": [
    { "role": "bot", "text": "Welcome! How can I help?" }
  ],
  "status": "waiting_input",
  "input_prompt": {
    "type": "entity",
    "prompt": "What size pizza would you like?",
    "entity_name": "pizzaSize",
    "entity_type": "string"
  }
}
```

### `POST /api/sessions/{session_id}/message`

Send user input and get bot replies.

```json
{ "text": "Large" }
```

**Response** (`200`): same shape as above.

### `GET /api/sessions/{session_id}`

Get session metadata (status, extracted variables, message count).

### `DELETE /api/sessions/{session_id}`

End and remove a session.

### `GET /health`

Returns `{"ok": true}`.

## Node Types

| Type | Behaviour |
|------|-----------|
| **Start** | Passthrough — auto-advances to the next node |
| **End** | Marks the conversation as complete |
| **Message** | Sends a bot message (supports `{{variable}}` interpolation) |
| **Entity** | Prompts the user, extracts a typed value, stores it in variables |
| **Confirmation** | Asks a yes/no question, routes via conditional edges |
| **Tool** | Placeholder for external API calls |

## Entity Extraction

Built-in regex extractors for `number`, `email`, `phone`, `date`, and `boolean` types. The `string` type passes through as-is. The `custom` type can use sentence-transformers semantic matching (via `nlp.semantic_match()`).
