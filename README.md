# Perplexity-Clone-LangGraph

## Installation

Install the LangChain CLI if you haven't yet

```bash
pip install -U langchain-cli
```

## Adding packages

```bash
# adding packages from 
# https://github.com/langchain-ai/langchain/tree/master/templates
langchain app add $PROJECT_NAME

# adding custom GitHub repo packages
langchain app add --repo $OWNER/$REPO
# or with whole git string (supports other git providers):
# langchain app add git+https://github.com/hwchase17/chain-of-verification

# with a custom api mount point (defaults to `/{package_name}`)
langchain app add $PROJECT_NAME --api_path=/my/custom/path/rag
```

Note: you remove packages by their api path

```bash
langchain app remove my/custom/path/rag
```

## Setup LangSmith (Optional)
LangSmith will help us trace, monitor and debug LangChain applications. 
You can sign up for LangSmith [here](https://smith.langchain.com/). 
If you don't have access, you can skip this section

```shell
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=<your-api-key>
export LANGCHAIN_PROJECT=<your-project>  # if not specified, defaults to "default"
```

## Launch LangServe

```bash
langchain serve
```

## Running in Docker

This project folder includes a Dockerfile that allows you to easily build and host your LangServe app.

### Building the Image

To build the image, you simply:

```shell
docker build . -t my-langserve-app
```

If you tag your image with something other than `my-langserve-app`,
note it for use in the next step.

### Running the Image Locally

To run the image, you'll need to include any environment variables
necessary for your application.

In the below example, we inject the `OPENAI_API_KEY` environment
variable with the value set in my local environment
(`$OPENAI_API_KEY`)

We also expose port 8080 with the `-p 8080:8080` option.

```shell
docker run -e OPENAI_API_KEY=$OPENAI_API_KEY -p 8080:8080 my-langserve-app
```

## Project Structure

The project is structured as follows:

- `app/`: Contains the main application code.
  - `server.py`: The main server file that sets up the FastAPI application.
  - `router.py`: Contains the API routes and WebSocket handling.
  - `db_setup.py`: Sets up the database connection and checkpointer.
- `packages/`: Contains utility functions and modules.
  - `search_utils/`: Contains search-related utilities.
    - `duckduckgo_utils.py`: Utilities for DuckDuckGo search.
    - `search_prompts.py`: Contains prompt templates for search queries.
    - `search_graph.py`: Defines the state graph for the search process.
    - `search_agent_nodes.py`: Contains the nodes for the search agent.
- `Dockerfile`: Dockerfile to build the application image.
- `pyproject.toml`: Project dependencies and configuration.
- `.gitignore`: Specifies files and directories to be ignored by git.

## Usage

### Running the Application

To run the application locally, use the following command:

```shell

uvicorn app.server:app --host 0.0.0.0 --port 8000
```

### API Endpoints

- `GET /`: Redirects to the API documentation.
- `POST /getresponse`: Retrieves the response for a given thread ID.
- `POST /getcheckpoint`: Retrieves the checkpoint for a given thread ID.
- `POST /listcheckpoints`: Lists all checkpoints for a given thread ID.
- `POST /search`: Custom search endpoint using the defined state graph.
- `WS /ws/search`: WebSocket endpoint for real-time search queries.

### Environment Variables

Ensure you have the following environment variables set:

- `DATABASE_URL`: The URL for the PostgreSQL database.
- `OPENAI_API_KEY`: API key for OpenAI.
- `MISTRAL_API_KEY`: API key for Mistral AI.

### Example Usage

To perform a search query, you can use the `/search` endpoint:

```bash
curl -X POST "http://localhost:8000/search" -H "Content-Type: application/json" -d '{"query": "What is the capital of France?", "thread_id": "12345"}'
```

This will return the search results processed by the state graph.

## Contributing

Feel free to open issues or submit pull requests for any improvements or bug fixes.

## License

This project is licensed under the MIT License.
