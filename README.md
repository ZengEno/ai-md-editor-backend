# AI MD Editor (Backend)

## Description

AI MD Editor (Backend) is the backend component of AI MD Editor, an AI agent-based application. This project serves as a practice project for building applications that leverage AI capabilities. The backend is designed to work in conjunction with a frontend service.

## Installation Instructions

To get started with the AI MD Editor backend, follow these steps:

1. Clone the repository:

    ```bash
    git clone https://github.com/ZengEno/ai-md-editor-backend.git
    cd ai-md-editor-backend
    ```

2. This project uses poetry to manage dependencies. If you don't have poetry, you should install it first.

(optional) Before installing the dependencies, it is recommended to set the Poetry configuration `virtualenvs.in-project = true`, so that the virtual environment will be created within the project directory. You can run `poetry config virtualenvs.in-project true` to set this configuration.

Run the following command to install the dependencies:

    ```bash
    poetry install
    ```

This command will install the dependencies and create a virtual environment for the project. 

3. Set up the environment variables according to the `.env.example` file (create a `.env` file in the root directory):

    ```bash
    # Example environment variables
    JWT_SECRET_KEY=Your_JWT_SECRET_KEY
    DASHSCOPE_API_KEY=Your_DASHSCOPE_API_KEY
    LANGCHAIN_API_KEY=Your_LANGCHAIN_API_KEY
    ```

4. You can directly run `main.py` to start the FastAPI server, or use this command: 

    ```bash
    python main.py
    ```

This will start the FastAPI server, and you can access the API documentation by navigating to http://localhost:8080/docs in your browser.

**Note**: Ensure that the frontend service is running simultaneously to use this backend service effectively.

## Usage

To use the backend service, you should start the frontend service and open the editor in the browser.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact Information

For any questions or support, feel free to reach out to me at zeng_eno@qq.com.