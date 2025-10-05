# LALO Router-Based Architecture

## Executive Summary

LALO uses a **hierarchical routing system** where intelligent router models direct requests through the optimal path - from simple direct responses to complex multi-model workflows.

## Hardware Assumptions

### Development (Current)
- **Your machine**: 8GB RAM, CPU-only
- **Upcoming**: RTX 4090 or better
- **Access**: High-end workstations via Intel/NVIDIA connections

### Client Deployments
- **Minimum**: DGX Spark (128GB unified memory, GB10)
- **Standard**: 2-8x GH200 GPUs
- **Inference**: Power/latency NOT a constraint
- **Focus**: Accuracy, capability, and orchestration

## New Architecture Overview

```
User Request
    ↓
┌─────────────────────────────────────┐
│  ROUTER MODEL (Liquid-1.2B-Tool)   │  ← First touch point
│  - Classifies request complexity    │
│  - Determines execution path         │
│  - Estimates confidence              │
└─────────────────────────────────────┘
    ↓
    ├─ SIMPLE PATH (60% of requests)
    │   └→ Direct LLM Response (Qwen/Mistral 7B)
    │       └→ Return to user ✓
    │
    └─ COMPLEX PATH (40% of requests)
        └→ AGENT ORCHESTRATOR
            ↓
        ┌──────────────────────────────────┐
        │  Workflow Planner                 │
        │  - Maps multi-step execution      │
        │  - Selects specialized models     │
        │  - Coordinates tools/MCPs         │
        └──────────────────────────────────┘
            ↓
        ┌──────────────────────────────────┐
        │  Execution Layer                  │
        │  ├─ LLMs (DeepSeek, Hermes)      │
        │  ├─ LFMs (Liquid specialized)     │
        │  ├─ HRM (reasoning)               │
        │  ├─ Tools (file, DB, web)         │
        │  └─ MCPs (browser, APIs)          │
        └──────────────────────────────────┘
            ↓
        ┌──────────────────────────────────┐
        │  Confidence Model                 │
        │  - Validates outputs              │
        │  - Triggers re-execution if low   │
        │  - Aggregates multi-model results │
        └──────────────────────────────────┘
            ↓
        Final Response to User ✓
```

## Core Components

### 1. Router Model (Entry Point)

**Model**: Liquid-1.2B-Tool (fast, lightweight, specialized)

**Responsibilities:**
- Classify request complexity (0-1 scale)
- Determine execution path (simple vs complex)
- Initial confidence estimation
- Route to appropriate handler

**Decision Tree:**
```python
if complexity < 0.3 and confidence > 0.8:
    → Direct LLM (simple Q&A)
elif complexity < 0.5 and no_tools_needed:
    → Single specialized LFM
elif requires_reasoning:
    → HRM + validation LLM
else:
    → Full Agent Orchestrator
```

**Size**: 1.2B params (700MB RAM, fast on CPU)
**Speed**: Critical (first touch, must be <1s)
**Accuracy**: High (wrong routing = bad UX)

### 2. Agent Orchestrator (Complex Path)

**Model**: Liquid-1.2B-Tool or DeepSeek-7B

**Responsibilities:**
- Multi-step workflow planning
- Model selection for each step
- Tool/MCP coordination
- Parallel execution management
- Result aggregation

**Example Execution Plan:**
```json
{
  "request": "Research competitors and create comparison chart",
  "plan": [
    {
      "step": 1,
      "action": "web_search",
      "model": "liquid-tool",
      "params": {"query": "top 5 competitors in AI space"},
      "parallel": false
    },
    {
      "step": 2,
      "action": "extract_data",
      "model": "liquid-extract",
      "params": {"urls": ["..."]},
      "parallel": true
    },
    {
      "step": 3,
      "action": "analyze",
      "model": "deepseek-v3",
      "params": {"data": "{results}"},
      "parallel": false
    },
    {
      "step": 4,
      "action": "generate_chart",
      "model": "code-executor",
      "params": {"format": "matplotlib"},
      "parallel": false
    }
  ],
  "confidence_checks": [2, 3, 4]
}
```

### 3. Confidence Model (Validation Layer)

**Model**: Lightweight LLM (Qwen-0.5B or Liquid-Extract)

