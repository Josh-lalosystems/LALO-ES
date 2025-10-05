"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

# © 2025 LALO AI, LLC. All Rights Reserved
# SPDX-License-Identifier: All-Rights-Reserved

"""
Module: MCPPacket Handler

Purpose:
 - Defines the MCP packet structure for agent-tool messaging
 - Dynamically selects transport mechanism (Redis Stream vs gRPC) based on payload size
 - Handles retries, fallback transport, fragmentation, protocol versioning, and deduplication
 - Aligned with emerging MCP standards (Model Context Protocol) and high-performance RPC practices

Dependencies:
 - redis.Redis client (for Redis Streams)
 - gRPC client stub (Protocol Buffers based RPC)
 - protobuf-defined `McpMessage` types
 - Configurable size threshold
 - Fallback logic for transport failures

Edge Case Handling:
 - Detect and handle Redis or gRPC transport failure
 - Automatically retry via alternate transport
 - Fragment large messages > MAX_PAYLOAD into sequenced chunks
 - Maintain `protocol_version` for evolving formats
 - Enforce unique `packet_id` to support deduplication
 - Optionally add `transport_hint` for priority requirements
"""

import uuid
import json

from .config import settings
import redis
import grpc

# Hypothetical protobuf generated classes
from .proto.mcp_pb2 import McpMessage, McpFragment
from .proto.mcp_pb2_grpc import McpServiceStub

class MCPPacketError(Exception):
    pass

class MCPPacket:
    def __init__(self, agent_id: str, step_id: str, tool: str, payload: dict,
                 memory_pointer: str, protocol_version: str = "1.0", transport_hint: str = None):
        self.packet_id = str(uuid.uuid4())
        self.agent_id = agent_id
        self.step_id = step_id
        self.tool = tool
        self.payload = payload
        self.memory_pointer = memory_pointer
        self.protocol_version = protocol_version
        self.transport_hint = transport_hint
        self.transport = None

        # Initialize Redis and gRPC clients
        self.redis = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT,
                                 decode_responses=False)
        channel = grpc.insecure_channel(settings.GRPC_ENDPOINT)
        self.grpc_client = McpServiceStub(channel)

    def to_json(self):
        return json.dumps({
            "packet_id": self.packet_id,
            "agent_id": self.agent_id,
            "step_id": self.step_id,
            "tool": self.tool,
            "payload": self.payload,
            "memory_pointer": self.memory_pointer,
            "protocol_version": self.protocol_version,
            "transport_hint": self.transport_hint
        })

    def choose_transport(self):
        size = len(self.to_json().encode('utf-8'))
        threshold = settings.PAYLOAD_SIZE_THRESHOLD
        # honor hint if provided
        if self.transport_hint:
            self.transport = self.transport_hint
        else:
            self.transport = "redis_stream" if size <= threshold else "grpc"
        return self.transport

    def send(self):
        t = self.choose_transport()
        if t == "redis_stream":
            return self._send_redis()
        elif t == "grpc":
            return self._send_grpc()
        else:
            raise MCPPacketError(f"Unknown transport: {t}")

    def _send_redis(self):
        msg = self.to_json()
        try:
            self.redis.xadd("mcp_stream", {"message": msg})
            return True
        except Exception as e:
            # fallback to gRPC if Redis fails
            return self._fallback("grpc", e)

    def _send_grpc(self):
        try:
            content = McpMessage(packet_json=self.to_json())
            response = self.grpc_client.SendPacket(content)
            return response.success
        except Exception as e:
            # fallback to Redis if gRPC fails
            return self._fallback("redis_stream", e)

    def _fallback(self, fallback_transport: str, original_error: Exception):
        self.transport = fallback_transport
        try:
            if fallback_transport == "redis_stream":
                self.redis.xadd("mcp_stream", {"message": self.to_json()})
            else:
                content = McpMessage(packet_json=self.to_json())
                self.grpc_client.SendPacket(content)
            return True
        except Exception as e2:
            raise MCPPacketError(
                f"Both {self.transport} and fallback {fallback_transport} failed: {e2}"
            )

    def fragment_payload(self, max_size: int = settings.MAX_FRAGMENT_SIZE):
        """
        Split large payload into fragments for streaming.
        Returns a list of McpFragment messages ready for gRPC streaming.
        """
        raw = self.to_json().encode('utf-8')
        fragments = []
        for i in range(0, len(raw), max_size):
            chunk = raw[i:i + max_size]
            frag = McpFragment(
                packet_id=self.packet_id,
                fragment_index=i // max_size,
                total_fragments=(len(raw) + max_size - 1) // max_size,
                data=chunk
            )
            fragments.append(frag)
        return fragments
