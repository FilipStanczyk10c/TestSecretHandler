# Secret Test

Handler-based AIConsole package. Your code has full control: when a user sends a message, it goes to your handler and your logic runs directly.

## Structure

- `src/secret_test/handlers/` – main handler with `handle_user_request(message, attached_assets)`
- No `tools/` – this project is handler-based only

## Setup

```bash
uv venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
uv pip install -r requirements.txt
uv pip install -e .
```

## Local development

```bash
aic-dev --url http://localhost:8000
```

Then pair with AIConsole via Developer Mode and the pairing code shown in the terminal.

## Deploy

Push to Git, add as Git Package API in AIConsole, set **Handling Strategy** to use this package, then Build Image.
