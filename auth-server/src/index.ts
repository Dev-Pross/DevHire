import http from "http";
import { URL } from "url";
import { WebSocketServer, WebSocket } from "ws";
import Redis from "ioredis";
import { handleBrowser } from "./browser";
import { config } from "dotenv";

config({ path: '../.env' })

const REDIS_URL = process.env.REDIS_URL;

if (!REDIS_URL) throw new Error("REDIS_URL is not defined");
const redis = new Redis(REDIS_URL)

const server = http.createServer((req, res) => {
    if (req.url === "/health") {
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ status: "ok" }));
        return;
    }
    if (req.url === "/") {
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ status: "stream server is running" }));
        return;
    }
    res.end(JSON.stringify({ status: "not found" }));
})

const wss = new WebSocketServer({ noServer: true })

server.on("upgrade", async (req, socket, head) => {
    try {
        const reqUrl = new URL(req.url || "", `http://${req.headers.host}`);
        const token = reqUrl.searchParams.get("token");
        const width = parseInt(reqUrl.searchParams.get("width") || "1366")
        const height = parseInt(reqUrl.searchParams.get("height") || "768")
        const dpr = parseFloat(reqUrl.searchParams.get("dpr") || "1")
        if (!token) {
            socket.write('HTTP/1.1 401 Unauthorized\r\n\r\n')
            socket.destroy()
            return;
        }

        const authUser = await redis.get(`stream_token:${token}`)

        if (!authUser) {
            socket.write('HTTP/1.1 401 Unauthorized\r\n\r\n')
            socket.destroy();
            return;
        }

        await redis.del(`stream_token:${token}`)

        wss.handleUpgrade(req, socket, head, (ws: WebSocket) => {
            wss.emit('connection', ws, req, authUser, width, height, dpr)
        })
    } catch (error) {
        console.error(error);
        socket.write('HTTP/1.1 500 Internal Server Error\r\n\r\n')
        socket.destroy()
    }
})

wss.on('connection', async (ws: WebSocket, _req: http.IncomingMessage, authUser: string, width: number, height: number, dpr: number) => {
    await handleBrowser(ws, authUser, width, height, dpr)
})

const PORT = process.env.PORT || 8080;

server.listen(Number(PORT), "0.0.0.0", () => {
    console.log(`Server is running on http://0.0.0.0:${PORT}`)
})