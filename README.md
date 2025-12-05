# Pricing Validator Agent

This project implements an intelligent agent using LangGraph to validate pricing strategies for gyms. It checks business rules (Ontology) against input data such as Customer Acquisition Cost (CAC), Minimum Price, and Per Capita Income (RPC). It includes a Python backend API and a React frontend for user interaction.

## Features

- **Ontological Validation**: Checks if the price covers costs (Rule 1) and is accessible based on local income (Rule 4).
- **Tactical Analysis**: Provides warnings if the price is too low for a premium brand positioning.
- **AI Feedback**: Integrates with Groq (LLM) to generate humanized, professional feedback for business owners.
- **Parallel Execution**: Validates independent rules concurrently using LangGraph.
- **Dynamic Rules**: Loads business rules from an external JSON file for flexibility.
- **Web Interface**: Modern React application to easily input data and view results.

## Tech Stack

- **Backend**: Python, LangGraph, FastAPI, Pydantic, LangChain (Groq).
- **Frontend**: React, TypeScript, Vite, CSS.

## Prerequisites

- Python 3.8+
- Node.js and npm
- Groq API Key (configured in the script)

## Installation

1. Clone the repository or navigate to the project directory.

2. Install Python dependencies:
   ```bash
   pip install langgraph pydantic fastapi uvicorn langchain-groq
   ```

3. Install Frontend dependencies:
   ```bash
   cd frontend
   npm install
   cd ..
   ```

## Usage

To run the full application, you need to start both the backend server and the frontend development server.

### 1. Start the Backend API

Open a terminal in the root directory and run:

```bash
python server.py
```

The API will start at `http://localhost:8000`.

### 2. Start the Frontend

Open a new terminal, navigate to the frontend directory, and start the server:

```bash
cd frontend
npm run dev
```

The web application will be available at `http://localhost:5173`.

### 3. Run the CLI Agent (Optional)

You can also run the agent directly via the command line without the web interface:

```bash
python agente.py --preco 150 --cac 100 --rpc 3800
```

## Project Structure

- **agente.py**: Core logic of the LangGraph agent, rule definitions, and execution flow.
- **server.py**: FastAPI server that exposes the agent logic as a REST endpoint.
- **regras.json**: Configuration file containing the business rules and thresholds.
- **frontend/**: Directory containing the React application source code.