**Responsibilities:**
- Score output quality (0-1)
- Detect hallucinations
- Validate multi-model consistency
- Trigger re-execution if needed

**Confidence Scoring:**
```python
def score_confidence(output, context, sources):
    scores = {
        'factual': check_facts(output, sources),      # 0-1
        'consistent': check_consistency(output),       # 0-1
        'complete': check_completeness(output),        # 0-1
        'grounded': check_grounding(output, context)   # 0-1
    }

    weighted_score = (
        scores['factual'] * 0.4 +
        scores['consistent'] * 0.3 +
        scores['complete'] * 0.2 +
        scores['grounded'] * 0.1
    )

    return weighted_score

# If score < 0.7: re-execute with different model or parameters
```

### 4. Specialized Model Pool

#### General Purpose LLMs
- **DeepSeek-V3-7B**: Complex reasoning, coding
- **Mistral-7B**: General chat, summaries
- **Qwen2.5-7B**: Fast responses, Chinese support

#### Liquid Foundation Models (LFMs)
- **Liquid-1.2B-Tool**: Function calling, routing
- **Liquid-350M-Extract**: Data extraction
- **Liquid-1.2B-RAG**: Document retrieval
- **Liquid-1.2B-Math**: Mathematical reasoning

#### Specialized Models
- **HRM-27M**: Complex logical reasoning, puzzles
- **Hermes-4-70B**: Advanced tool use (high-end deployments)
- **Code-Llama-7B**: Code generation/debugging

## Implementation Architecture

### Phase 1: Router Model (Week 1-2)

```python
# File: core/services/router_model.py

from llama_cpp import Llama
from typing import Dict, Literal
import asyncio

class RouterModel:
    """
    First-touch router that classifies requests and determines execution path

    Replaces old "semantic model" with intelligent routing
    """

    def __init__(self):
        # Load Liquid Tool (optimized for classification/routing)
        self.model = Llama(
            model_path="./models/liquid-tool-1.2b-q4.gguf",
            n_ctx=2048,
            n_threads=4,
            verbose=False
        )

    async def route(self, user_request: str, context: Dict = None) -> Dict:
        """
        Analyze request and determine optimal execution path

        Returns:
        {
            "path": "simple" | "complex" | "specialized",
            "complexity": 0.0-1.0,
            "confidence": 0.0-1.0,
            "reasoning": str,
            "recommended_models": [str],
            "requires_tools": bool,
            "requires_workflow": bool
        }
        """

        # Construct routing prompt
        prompt = f"""<|system|>
You are a router model. Analyze the user request and determine the optimal execution path.

Classify:
1. Complexity (0-1): How complex is this request?
   - 0.0-0.3: Simple factual question, direct answer
   - 0.3-0.6: Moderate, may need tool or specialized model
   - 0.6-1.0: Complex, multi-step reasoning/workflow needed

2. Confidence (0-1): How confident are you about handling this?
   - <0.7: Need specialized model or validation
   - 0.7-0.9: Can handle with standard LLM
   - >0.9: Simple, direct answer

3. Path: simple | complex | specialized
4. Required tools/models

Respond in JSON format.
<|user|>
Request: {user_request}
Context: {context or "None"}
<|assistant|>
"""

        # Get routing decision
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.model(
                prompt,
                max_tokens=256,
                temperature=0.3,  # Low temp for consistent routing
                stop=["<|user|>"]
            )
        )

        # Parse JSON response
        import json
        try:
            decision = json.loads(result['choices'][0]['text'])
        except:
            # Fallback to complex path if parsing fails
            decision = {
                "path": "complex",
                "complexity": 0.5,
                "confidence": 0.5,
                "reasoning": "Failed to parse routing decision",
                "recommended_models": ["deepseek-7b"],
                "requires_tools": False,
                "requires_workflow": True
            }

        return decision

    async def estimate_complexity(self, request: str) -> float:
        """Quick complexity estimation (faster than full routing)"""

        # Simple heuristics + model confirmation
        indicators = {
            'simple': ['what is', 'define', 'who is', 'when did'],
            'medium': ['how to', 'compare', 'explain', 'summarize'],
            'complex': ['design', 'analyze', 'research', 'create plan']
        }

        request_lower = request.lower()

        # Quick heuristic check
        if any(kw in request_lower for kw in indicators['simple']):
            base_score = 0.2
        elif any(kw in request_lower for kw in indicators['complex']):
            base_score = 0.8
        else:
            base_score = 0.5

        # Adjust based on length (longer = more complex)
        length_factor = min(len(request.split()) / 50, 0.3)

        return min(base_score + length_factor, 1.0)


# Global instance
router_model = RouterModel()
```

