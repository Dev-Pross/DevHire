"use client"
import { useEffect, useRef, useState, MouseEvent, WheelEvent, KeyboardEvent, TouchEvent } from 'react'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'

const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY_MS = 2000;

export default function StreamViewer() {
    const router = useRouter()
    const [wsServerUrl, setWsServerUrl] = useState<string>('')
    const [streamToken, setStreamToken] = useState<string>('')

    const [status, setStatus] = useState<"connecting" | "connected" | "reconnecting" | "success" | "error" | "disconnected">("connecting");
    const [dimensions, setDimensions] = useState<{ width: number; height: number } | null>(null);
    const canvasRef = useRef<HTMLCanvasElement | null>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectAttemptsRef = useRef<number>(0);
    const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const isIntentionalCloseRef = useRef<boolean>(false);

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

    function connectWebSocket() {
        if (!dimensions || !wsServerUrl || !streamToken) return;

        const formattedUrl = wsServerUrl.replace(/^http:\/\//, 'ws://').replace(/^https:\/\//, 'wss://')
        const dpr = window.devicePixelRatio || 1;
        const ws = new WebSocket(`${formattedUrl}?token=${streamToken}&width=${dimensions.width}&height=${dimensions.height}&dpr=${dpr}`)
        wsRef.current = ws

        ws.onopen = () => {
            setStatus("connected")
            reconnectAttemptsRef.current = 0;
            canvasRef.current?.focus()
        }

        ws.onclose = () => {
            // If this was an intentional close (success), don't reconnect
            if (isIntentionalCloseRef.current) return;

            // Try to reconnect (user may have just switched apps for OTP)
            if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
                setStatus("reconnecting");
                reconnectAttemptsRef.current += 1;
                console.log(`WebSocket closed. Reconnect attempt ${reconnectAttemptsRef.current}/${MAX_RECONNECT_ATTEMPTS}...`);

                reconnectTimerRef.current = setTimeout(() => {
                    connectWebSocket();
                }, RECONNECT_DELAY_MS);
            } else {
                // Max attempts exhausted — session timed out
                setStatus("disconnected");
                toast.error("Session timed out. Please try again.");
                router.push("/Jobs/profile");
            }
        }

        ws.onerror = () => {
            // onerror is always followed by onclose, so let onclose handle reconnection
        }

        ws.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data.toString())

                if (msg.type === 'frame') {
                    const img = new Image()

                    img.onload = () => {
                        const canvas = canvasRef.current;
                        if (!canvas || !dimensions) return;

                        // Keep canvas buffer at the physical high-DPR image size.
                        // CSS max-w-full will visually scale it down to the logical screen size,
                        // giving us crystal-clear retina/high-DPI sharpness.
                        if (canvas.width !== img.width || canvas.height !== img.height) {
                            canvas.width = img.width;
                            canvas.height = img.height;
                        }

                        const ctx = canvas.getContext('2d')
                        if (ctx) {
                            ctx.drawImage(img, 0, 0, img.width, img.height)
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
                    isIntentionalCloseRef.current = true;
                    setStatus("success")
                    toast.success("LinkedIn Connected successfully!")
                    router.push('/')
                }
            }
            catch (error) {
                console.log(`Error parsing stream message ${error}`)
            }
        }
    }

    useEffect(() => {
        if (!dimensions || !wsServerUrl || !streamToken) return;

        connectWebSocket();

        return () => {
            // Clean up on unmount
            isIntentionalCloseRef.current = true;
            if (reconnectTimerRef.current) {
                clearTimeout(reconnectTimerRef.current);
            }
            wsRef.current?.close();
        }
    }, [streamToken, wsServerUrl, dimensions])

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

    const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
        if (wsRef.current?.readyState !== WebSocket.OPEN || !wsRef.current) {
            return;
        }

        // Only send control/navigation keys from onKeyDown.
        // Character keys are handled exclusively by handleInputChange
        // to prevent double-sending (canvas onKeyDown + input onKeyDown).
        const controlKeys = ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Tab', 'Enter', 'Backspace'];
        if (controlKeys.includes(e.key)) {
            e.preventDefault();
            wsRef.current.send(JSON.stringify({
                type: 'keyboard',
                key: e.key
            }));
        }
        // All printable characters flow through handleInputChange only
    };

    // Desktop-only: when canvas is focused (before any text field is clicked),
    // allow typing directly. Once a text field is focused, the hidden input
    // takes over and this stops firing.
    const handleCanvasKeyDown = (e: KeyboardEvent<HTMLCanvasElement>) => {
        // If the hidden input is focused, skip — it handles keys already
        if (document.activeElement === inputRef.current) return;

        if (wsRef.current?.readyState !== WebSocket.OPEN || !wsRef.current) return;
        e.preventDefault();
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
            if (totalDist > 20) {
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

        if (!hasMovedRef.current && duration < 500) {
            // Prevent the browser from synthesizing a compatibility `mousedown` / `click` event!
            // Without this, tapping on mobile fires both handleTouchEnd AND handleMouseDown,
            // sending TWO websocket messages to the backend, causing the infamous "double click".
            e.preventDefault();

            const { x, y } = scaleCalculationCoords(touchStartRef.current.x, touchStartRef.current.y);

            if (wsRef.current?.readyState === WebSocket.OPEN) {
                wsRef.current.send(JSON.stringify({
                    type: "mouse",
                    x: x,
                    y: y
                }));
            }
        }

        touchStartRef.current = null;
        lastTouchRef.current = null;
    };

    // Show reconnecting overlay
    if (status === 'reconnecting') {
        return (
            <div className="w-screen h-screen bg-[#F3F2EF] flex items-center justify-center">
                <div className="flex flex-col items-center gap-3">
                    <div className="w-8 h-8 rounded-full border-2 border-blue-500/30 border-t-blue-500 animate-spin" />
                    <p className="text-gray-600 text-sm font-medium">Reconnecting...</p>
                    <p className="text-gray-400 text-xs">Please wait while we restore your session</p>
                </div>
            </div>
        );
    }

    if (!dimensions || status === 'success' || status === 'error' || status === 'disconnected' || status === 'connecting') {
        return <div className="w-screen h-screen bg-[#F3F2EF]" />
    }

    return (
        <div className="w-screen h-screen flex items-center justify-center bg-white overflow-hidden select-none touch-none">
            {/* Hidden capture input for virtual keyboard */}
            <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                className="absolute opacity-0 pointer-events-none w-px h-px p-0 border-0 top-0 left-0 -z-10"
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
                onKeyDown={handleCanvasKeyDown}
                onTouchStart={handleTouchStart}
                onTouchMove={handleTouchMove}
                onTouchEnd={handleTouchEnd}
                tabIndex={0}
                className="max-w-full max-h-full object-contain cursor-default"
            />
        </div>
    );
}