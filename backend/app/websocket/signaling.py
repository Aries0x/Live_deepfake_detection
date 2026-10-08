"""
WebRTC Signaling WebSocket Router — Multi-Peer Mesh Support.
Routes SDP offers, answers, and ICE candidates between participants.
Supports targeted (peer-to-peer) and broadcast messaging for N-way calls.
"""
import uuid
from typing import Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from starlette.websockets import WebSocketState
from backend.app.logging_config import get_logger

logger = get_logger("webrtc_signaling")
router = APIRouter()

# Mapping: room_id -> {peer_id: WebSocket}
rooms: Dict[str, Dict[str, WebSocket]] = {}


def get_active_room_peers(room_id: str) -> Dict[str, WebSocket]:
    """Prunes closed or stale WebSockets and returns only actively connected peers."""
    if room_id not in rooms:
        return {}
    active: Dict[str, WebSocket] = {}
    for pid, ws in list(rooms[room_id].items()):
        try:
            if ws.client_state == WebSocketState.CONNECTED:
                active[pid] = ws
        except Exception:
            pass
    rooms[room_id] = active
    if not active:
        rooms.pop(room_id, None)
    return active


@router.websocket("/ws/signaling/{room_id}")
async def webrtc_signaling(
    websocket: WebSocket,
    room_id: str,
    client_id: str = Query(default=None),
):
    await websocket.accept()

    # Clean up stale connections
    get_active_room_peers(room_id)
    if room_id not in rooms:
        rooms[room_id] = {}

    # Assign or reuse client identifier
    peer_id = client_id if client_id else f"peer-{uuid.uuid4().hex[:6]}"

    # If reconnecting, close old socket
    if peer_id in rooms[room_id]:
        old_ws = rooms[room_id][peer_id]
        if old_ws != websocket:
            try:
                await old_ws.close()
            except Exception:
                pass

    rooms[room_id][peer_id] = websocket
    active_peers = get_active_room_peers(room_id)
    peer_count = len(active_peers)

    # List of peers already in the room (excluding self)
    existing_peer_ids = [pid for pid in active_peers.keys() if pid != peer_id]

    logger.info(
        "Peer joined signaling room",
        room_id=room_id,
        peer_id=peer_id,
        peer_count=peer_count,
        existing_peers=existing_peer_ids,
    )

    # 1. Send assignment with list of existing peers (new peer creates offers to each)
    try:
        await websocket.send_json({
            "type": "assigned",
            "peer_id": peer_id,
            "room_id": room_id,
            "peer_count": peer_count,
            "existing_peers": existing_peer_ids,
        })
    except Exception as e:
        logger.warning("Failed to send assigned ack", peer_id=peer_id, error=str(e))

    # 2. Notify existing peers about the newcomer
    for other_pid, other_ws in list(active_peers.items()):
        if other_pid != peer_id:
            try:
                await other_ws.send_json({
                    "type": "peer_joined",
                    "joined_peer": peer_id,
                    "peer_count": peer_count,
                })
            except Exception:
                pass

    # 3. Message forwarding loop with targeted routing support
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "unknown")
            target_peer = data.get("target_peer")

            # Stamp sender so receivers know who sent it
            payload = dict(data)
            payload["sender_peer"] = peer_id

            current_peers = get_active_room_peers(room_id)

            if target_peer:
                # Targeted: route only to the specified peer
                target_ws = current_peers.get(target_peer)
                if target_ws:
                    try:
                        await target_ws.send_json(payload)
                    except Exception as e:
                        logger.warning(
                            "Failed targeted signaling forward",
                            msg_type=msg_type,
                            from_peer=peer_id,
                            to_peer=target_peer,
                            error=str(e),
                        )
                else:
                    logger.warning(
                        "Target peer not found in room",
                        target_peer=target_peer,
                        room_id=room_id,
                    )
            else:
                # Broadcast to all other peers in the room
                for other_pid, other_ws in list(current_peers.items()):
                    if other_pid != peer_id:
                        try:
                            await other_ws.send_json(payload)
                        except Exception as e:
                            logger.warning(
                                "Failed broadcast signaling",
                                msg_type=msg_type,
                                from_peer=peer_id,
                                to_peer=other_pid,
                                error=str(e),
                            )

    except (WebSocketDisconnect, RuntimeError):
        logger.info("Peer disconnected normally", room_id=room_id, peer_id=peer_id)
    except Exception as e:
        logger.warning("Signaling loop exception", room_id=room_id, peer_id=peer_id, error=str(e))
    finally:
        # Remove this peer
        if room_id in rooms and peer_id in rooms[room_id]:
            rooms[room_id].pop(peer_id, None)

        remaining_peers = get_active_room_peers(room_id)
        logger.info(
            "Room peer departure",
            room_id=room_id,
            peer_id=peer_id,
            remaining=len(remaining_peers),
        )

        # Notify remaining peers that this participant left
        for other_pid, other_ws in list(remaining_peers.items()):
            try:
                await other_ws.send_json({
                    "type": "peer_left",
                    "departed_peer": peer_id,
                    "peer_count": len(remaining_peers),
                })
            except Exception:
                pass
