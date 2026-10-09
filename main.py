
import hashlib
import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

app = FastAPI()

EMAIL = "23f1000365@ds.study.iitm.ac.in"
PROTOCOL_VERSION = "2025-03-26"


@app.get("/")
def home():
    return {"status": "MCP server is running"}


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    body = await request.json()

    method = body.get("method")
    request_id = body.get("id")

    # Handle MCP initialization
    if method == "initialize":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "live-challenge-server",
                    "version": "1.0.0"
                }
            }
        })

    # Notifications do not require a JSON-RPC response
    if method == "notifications/initialized":
        return Response(status_code=202)

    # Expose exactly one MCP tool
    if method == "tools/list":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": [{
                    "name": "solve_challenge",
                    "description": (
                        "Calculate the required SHA-256 challenge response."
                    ),
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }]
            }
        })

    # Execute the tool using the actual HTTP headers
    if method == "tools/call":
        params = body.get("params", {})

        if params.get("name") != "solve_challenge":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": "Unknown tool"
                }
            })

        challenge = request.headers.get("X-Exam-Challenge")

        if challenge is None:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": "Missing X-Exam-Challenge header"
                }
            })

        normalized_email = EMAIL.strip().lower()
        message = f"{challenge}:{normalized_email}"

        digest = hashlib.sha256(
            message.encode("utf-8")
        ).hexdigest()[:16]

        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [{
                    "type": "text",
                    "text": digest
                }]
            }
        })

    if request_id is None:
        return Response(status_code=202)

    return JSONResponse({
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": -32601,
            "message": "Method not found"
        }
    })