### Phase 2: Agent Orchestrator (Week 3-4)

```python
# File: core/services/agent_orchestrator.py

from typing import List, Dict, Any
from core.services.router_model import router_model
from core.tools.registry import tool_registry
import asyncio

class AgentOrchestrator:
    """
    Coordinates multi-model, multi-tool workflows

    Replaces old workflow coordinator with intelligent orchestration
    """

    def __init__(self):
        self.planner_model = None  # Liquid-Tool or DeepSeek
        self.available_models = {}
        self.available_tools = {}

    async def plan_execution(self, request: str, routing_decision: Dict) -> Dict:
        """
        Create execution plan for complex requests

        Returns workflow DAG (Directed Acyclic Graph)
        """

        prompt = f"""<|system|>
You are an execution planner. Create a step-by-step plan to fulfill the request.

Available Models:
- deepseek-v3: Complex reasoning, coding
- liquid-tool: Function calling, APIs
- liquid-extract: Data extraction
- liquid-math: Mathematical reasoning
- hrm: Logical puzzles, proofs
- mistral-7b: General purpose

Available Tools:
- web_search: Search internet
- file_read/write: File operations
- code_execute: Run Python code
- database_query: SQL queries
- chrome_control: Browser automation
- api_call: External APIs

Create a JSON execution plan with steps.
<|user|>
Request: {request}
Routing Info: {routing_decision}
<|assistant|>
"""

        # Get execution plan from planner
        plan = await self.planner_model.generate(prompt, max_tokens=512)

        import json
        try:
            execution_plan = json.loads(plan)
        except:
            # Fallback: simple single-step plan
            execution_plan = {
                "steps": [
                    {
                        "id": 1,
                        "action": "generate",
                        "model": "deepseek-v3",
                        "params": {"prompt": request}
                    }
                ]
            }

        return execution_plan

    async def execute_plan(self, plan: Dict, user_id: str) -> Dict:
        """
        Execute the planned workflow

        Handles:
        - Sequential execution
        - Parallel execution
        - Error handling and retries
        - Confidence checking at key steps
        """

        results = {}

        for step in plan['steps']:
            step_id = step['id']
            action = step['action']

            # Check if this step can run in parallel
            parallel = step.get('parallel', False)

            if action == 'tool_call':
                # Execute tool
                tool_name = step['tool']
                params = step['params']
                result = await tool_registry.execute_tool(tool_name, **params)

            elif action == 'model_generate':
                # Call specific model
                model_name = step['model']
                prompt = step['prompt']
                result = await self._call_model(model_name, prompt)

            elif action == 'confidence_check':
                # Validate previous step
                target_step = step['validates']
                result = await self._check_confidence(
                    results[target_step],
                    step.get('threshold', 0.7)
                )

                # Re-execute if confidence too low
                if result['confidence'] < step.get('threshold', 0.7):
                    # Retry with different model/parameters
                    retry_step = step.get('retry_with')
                    if retry_step:
                        result = await self._call_model(
                            retry_step['model'],
                            retry_step['prompt']
                        )

            results[step_id] = result

            # Yield intermediate results for streaming
            yield {
                "step": step_id,
                "status": "complete",
                "result": result
            }

        # Aggregate final result
        final_result = self._aggregate_results(results, plan)
        yield {
            "step": "final",
            "status": "complete",
            "result": final_result
        }

    async def _call_model(self, model_name: str, prompt: str) -> Any:
        """Call a specific model from the pool"""
        # Implementation for calling different model types
        pass

    async def _check_confidence(self, output: Any, threshold: float) -> Dict:
        """Check output confidence"""
        # Call confidence model
        pass

    def _aggregate_results(self, results: Dict, plan: Dict) -> Any:
        """Combine multi-step results into final output"""
        # Aggregate logic
        pass


# Global instance
agent_orchestrator = AgentOrchestrator()
```

