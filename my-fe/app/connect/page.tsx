"use client"
import { useEffect, useRef, useState, MouseEvent, WheelEvent, KeyboardEvent, TouchEvent } from 'react'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'

export default function StreamViewer() {
    const router = useRouter()
    const [wsServerUrl, setWsServerUrl] = useState<string>('')
    const [streamToken, setStreamToken] = useState<string>('')

    const [status, setStatus] = useState<"connecting" | "connected" | "success" | "error" | "disconnected">("connecting");
    const [dimensions, setDimensions] = useState<{ width: number; height: number } | null>(null);
    const canvasRef = useRef<HTMLCanvasElement | null>(null);
    const wsRef = useRef<WebSocket | null>(null);

    // Mobile keyboard input capturing
    const inputRef = useRef<HTMLInputElement | null>(null);
    const [inputValue, setInputValue] = useState<string>(" ");

    // Touch gesture tracking
    const touchStartRef = useRef<{ x: number; y: number; time: number } | null>(null);
    const lastTouchRef = useRef<{ x: number; y: number } | null>(null);
    const hasMovedRef = useRef<boolean>(false);

    useEffect(() => {
        const width = window.innerWidth || 1366;
        const height = window.innerHeight || 768;
        setDimensions({ width, height });

        // Retrieve params client-side to prevent hydration mismatches
        const params = new URLSearchParams(window.location.search);
        const token = params.get('token') || 'postman_test_123';
        const rawStreamUrl = params.get('stream_url') || process.env.NEXT_PUBLIC_STREAM_SERVER || "http://localhost:8080";
        setStreamToken(token);
        setWsServerUrl(rawStreamUrl);
    }, [])

    useEffect(() => {
        if (!dimensions || !wsServerUrl) return;

        const formattedUrl = wsServerUrl.replace(/^http:\/\//, 'ws://').replace(/^https:\/\//, 'wss://')
        const dpr = window.devicePixelRatio || 1;
        const ws = new WebSocket(`${formattedUrl}?token=${streamToken}&width=${dimensions.width}&height=${dimensions.height}&dpr=${dpr}`)
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
                        const canvas = canvasRef.current;
                        if (!canvas) return;

                        if (canvas.width !== msg.width || canvas.height !== msg.height) {
                            canvas.width = msg.width;
                            canvas.height = msg.height;
                        }

                        const ctx = canvas.getContext('2d')
                        if (ctx) {
                            ctx.drawImage(img, 0, 0, msg.width, msg.height)
                        }
                    }

                    img.src = `data:image/jpeg;base64,${msg.data}`
                }
                else if (msg.type === 'focus_changed') {
                    if (msg.isInput) {
                        inputRef.current?.focus();
                    } else {
                        inputRef.current?.blur();
                    }
                }
                else if (msg.type === 'success') {
                    setStatus("success")
                    toast.success("LinkedIn Connected successfully!")
                    router.push('/')
                }
            }
            catch (error) {
                console.log(`Error parsing stream message ${error}`)
            }
        }
    }, [streamToken, wsServerUrl, dimensions, router])

    function scaleCalculationCoords(clientX: number, clientY: number) {
        const canvas = canvasRef.current;
        if (!canvas || !dimensions) return { x: 0, y: 0 };

        const rect = canvas.getBoundingClientRect();
        const scaleX = dimensions.width / rect.width;
        const scaleY = dimensions.height / rect.height;

        return {
            x: Math.round((clientX - rect.left) * scaleX),
            y: Math.round((clientY - rect.top) * scaleY),
        };
    }

    const handleMouseDown = (e: MouseEvent<HTMLCanvasElement>) => {
        if (wsRef.current?.readyState !== WebSocket.OPEN || !wsRef.current) {
            return;
        }
        const { x, y } = scaleCalculationCoords(e.clientX, e.clientY);
        wsRef.current.send(JSON.stringify({
            type: "mouse",
            x: x,
            y: y
        }));
        
        // Focus hidden input to prompt keyboard trigger on tap/click
        setTimeout(() => {
            inputRef.current?.focus();
        }, 30);
    };

    const handleWheel = (e: WheelEvent<HTMLCanvasElement>) => {
        if (wsRef.current?.readyState !== WebSocket.OPEN || !wsRef.current) {
            return;
        }
        e.preventDefault();
        wsRef.current.send(JSON.stringify({
            type: 'scroll',
            deltaX: e.deltaX,
            deltaY: e.deltaY
        }));
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLCanvasElement | HTMLInputElement>) => {
        if (wsRef.current?.readyState !== WebSocket.OPEN || !wsRef.current) {
            return;
        }

        // Prevent browser scrolling and default behaviors for keys we want to route to browser
        if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Tab', 'Enter', 'Backspace'].includes(e.key)) {
            e.preventDefault();
            wsRef.current.send(JSON.stringify({
                type: 'keyboard',
                key: e.key
            }));
            return;
        }

        if (e.key === ' ' && e.currentTarget.tagName === 'CANVAS') {
            e.preventDefault();
        }

        wsRef.current.send(JSON.stringify({
            type: 'keyboard',
            key: e.key
        }));
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const val = e.target.value;
        if (wsRef.current?.readyState !== WebSocket.OPEN || !wsRef.current) {
            return;
        }

        if (val === "") {
            // Backspace fallback
            wsRef.current.send(JSON.stringify({
                type: 'keyboard',
                key: 'Backspace'
            }));
            setInputValue(" ");
        } else if (val.length > 1) {
            // New character(s) typed or pasted
            const addedText = val.substring(1);
            for (let i = 0; i < addedText.length; i++) {
                wsRef.current.send(JSON.stringify({
                    type: 'keyboard',
                    key: addedText[i]
                }));
            }
            setInputValue(" ");
        }
    };

    const handleTouchStart = (e: TouchEvent<HTMLCanvasElement>) => {
        if (e.touches.length === 1) {
            const touch = e.touches[0];
            touchStartRef.current = {
                x: touch.clientX,
                y: touch.clientY,
                time: Date.now()
            };
            lastTouchRef.current = {
                x: touch.clientX,
                y: touch.clientY
            };
            hasMovedRef.current = false;
        }
    };

    const handleTouchMove = (e: TouchEvent<HTMLCanvasElement>) => {
        if (!lastTouchRef.current || e.touches.length !== 1) return;

        const touch = e.touches[0];
        const deltaX = lastTouchRef.current.x - touch.clientX;
        const deltaY = lastTouchRef.current.y - touch.clientY;

        const start = touchStartRef.current;
        if (start) {
            const totalDist = Math.sqrt(
                Math.pow(touch.clientX - start.x, 2) +
                Math.pow(touch.clientY - start.y, 2)
            );
            if (totalDist > 8) {
                hasMovedRef.current = true;
            }
        }

        if (wsRef.current?.readyState === WebSocket.OPEN && (Math.abs(deltaX) > 0.5 || Math.abs(deltaY) > 0.5)) {
            // Scale scrolling for natural responsiveness on mobile screens
            wsRef.current.send(JSON.stringify({
                type: 'scroll',
                deltaX: Math.round(deltaX * 1.5),
                deltaY: Math.round(deltaY * 1.5)
            }));
        }

        lastTouchRef.current = {
            x: touch.clientX,
            y: touch.clientY
        };
    };

    const handleTouchEnd = (e: TouchEvent<HTMLCanvasElement>) => {
        if (!touchStartRef.current) return;

        const duration = Date.now() - touchStartRef.current.time;

        if (!hasMovedRef.current && duration < 300) {
            const { x, y } = scaleCalculationCoords(touchStartRef.current.x, touchStartRef.current.y);

            if (wsRef.current?.readyState === WebSocket.OPEN) {
                wsRef.current.send(JSON.stringify({
                    type: "mouse",
                    x: x,
                    y: y
                }));
            }

            setTimeout(() => {
                inputRef.current?.focus();
            }, 30);
        }

        touchStartRef.current = null;
        lastTouchRef.current = null;
    };

    if (!dimensions || status === 'success' || status === 'error' || status === 'disconnected' || status === 'connecting') {
        return <div className="w-screen h-screen bg-[#F3F2EF]" />;
    }

    return (
        <div className="w-screen h-screen flex items-center justify-center bg-[#F3F2EF] overflow-hidden select-none touch-none">
            {/* Hidden capture input for virtual keyboard */}
            <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                className="absolute opacity-0 pointer-events-none w-px h-px p-0 border-0"
                style={{ top: '50%', left: '50%' }}
                autoComplete="off"
                autoCorrect="off"
                autoCapitalize="none"
                spellCheck="false"
            />

            {/* Canvas representing remote browser viewport */}
            <canvas
                ref={canvasRef}
                width={dimensions!.width}
                height={dimensions!.height}
                onMouseDown={handleMouseDown}
                onWheel={handleWheel}
                onKeyDown={handleKeyDown}
                onTouchStart={handleTouchStart}
                onTouchMove={handleTouchMove}
                onTouchEnd={handleTouchEnd}
                tabIndex={0}
                className="max-w-full max-h-full object-contain cursor-default"
            />
        </div>
    );
}