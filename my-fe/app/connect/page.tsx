"use client"
import { useEffect, useRef, useState, MouseEvent, WheelEvent, KeyboardEvent } from 'react'


export default function StreamViewer() {
    const wsServerUrl = process.env.NEXT_PUBLIC_STREAM_SERVER || "http://localhost:8080"
    const streamToken = 'postman_test_123'

    const [status, setStatus] = useState<"connecting" | "connected" | "success" | "error" | "disconnected">("connecting");
    const [dimensions, setDimensions] = useState<{ width: number; height: number } | null>(null);
    const canvasRef = useRef<HTMLCanvasElement | null>(null);
    const wsRef = useRef<WebSocket | null>(null);

    useEffect(() => {
        const width = window.innerWidth || 1366;
        const height = window.innerHeight || 768;
        setDimensions({ width, height });
    }, [])

    useEffect(() => {
        if (!dimensions) return;

        // Convert http/https to ws/wss protocols dynamically to prevent browser connection failures
        const formattedUrl = wsServerUrl.replace(/^http:\/\//, 'ws://').replace(/^https:\/\//, 'wss://')
        const ws = new WebSocket(`${formattedUrl}?token=${streamToken}&width=${dimensions.width}&height=${dimensions.height}`)
        wsRef.current = ws

        ws.onopen = () => {
            setStatus("connected")
            canvasRef.current?.focus()
        }

        ws.onclose = () => {
            setStatus("disconnected")
        }

        ws.onerror = () => {
            setStatus("error")
        }

        ws.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data.toString())

                if (msg.type === 'frame') {
                    const img = new Image()

                    img.onload = () => {
                        const ctx = canvasRef.current?.getContext('2d')
                        if (ctx) {
                            ctx.drawImage(img, 0, 0, msg.width, msg.height)
                        }
                    }

                    img.src = `data:image/jpeg;base64,${msg.data}`
                }
                else if (msg.type === 'success') {
                    setStatus("success")
                    window.location.href = '/'
                }
            }
            catch (error) {
                console.log(`Error parsing stream message ${error}`)
            }
        }
    }, [streamToken, wsServerUrl, dimensions])

    function scaleCalculation(e: MouseEvent<HTMLCanvasElement> | WheelEvent<HTMLCanvasElement>) {
        const canvas = canvasRef.current;

        if (!canvas) return { x: 0, y: 0 };

        const rect = canvas.getBoundingClientRect()
        const scaleX = dimensions!.width / rect.width;
        const scaleY = dimensions!.height / rect.height;

        return {
            x: Math.round((e.clientX - rect.left) * scaleX),
            y: Math.round((e.clientY - rect.top) * scaleY),
        }
    }

    const handleMouseDown = (e: MouseEvent<HTMLCanvasElement>) => {
        if (wsRef.current?.readyState !== WebSocket.OPEN || !wsRef.current) {
            return
        }
        const { x, y } = scaleCalculation(e);
        wsRef.current.send(JSON.stringify({
            type: "mouse",
            x: x,
            y: y
        }))
    }

    const handleWheel = (e: WheelEvent<HTMLCanvasElement>) => {
        if (wsRef.current?.readyState !== WebSocket.OPEN || !wsRef.current) {
            return
        }
        e.preventDefault()
        wsRef.current.send(JSON.stringify({
            type: 'scroll',
            deltaX: e.deltaX,
            deltaY: e.deltaY
        }));
    }

    const handleKeyDown = (e: KeyboardEvent<HTMLCanvasElement>) => {
        if (wsRef.current?.readyState !== WebSocket.OPEN || !wsRef.current) {
            return
        }
        if ([' ', 'ArrowUp', 'ArrowDown', 'Enter', 'Tab'].includes(e.key)) {
            e.preventDefault();
        }

        wsRef.current.send(JSON.stringify({
            type: 'keyboard',
            key: e.key
        }))
    }

    if (!dimensions || status === 'success' || status === 'error' || status === 'disconnected' || status === 'connecting') {
        return <div className="w-screen h-screen bg-[#F3F2EF]" />;
    }

    return (
        <canvas
            ref={canvasRef}
            width={dimensions!.width}
            height={dimensions!.height}
            onMouseDown={handleMouseDown}
            onWheel={handleWheel}
            onKeyDown={handleKeyDown}
            tabIndex={0}
            className="max-w-full max-h-full object-contain cursor-default"
        />
    );
}