### Phase 3: Confidence Model (Week 5)

```python
# File: core/services/confidence_model.py

from llama_cpp import Llama
import asyncio

class ConfidenceModel:
    """
    Validates outputs and detects hallucinations

    Works in tandem with router for each layer
    """

    def __init__(self):
        # Use small, fast model for validation
        self.model = Llama(
            model_path="./models/qwen-0.5b-q4.gguf",
            n_ctx=2048,
            n_threads=2,
            verbose=False
        )

    async def score(
        self,
        output: str,
        original_request: str,
        sources: List[str] = None,
        context: Dict = None
    ) -> Dict:
        """
        Score output confidence

        Returns:
        {
            "confidence": 0.0-1.0,
            "scores": {
                "factual": 0.0-1.0,
                "consistent": 0.0-1.0,
                "complete": 0.0-1.0,
                "grounded": 0.0-1.0
            },
            "issues": [str],
            "recommendation": "accept" | "retry" | "escalate"
        }
        """

        prompt = f"""<|system|>
You are a confidence scorer. Evaluate the output quality.

Criteria:
1. Factual: Is it accurate? (check against sources if provided)
2. Consistent: Is it internally consistent?
3. Complete: Does it fully answer the request?
4. Grounded: Is it based on provided context/sources?

Score each 0-1, provide overall confidence.
<|user|>
Original Request: {original_request}
Output to Evaluate: {output}
Sources: {sources or "None provided"}
Context: {context or "None"}
<|assistant|>
"""

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.model(prompt, max_tokens=256, temperature=0.2)
        )

        # Parse confidence scores
        import json
        try:
            scores = json.loads(result['choices'][0]['text'])
        except:
            # Fallback: medium confidence
            scores = {
                "confidence": 0.6,
                "scores": {
                    "factual": 0.6,
                    "consistent": 0.6,
                    "complete": 0.6,
                    "grounded": 0.6
                },
                "issues": ["Could not parse confidence score"],
                "recommendation": "accept"
            }

        # Determine recommendation
        if scores['confidence'] >= 0.8:
            scores['recommendation'] = 'accept'
        elif scores['confidence'] >= 0.6:
            scores['recommendation'] = 'retry'
        else:
            scores['recommendation'] = 'escalate'

        return scores


# Global instance
confidence_model = ConfidenceModel()
```

### Phase 4: Unified Request Handler (Week 6)

```python
# File: core/services/unified_request_handler.py

from core.services.router_model import router_model
from core.services.agent_orchestrator import agent_orchestrator
from core.services.confidence_model import confidence_model
from core.services.local_llm_service import local_llm_service

class UnifiedRequestHandler:
    """
    Main entry point for all user requests

    Orchestrates: Router → Execution → Confidence → Response
    """

    async def handle_request(
        self,
        user_request: str,
        user_id: str,
        context: Dict = None,
        stream: bool = False
    ):
        """
        Process user request through intelligent routing system
        """

        # Step 1: Route the request
        routing_decision = await router_model.route(user_request, context)

        # Step 2: Execute based on path
        if routing_decision['path'] == 'simple':
            # Direct LLM response
            response = await local_llm_service.generate(
                prompt=user_request,
                model_name=routing_decision['recommended_models'][0],
                max_tokens=512
            )

            # Quick confidence check
            confidence = await confidence_model.score(
                output=response,
                original_request=user_request
            )

            return {
                "response": response,
                "path": "simple",
                "confidence": confidence,
                "models_used": routing_decision['recommended_models']
            }

        elif routing_decision['path'] == 'complex':
            # Multi-step workflow through orchestrator
            plan = await agent_orchestrator.plan_execution(
                user_request,
                routing_decision
            )

            # Execute plan (streaming)
            final_result = None
            async for step_result in agent_orchestrator.execute_plan(plan, user_id):
                if stream:
                    yield step_result

                if step_result['step'] == 'final':
                    final_result = step_result['result']

            return final_result

        else:  # specialized
            # Route to specific specialized model/tool
            # Implementation for specialized paths
            pass


# Global instance
unified_handler = UnifiedRequestHandler()
```

## Updated Request Flow

