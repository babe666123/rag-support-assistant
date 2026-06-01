import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

from rag import build_knowledge_base, retrieve_relevant_chunks


ROOT = Path(__file__).parent
ENV_FILE = ROOT / ".env"
KNOWLEDGE_BASE_DIR = ROOT / "knowledge_base"
API_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-chat"
HOST = "127.0.0.1"
PORT = 8787

SYSTEM_PROMPT = """你是企业 API 服务平台的技术支持助手。
请优先根据“参考资料”回答用户问题。
如果参考资料不足以回答，请明确说明资料中没有相关信息，并给出下一步排查建议。
回答要清晰、简洁、可执行。"""


class AppError(Exception):
    def __init__(self, code, message, status=500):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def error_payload(error):
    return {
        "code": error.code,
        "message": error.message,
    }


def load_env_file():
    if not ENV_FILE.exists():
        return

    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def build_augmented_messages(messages, sources):
    user_messages = [message for message in messages if message.get("role") == "user"]
    latest_question = user_messages[-1]["content"] if user_messages else ""
    context = "\n\n".join(
        f"[来源：{source['source']}]\n{source['text']}" for source in sources
    )
    if not context:
        context = "未检索到相关资料。"

    return [
        {
            "role": "system",
            "content": f"{SYSTEM_PROMPT}\n\n参考资料：\n{context}",
        },
        *messages[-8:],
        {
            "role": "user",
            "content": f"请基于参考资料回答这个问题：{latest_question}",
        },
    ]


def retrieve_sources_for_question(question, knowledge_chunks):
    return {
        "question": question,
        "sources": retrieve_relevant_chunks(question, knowledge_chunks, limit=3),
    }


def call_model(messages):
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise AppError(
            "MODEL_AUTH_MISSING",
            "没有找到 API Key。请在项目根目录创建 .env，并配置 DEEPSEEK_API_KEY。",
            400,
        )

    payload = {
        "model": os.getenv("DEEPSEEK_MODEL", DEFAULT_MODEL),
        "messages": messages,
        "temperature": 0.2,
    }
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raise AppError(
            "MODEL_HTTP_ERROR",
            f"模型接口返回 HTTP {error.code}。请检查 API Key、模型名称或账户额度。",
            502,
        ) from error
    except urllib.error.URLError as error:
        raise AppError(
            "MODEL_NETWORK_ERROR",
            f"无法连接模型服务：{error.reason}",
            502,
        ) from error

    return data["choices"][0]["message"]["content"]


def json_response(handler, status, data):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class ChatHandler(BaseHTTPRequestHandler):
    knowledge_chunks = []

    def do_GET(self):
        path = unquote(self.path.split("?", 1)[0])
        if path == "/":
            path = "/index.html"

        file_path = (ROOT / path.lstrip("/")).resolve()
        if not file_path.is_file() or ROOT.resolve() not in file_path.parents:
            self.send_error(404, "Not Found")
            return

        content_type = "text/plain; charset=utf-8"
        if file_path.suffix == ".html":
            content_type = "text/html; charset=utf-8"
        elif file_path.suffix == ".css":
            content_type = "text/css; charset=utf-8"
        elif file_path.suffix == ".js":
            content_type = "application/javascript; charset=utf-8"

        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path not in {"/api/chat", "/api/retrieve"}:
            json_response(self, 404, {"error": "接口不存在"})
            return

        length = int(self.headers.get("Content-Length", "0"))
        try:
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)
            if self.path == "/api/retrieve":
                question = data["question"]
                json_response(self, 200, retrieve_sources_for_question(question, self.knowledge_chunks))
                return

            messages = data["messages"]
            latest_question = messages[-1]["content"]
            sources = retrieve_sources_for_question(latest_question, self.knowledge_chunks)["sources"]
            answer = call_model(build_augmented_messages(messages, sources))
        except AppError as error:
            json_response(self, error.status, {"error": error_payload(error)})
            return
        except Exception:
            json_response(
                self,
                500,
                {"error": {"code": "INTERNAL_ERROR", "message": "服务处理失败，请查看后端日志。"}},
            )
            return

        json_response(self, 200, {"answer": answer, "sources": sources})

    def log_message(self, format, *args):
        return


def main():
    load_env_file()
    ChatHandler.knowledge_chunks = build_knowledge_base(KNOWLEDGE_BASE_DIR)
    server = ThreadingHTTPServer((HOST, PORT), ChatHandler)
    print("RAG 智能技术支持问答助手已启动")
    print(f"知识库片段数：{len(ChatHandler.knowledge_chunks)}")
    print(f"打开：http://{HOST}:{PORT}")
    print("按 Ctrl + C 停止服务")
    server.serve_forever()


if __name__ == "__main__":
    main()
