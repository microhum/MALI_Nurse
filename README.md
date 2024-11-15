# Nurse LLM

```
/your_path/MALI_Nurse/
├── cli.py
├── main.py
├── README.md
├── llm/
│   ├── __init__.py
│   ├── client.py
│   └── llm.py
└── .env
```

## Quick Start

### Prerequisites

- Python 3.10

### Installation

1. Clone the repository:

   ```sh
   git clone https://github.com/yourusername/MALI_Nurse.git
   cd MALI_Nurse
   ```
2. Install the required packages:

   ```sh
   pip install -r requirements.txt
   ```

   Alternatively, you can use Poetry for dependency management:

    ```sh
    poetry install
    ```
3. Set up your environment variables in a `.env` file:

   ```env
   TYPHOON_API_KEY=your_typhoon_api_key
   ```

### Running the CLI

To start the CLI, run:

```sh
python cli.py
```

### Running the API

To start the FastAPI server, run:

```sh
uvicorn main:app --reload
```

The server will be available at `http://127.0.0.1:8000`.

### API Endpoints

- `GET /history`: Retrieve chat history
- `GET /ehr`: Retrieve EHR data
- `GET /status`: Get current prompt status
- `POST /debug`: Toggle debug mode
- `POST /reset`: Reset chat history and EHR data
- `POST /nurse_response`: Get a response from the nurse LLM

### Example Request

To get a response from the nurse LLM, send a POST request to `/nurse_response` with a JSON body:

```json
{
    "user_input": "Your question here"
}
```

### CLI Commands

The CLI provides several commands to interact with the Nurse LLM. Below are the available commands:

- `start`: Start the CLI session.
- `help`: Display help information about the CLI commands.
- `exit`: Exit the CLI session.

### Example Usage

To start the CLI session, simply run:

```sh
python cli.py
```

Once the CLI is running, you can use the following commands:

- To start interacting with the nurse LLM:

    ```sh
    start
    ```

- To display help information:

    ```sh
    help
    ```

- To exit the CLI session:

    ```sh
    exit
    ```