### Example 1: Simple Request
```
User: "What is Python?"

Router Model (Liquid-1.2B):
├─ Complexity: 0.2
├─ Confidence: 0.95
└─ Path: SIMPLE → Qwen-7B

Qwen-7B:
└─ "Python is a high-level programming language..."

Confidence Model:
├─ Factual: 0.95
├─ Complete: 0.90
└─ Overall: 0.92 → ACCEPT

Response to user (total time: 2-3 seconds)
```

### Example 2: Complex Request
```
User: "Research top 5 AI companies, analyze their strategies, create comparison table"

Router Model:
├─ Complexity: 0.85
├─ Confidence: 0.7
└─ Path: COMPLEX → Agent Orchestrator

Agent Orchestrator Plans:
├─ Step 1: web_search (Liquid-Tool)
├─ Step 2: extract_data (Liquid-Extract) [PARALLEL: 5 URLs]
├─ Step 3: analyze (DeepSeek-V3)
├─ Step 4: create_table (Code-Executor)
└─ Step 5: confidence_check (threshold: 0.8)

Execution:
├─ Step 1: ✓ Found 5 companies
├─ Step 2: ✓ Extracted data (parallel)
├─ Step 3: ✓ Analysis complete
├─ Step 4: ✓ Table generated
└─ Step 5: Confidence 0.85 → ACCEPT

Response to user (total time: 15-30 seconds)
```

## Model Selection Strategy

### Router Decision Matrix

| Complexity | Confidence | Tools Needed | Reasoning Required | Path | Model |
|------------|------------|--------------|-------------------|------|-------|
| <0.3 | >0.8 | No | No | Simple | Qwen-7B |
| <0.3 | >0.8 | Yes | No | Simple | Liquid-Tool |
| 0.3-0.6 | >0.7 | No | Yes | Specialized | DeepSeek-7B |
| 0.3-0.6 | >0.7 | Yes | No | Specialized | Liquid-Tool + LLM |
| >0.6 | Any | Any | Yes | Complex | Orchestrator → Multiple |
| Any | <0.7 | Any | Any | Complex | Orchestrator → Validation |

## Development Roadmap

### Week 1-2: Router Foundation
- [ ] Install llama.cpp
- [ ] Download Liquid-1.2B-Tool
- [ ] Implement RouterModel class
- [ ] Test complexity classification
- [ ] Test path decisions

### Week 3-4: Agent Orchestrator
- [ ] Download additional models (Qwen, DeepSeek)
- [ ] Implement AgentOrchestrator
- [ ] Workflow planning logic
- [ ] Multi-step execution
- [ ] Parallel task handling

### Week 5: Confidence Layer
- [ ] Download Qwen-0.5B for confidence
- [ ] Implement ConfidenceModel
- [ ] Validation scoring
- [ ] Retry logic

### Week 6: Integration
- [ ] UnifiedRequestHandler
- [ ] Remove old semantic model
- [ ] Update routes to use new architecture
- [ ] End-to-end testing
- [ ] Frontend updates

### Week 7-8: High-End Hardware Testing
- [ ] Port to 4090/better machine
- [ ] Load larger models (70B+)
- [ ] Benchmark DGX Spark equivalent
- [ ] Optimize for GH200 deployments
- [ ] Performance tuning

## Benefits of This Architecture

### vs Old Architecture:
- ❌ OLD: Every request went through full 5-step workflow
- ✅ NEW: 60% of requests get direct answers (faster)
- ❌ OLD: One semantic model did everything poorly
- ✅ NEW: Specialized models for specific tasks
- ❌ OLD: No confidence checking
- ✅ NEW: Built-in validation at every layer
- ❌ OLD: Fixed workflow
- ✅ NEW: Dynamic, intelligent orchestration

### Performance:
- **Simple requests**: 2-5 seconds (was 10-20s)
- **Complex requests**: 15-30 seconds (was 30-60s)
- **Accuracy**: Higher (specialized models)
- **Cost**: Lower (smaller models when possible)

### Scalability:
- Works on 8GB RAM (development)
- Scales to DGX Spark (128GB)
- Optimizes for GH200 clusters
- Adds models without architecture changes

Does this align with your vision? Should we proceed with implementation?
