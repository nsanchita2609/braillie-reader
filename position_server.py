"""
Braill'ie - Position Server
============================
Run this FIRST before opening the GUI.

This file:
- Holds the current character position variable
- Simulates glove movement (auto-increments position)
- Broadcasts position to GUI via WebSocket

Install:
    pip install websockets

Run:
    python position_server.py
"""

import asyncio
import websockets
import json
import time

# ─────────────────────────────────────────
# GLOBAL STATE
# ─────────────────────────────────────────
state = {
    "position": 0,        # current character index (0 = start)
    "calibrated": False,  # has user calibrated?
    "running": False,     # is simulation running?
    "total_chars": 0,     # total chars in loaded text
}

connected_clients = set()

# ─────────────────────────────────────────
# BROADCAST to all connected GUIs
# ─────────────────────────────────────────
async def broadcast(message: dict):
    if connected_clients:
        msg = json.dumps(message)
        await asyncio.gather(*[ws.send(msg) for ws in connected_clients])

# ─────────────────────────────────────────
# HANDLE MESSAGES FROM GUI
# ─────────────────────────────────────────
async def handler(websocket):
    connected_clients.add(websocket)
    print(f"[SERVER] GUI connected. Total clients: {len(connected_clients)}")

    # Send current state immediately on connect
    await websocket.send(json.dumps({"type": "state", **state}))

    try:
        async for message in websocket:
            data = json.loads(message)
            cmd = data.get("cmd")

            if cmd == "calibrate":
                # User moved glove to top-left, reset origin
                state["position"] = 0
                state["calibrated"] = True
                print("[SERVER] Calibrated! Origin set to position 0.")
                await broadcast({"type": "calibrated", "position": 0})

            elif cmd == "set_total":
                # GUI tells server how many chars are in the PDF
                state["total_chars"] = data.get("total", 0)
                print(f"[SERVER] Total chars set to {state['total_chars']}")

            elif cmd == "start_sim":
                # Start simulating glove movement
                state["running"] = True
                print("[SERVER] Simulation started.")
                asyncio.create_task(simulate_movement())

            elif cmd == "stop_sim":
                state["running"] = False
                print("[SERVER] Simulation stopped.")

            elif cmd == "reset":
                state["position"] = 0
                state["running"] = False
                await broadcast({"type": "position", "position": 0})

            elif cmd == "set_position":
                # Manual override (for testing)
                state["position"] = data.get("position", 0)
                await broadcast({"type": "position", "position": state["position"]})

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.discard(websocket)
        print(f"[SERVER] GUI disconnected. Total clients: {len(connected_clients)}")

# ─────────────────────────────────────────
# SIMULATE GLOVE MOVEMENT
# Increments position like the glove is
# slowly moving across the page
# ─────────────────────────────────────────
async def simulate_movement():
    print("[SERVER] Simulating glove movement...")
    while state["running"]:
        if state["total_chars"] > 0 and state["position"] >= state["total_chars"] - 1:
            state["running"] = False
            await broadcast({"type": "done"})
            print("[SERVER] Reached end of text.")
            break

        state["position"] += 1
        await broadcast({"type": "position", "position": state["position"]})
        await asyncio.sleep(0.4)  # ~400ms per character (adjust to match actuator speed)

# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
async def main():
    print("=" * 45)
    print("  Braill'ie Position Server")
    print("  WebSocket running on ws://localhost:8765")
    print("  Waiting for GUI to connect...")
    print("=" * 45)
    async with websockets.serve(handler, "localhost", 8765):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
