# LALO AI - Functional MVP Implementation Plan
**Status**: Current system has cosmetic UI but lacks core enterprise functionality
**Goal**: Build a working enterprise AI platform with full LALO workflow, tools, security, and governance

---

## CRITICAL GAPS IDENTIFIED

### What's Missing (Enterprise Blockers)
1. **Core LALO Workflow** - Recursive feedback loops not implemented
2. **Semantic Interpretation Layer** - Confidence scoring exists but not integrated into flow
3. **Tool Integration** - No web search, RAG, image generation in main chat
4. **Security & Governance** - Missing RBAC, audit logs, data governance
5. **Agent Management** - No ability to create/manage custom agents
6. **Data Seeding** - No connector framework for enterprise data sources
7. **Self-Improvement** - Feedback collection exists but no learning loop
8. **Professional UI** - Text too large, poor spacing, looks "childish"

### What Needs to Work for MVP
- ✅ User sends request via professional chat interface
- ✅ System runs full LALO workflow with visual progress
- ✅ Recursive feedback at each stage (human-in-the-loop)
- ✅ Confidence gating prevents low-quality outputs
- ✅ Tools available: Web search, RAG, image generation, code execution
- ✅ Results shown with full audit trail
- ✅ Admin can create agents, seed data, configure governance
- ✅ System learns from feedback (self-improvement)

---

## PHASE 1: CORE ARCHITECTURE REBUILD (Week 1-2)

### 1.1 Professional Chat Interface (3-4 days)
**Problem**: Current UI is rudimentary, elements too large, poor UX

**Solution**: Build enterprise-grade chat interface
- Compact, professional design (similar to ChatGPT/Claude.ai but branded)
- Message history with user/assistant roles
- Tool use indicators (searching web, generating image, etc.)
- Streaming responses with typewriter effect
- Markdown rendering with code syntax highlighting
- File upload support (PDFs, images, documents)
- Export conversation as PDF/JSON

**Files to Create/Modify**:
```
lalo-frontend/src/components/
  ├── Chat/
  │   ├── ChatInterface.tsx          # Main chat container
  │   ├── MessageList.tsx             # Scrollable message history
  │   ├── Message.tsx                 # Individual message component
  │   ├── MessageInput.tsx            # Input with file upload
  │   ├── ToolIndicator.tsx           # Visual indicator for tool use
  │   ├── StreamingMessage.tsx        # Typewriter effect component
  │   └── ExportDialog.tsx            # Export conversation UI
  └── styles/
      └── chat.module.css             # Professional, compact styling
```

**Design Requirements**:
- Font size: 14-16px (not 18-20px)
- Line height: 1.5
- Message padding: 12px 16px
- Proper whitespace and visual hierarchy
- Subtle shadows and borders
- Responsive (desktop/tablet/mobile)

### 1.2 Full LALO Workflow Integration (5-7 days)
**Problem**: Workflow exists but doesn't run end-to-end in chat

**Solution**: Implement complete recursive workflow

**Step 1: Semantic Interpretation with Confidence**
```python
# core/services/semantic_interpreter.py
class SemanticInterpreter:
    async def interpret(self, user_input: str) -> InterpretationResult:
        # Use GPT-4 for semantic understanding
        interpretation = await self.model.generate(
            prompt=f"Analyze this request and extract intent: {user_input}"
        )

        # Use separate model for confidence scoring
        confidence = await self.confidence_judge.score(
            input=user_input,
            interpretation=interpretation
        )

        # Generate clarifying questions if confidence < threshold
        if confidence < 0.75:
            clarifications = await self.generate_clarifications(
                user_input, interpretation, confidence
            )
            return InterpretationResult(
                intent=interpretation,
                confidence=confidence,
                needs_clarification=True,
                suggested_questions=clarifications
            )

        return InterpretationResult(
            intent=interpretation,
            confidence=confidence,
            needs_clarification=False
        )
```

**Step 2: Recursive Planning with Feedback**
```python
# core/services/action_planner.py
class ActionPlanner:
    async def create_plan(
        self,
        intent: str,
        context: dict,
        max_iterations: int = 3
    ) -> ActionPlan:
        plan = None
        critique = None

        for iteration in range(max_iterations):
            # Generate or refine plan
            plan = await self.generate_plan(intent, context, critique)

            # Self-critique using separate model
            critique = await self.critique_plan(plan, intent)

            # Check if plan meets quality threshold
            if critique.score >= 0.8:
                break

            # If not, use critique to improve next iteration
            context["previous_critique"] = critique

        return ActionPlan(
            steps=plan.steps,
            confidence=critique.score,
            iterations=iteration + 1,
            final_critique=critique
        )
```

**Step 3: Tool Execution with Verification**
```python
# core/services/tool_executor.py
class ToolExecutor:
    async def execute_step(
        self,
        step: PlanStep,
        human_approved: bool = False
    ) -> ExecutionResult:
        # Create backup/snapshot before execution
        backup_id = await self.create_backup()

        try:
            # Execute with appropriate tool
            if step.tool == "web_search":
                result = await self.search_web(step.params)
            elif step.tool == "generate_image":
                result = await self.generate_image(step.params)
            elif step.tool == "query_rag":
                result = await self.query_rag(step.params)
            elif step.tool == "execute_code":
                result = await self.execute_code_sandboxed(step.params)

            # Verify result meets expectations
            verification = await self.verify_result(
                result, step.expected_outcome
            )

            if not verification.passed:
                # Rollback if verification fails
                await self.restore_backup(backup_id)
                return ExecutionResult(
                    success=False,
                    error=verification.issue,
                    backup_restored=True
                )

            return ExecutionResult(
                success=True,
                data=result,
                verification=verification
            )

        except Exception as e:
            # Automatic rollback on error
            await self.restore_backup(backup_id)
            return ExecutionResult(
                success=False,
                error=str(e),
                backup_restored=True
            )
```

**Step 4: Human-in-the-Loop Gates**
```python
# core/services/workflow_orchestrator.py
class WorkflowOrchestrator:
    async def run_workflow(
        self,
        user_request: str,
        user_id: str
    ) -> WorkflowResult:
        # Step 1: Semantic Interpretation
        interpretation = await self.semantic_interpreter.interpret(user_request)

        if interpretation.needs_clarification:
            # PAUSE: Wait for human feedback
            await self.request_clarification(
                user_id,
                interpretation.suggested_questions
            )
            # Resume when user provides clarification
            user_clarification = await self.wait_for_user_response(user_id)
            interpretation = await self.semantic_interpreter.interpret(
                user_request + "\n" + user_clarification
            )

        # Step 2: Action Planning
        plan = await self.action_planner.create_plan(
            interpretation.intent,
            context={"user_history": await self.get_user_history(user_id)}
        )

        # PAUSE: Human approval of plan
        plan_approved = await self.request_approval(
            user_id,
            plan,
            approval_type="plan"
        )

        if not plan_approved:
            # User rejected plan - ask for feedback
            feedback = await self.request_feedback(user_id, "plan_rejection")
            plan = await self.action_planner.create_plan(
                interpretation.intent,
                context={"user_feedback": feedback}
            )
            plan_approved = await self.request_approval(user_id, plan)

        # Step 3: Execution
        results = []
        for step in plan.steps:
            result = await self.tool_executor.execute_step(step)
            results.append(result)

            if not result.success:
                # PAUSE: Notify user of failure
                retry = await self.request_retry_decision(
                    user_id,
                    step,
                    result.error
                )
                if retry:
                    result = await self.tool_executor.execute_step(step)
                else:
                    break

        # Step 4: Review Results
        # PAUSE: Human review
        final_approval = await self.request_approval(
            user_id,
            results,
            approval_type="final"
        )

        # Step 5: Commit to Memory
        if final_approval:
            await self.commit_to_permanent_memory(
                user_request,
                interpretation,
                plan,
                results
            )

        return WorkflowResult(
            success=final_approval,
            interpretation=interpretation,
            plan=plan,
            results=results
        )
```

### 1.3 Tool Integration (4-5 days)
**Problem**: No web search, RAG, image generation, or code execution

**Solution**: Implement core enterprise tools

#### Web Search Tool
```python
# core/tools/web_search.py
from tavily import TavilyClient  # or SerpAPI, Bing API

class WebSearchTool:
    def __init__(self, api_key: str):
        self.client = TavilyClient(api_key=api_key)

    async def search(
        self,
        query: str,
        num_results: int = 5
    ) -> SearchResults:
        results = await self.client.search(
            query=query,
            max_results=num_results,
            search_depth="advanced"
        )

        return SearchResults(
            query=query,
            results=[
                SearchResult(
                    title=r["title"],
                    url=r["url"],
                    content=r["content"],
                    relevance_score=r.get("score", 0)
                )
                for r in results["results"]
            ]
        )
```

#### RAG (Retrieval-Augmented Generation) Tool
```python
# core/tools/rag_tool.py
from chromadb import Client
from sentence_transformers import SentenceTransformer

class RAGTool:
    def __init__(self, vector_db_path: str):
        self.db = Client(path=vector_db_path)
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')

    async def query(
        self,
        query: str,
        collection_name: str,
        top_k: int = 5
    ) -> RAGResults:
        # Encode query
        query_embedding = self.encoder.encode(query)

        # Retrieve similar documents
        collection = self.db.get_collection(collection_name)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        return RAGResults(
            query=query,
            documents=results["documents"][0],
            metadatas=results["metadatas"][0],
            distances=results["distances"][0]
        )
```

#### Image Generation Tool
```python
# core/tools/image_generator.py
from openai import AsyncOpenAI

class ImageGeneratorTool:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard"
    ) -> ImageResult:
        response = await self.client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality=quality,
            n=1
        )

        return ImageResult(
            url=response.data[0].url,
            revised_prompt=response.data[0].revised_prompt
        )
```

#### Code Execution Tool (Sandboxed)
```python
# core/tools/code_executor.py
import docker

class CodeExecutorTool:
    def __init__(self):
        self.docker_client = docker.from_env()

    async def execute(
        self,
        code: str,
        language: str = "python",
        timeout: int = 30
    ) -> ExecutionResult:
        # Create isolated container
        container = self.docker_client.containers.run(
            image=f"lalo-sandbox-{language}:latest",
            command=f"python -c \"{code}\"",
            detach=True,
            mem_limit="512m",
            cpu_quota=50000,  # 50% of one core
            network_disabled=True  # No network access
        )

        try:
            # Wait for completion
            result = container.wait(timeout=timeout)
            logs = container.logs().decode('utf-8')

            return ExecutionResult(
                success=result["StatusCode"] == 0,
                output=logs,
                exit_code=result["StatusCode"]
            )

        finally:
            container.remove(force=True)
```

### 1.4 Chat-Workflow Integration (2-3 days)
**Problem**: Workflow and chat are separate

**Solution**: Stream workflow updates into chat

```typescript
// lalo-frontend/src/components/Chat/ChatInterface.tsx
export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [workflowState, setWorkflowState] = useState<WorkflowState | null>(null);

  const sendMessage = async (content: string) => {
    // Add user message
    const userMsg: Message = { role: 'user', content };
    setMessages(prev => [...prev, userMsg]);

    // Start workflow
    const response = await fetch('/api/workflow/start', {
      method: 'POST',
      body: JSON.stringify({ user_request: content })
    });

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();

    let assistantMessage: Message = {
      role: 'assistant',
      content: '',
      workflow: null
    };

    // Stream workflow updates
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const updates = chunk.split('\n').filter(Boolean);

      for (const update of updates) {
        const data = JSON.parse(update);

        if (data.type === 'workflow_update') {
          setWorkflowState(data.workflow);
          assistantMessage.workflow = data.workflow;
        } else if (data.type === 'content_chunk') {
          assistantMessage.content += data.text;
        } else if (data.type === 'tool_use') {
          assistantMessage.tool_calls = [
            ...(assistantMessage.tool_calls || []),
            data.tool
          ];
        }

        setMessages(prev => [...prev.slice(0, -1), { ...assistantMessage }]);
      }
    }
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <MessageList messages={messages} />

      {workflowState && (
        <WorkflowProgress state={workflowState} />
      )}

      <MessageInput onSend={sendMessage} />
    </Box>
  );
}
```

---

## PHASE 2: SECURITY & GOVERNANCE (Week 3)

### 2.1 Role-Based Access Control (2-3 days)
```python
# core/services/auth.py
class Role(Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"

class Permission(Enum):
    CREATE_AGENT = "create_agent"
    MODIFY_SYSTEM = "modify_system"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    EXECUTE_WORKFLOW = "execute_workflow"

ROLE_PERMISSIONS = {
    Role.ADMIN: [
        Permission.CREATE_AGENT,
        Permission.MODIFY_SYSTEM,
        Permission.VIEW_AUDIT_LOGS,
        Permission.EXECUTE_WORKFLOW
    ],
    Role.USER: [Permission.EXECUTE_WORKFLOW],
    Role.VIEWER: []
}

def has_permission(user_role: Role, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(user_role, [])
```

### 2.2 Audit Logging (1-2 days)
```python
# core/services/audit_logger.py
class AuditLogger:
    async def log_event(
        self,
        user_id: str,
        action: str,
        resource: str,
        details: dict,
        result: str  # "success" or "failure"
    ):
        entry = AuditLogEntry(
            timestamp=datetime.utcnow(),
            user_id=user_id,
            action=action,
            resource=resource,
            details=details,
            result=result,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )

        # Store in database
        await self.db.audit_logs.insert(entry)

        # Also write to immutable log file
        await self.write_to_immutable_log(entry)
```

### 2.3 Data Governance (1-2 days)
```python
# core/services/data_governance.py
class DataGovernor:
    def __init__(self):
        self.policies = self.load_governance_policies()

    async def check_data_access(
        self,
        user_id: str,
        data_source: str,
        action: str
    ) -> GovernanceDecision:
        policy = self.policies.get(data_source)

        if not policy:
            return GovernanceDecision(
                allowed=False,
                reason="No governance policy defined"
            )

        # Check user clearance
        user_clearance = await self.get_user_clearance(user_id)

        if user_clearance < policy.required_clearance:
            await self.audit_logger.log_event(
                user_id=user_id,
                action=f"denied_access_to_{data_source}",
                resource=data_source,
                details={"reason": "insufficient_clearance"},
                result="failure"
            )
            return GovernanceDecision(
                allowed=False,
                reason=f"Requires {policy.required_clearance} clearance"
            )

        return GovernanceDecision(allowed=True)
```

---

## PHASE 3: AGENT MANAGEMENT (Week 4)

### 3.1 Agent Builder UI (3-4 days)
```typescript
// lalo-frontend/src/components/AgentBuilder/AgentBuilder.tsx
interface Agent {
  id: string;
  name: string;
  description: string;
  system_prompt: string;
  tools: string[];  // ["web_search", "rag", "image_gen"]
  model: string;
  temperature: number;
  max_tokens: number;
  guardrails: Guardrail[];
}

export function AgentBuilder() {
  const [agent, setAgent] = useState<Agent>(defaultAgent);

  return (
    <Box>
      <TextField
        label="Agent Name"
        value={agent.name}
        onChange={e => setAgent({...agent, name: e.target.value})}
      />

      <TextField
        label="System Prompt"
        multiline
        rows={8}
        value={agent.system_prompt}
        onChange={e => setAgent({...agent, system_prompt: e.target.value})}
      />

      <FormControl>
        <InputLabel>Available Tools</InputLabel>
        <Select
          multiple
          value={agent.tools}
          onChange={e => setAgent({...agent, tools: e.target.value as string[]})}
        >
          <MenuItem value="web_search">Web Search</MenuItem>
          <MenuItem value="rag">RAG (Document Search)</MenuItem>
          <MenuItem value="image_gen">Image Generation</MenuItem>
          <MenuItem value="code_exec">Code Execution</MenuItem>
        </Select>
      </FormControl>

      <GuardrailBuilder
        guardrails={agent.guardrails}
        onChange={guardrails => setAgent({...agent, guardrails})}
      />

      <Button onClick={() => saveAgent(agent)}>
        Create Agent
      </Button>
    </Box>
  );
}
```

### 3.2 Agent Execution Engine (2-3 days)
```python
# core/services/agent_engine.py
class AgentEngine:
    async def execute_agent(
        self,
        agent_id: str,
        user_input: str,
        user_id: str
    ) -> AgentResponse:
        agent = await self.load_agent(agent_id)

        # Build conversation context
        messages = [
            {"role": "system", "content": agent.system_prompt},
            {"role": "user", "content": user_input}
        ]

        # Run with tool support
        response = await self.llm_client.chat.completions.create(
            model=agent.model,
            messages=messages,
            tools=self.build_tool_definitions(agent.tools),
            temperature=agent.temperature,
            max_tokens=agent.max_tokens
        )

        # Process tool calls
        if response.choices[0].message.tool_calls:
            tool_results = []
            for tool_call in response.choices[0].message.tool_calls:
                result = await self.execute_tool(
                    tool_call.function.name,
                    json.loads(tool_call.function.arguments),
                    agent.guardrails
                )
                tool_results.append(result)

            # Continue conversation with tool results
            messages.append(response.choices[0].message)
            for result in tool_results:
                messages.append({
                    "role": "tool",
                    "content": json.dumps(result)
                })

            # Get final response
            final_response = await self.llm_client.chat.completions.create(
                model=agent.model,
                messages=messages
            )

            return AgentResponse(
                content=final_response.choices[0].message.content,
                tool_calls=tool_results
            )

        return AgentResponse(
            content=response.choices[0].message.content
        )
```

---

## PHASE 4: DATA SEEDING & CONNECTORS (Week 5)

### 4.1 Connector Framework (3-4 days)
```python
# connectors/base_connector.py
class BaseConnector(ABC):
    @abstractmethod
    async def connect(self, credentials: dict) -> bool:
        """Establish connection to data source"""
        pass

    @abstractmethod
    async def query(self, query: str) -> QueryResult:
        """Execute query and return results"""
        pass

    @abstractmethod
    async def index_documents(self, collection_name: str) -> IndexResult:
        """Index documents into vector database"""
        pass

# connectors/sharepoint_connector.py
class SharePointConnector(BaseConnector):
    async def connect(self, credentials: dict) -> bool:
        self.client = SharePointClient(
            site_url=credentials["site_url"],
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"]
        )
        return await self.client.authenticate()

    async def query(self, query: str) -> QueryResult:
        results = await self.client.search(query)
        return QueryResult(
            items=[
                Document(
                    title=item["title"],
                    content=item["content"],
                    url=item["url"],
                    metadata=item["metadata"]
                )
                for item in results
            ]
        )

    async def index_documents(self, collection_name: str) -> IndexResult:
        # Get all documents
        docs = await self.client.get_all_documents()

        # Chunk and embed
        chunks = []
        for doc in docs:
            doc_chunks = self.chunk_document(doc.content)
            embeddings = await self.embed_chunks(doc_chunks)
            chunks.extend([
                ChunkedDocument(
                    text=chunk,
                    embedding=emb,
                    metadata={
                        "source": doc.url,
                        "title": doc.title,
                        **doc.metadata
                    }
                )
                for chunk, emb in zip(doc_chunks, embeddings)
            ])

        # Store in vector DB
        await self.vector_db.add_documents(collection_name, chunks)

        return IndexResult(
            success=True,
            documents_indexed=len(docs),
            chunks_created=len(chunks)
        )
```

### 4.2 Data Seeding UI (2-3 days)
```typescript
// lalo-frontend/src/components/DataSeeding/DataSeedingManager.tsx
export function DataSeedingManager() {
  const [connectors, setConnectors] = useState<Connector[]>([]);

  const addConnector = async (type: string, credentials: any) => {
    const response = await fetch('/api/connectors', {
      method: 'POST',
      body: JSON.stringify({ type, credentials })
    });

    if (response.ok) {
      const connector = await response.json();
      setConnectors([...connectors, connector]);
    }
  };

  const indexData = async (connectorId: string, collectionName: string) => {
    await fetch(`/api/connectors/${connectorId}/index`, {
      method: 'POST',
      body: JSON.stringify({ collection_name: collectionName })
    });
  };

  return (
    <Box>
      <Typography variant="h5">Data Sources</Typography>

      <Grid container spacing={2}>
        {connectors.map(connector => (
          <Grid item xs={12} md={6} key={connector.id}>
            <Card>
              <CardContent>
                <Typography variant="h6">{connector.type}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Status: {connector.status}
                </Typography>
                <Typography variant="caption">
                  Documents indexed: {connector.documents_indexed}
                </Typography>
              </CardContent>
              <CardActions>
                <Button onClick={() => indexData(connector.id, 'default')}>
                  Reindex
                </Button>
                <Button onClick={() => testConnection(connector.id)}>
                  Test Connection
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Button onClick={() => setShowAddDialog(true)}>
        Add Data Source
      </Button>
    </Box>
  );
}
```

---

## PHASE 5: SELF-IMPROVEMENT SYSTEM (Week 6)

### 5.1 Feedback Collection & Analysis (2-3 days)
```python
# core/services/feedback_analyzer.py
class FeedbackAnalyzer:
    async def analyze_feedback(self, workflow_id: str) -> FeedbackInsights:
        workflow = await self.db.workflows.find_one({"id": workflow_id})
        feedback_history = workflow.get("feedback_history", [])

        # Analyze patterns
        negative_feedback = [f for f in feedback_history if f["rating"] < 3]

        if negative_feedback:
            # Extract common issues
            issues = await self.extract_issues(negative_feedback)

            # Generate improvement suggestions
            suggestions = await self.generate_improvements(issues)

            # Store for training
            await self.db.training_data.insert({
                "workflow_id": workflow_id,
                "issues": issues,
                "suggestions": suggestions,
                "created_at": datetime.utcnow()
            })

            return FeedbackInsights(
                has_issues=True,
                issues=issues,
                suggestions=suggestions
            )

        return FeedbackInsights(has_issues=False)
```

### 5.2 Continuous Learning Loop (2-3 days)
```python
# core/services/learning_engine.py
class LearningEngine:
    async def update_models_from_feedback(self):
        # Get recent feedback
        training_data = await self.db.training_data.find({
            "processed": False
        }).limit(100).to_list()

        if not training_data:
            return

        # Prepare fine-tuning dataset
        examples = []
        for data in training_data:
            examples.append({
                "input": data["original_input"],
                "good_output": data["expected_output"],
                "bad_output": data["actual_output"],
                "feedback": data["user_feedback"]
            })

        # Fine-tune interpretation model
        await self.fine_tune_model(
            model_name="semantic_interpreter",
            examples=examples
        )

        # Mark as processed
        await self.db.training_data.update_many(
            {"_id": {"$in": [d["_id"] for d in training_data]}},
            {"$set": {"processed": True}}
        )
```

---

## PHASE 6: PROFESSIONAL UI POLISH (Week 7)

### 6.1 Design System Implementation (3-4 days)
**Files to Create**:
```
lalo-frontend/src/
  ├── theme/
  │   ├── typography.ts       # Professional font stack and sizes
  │   ├── spacing.ts          # Consistent spacing scale
  │   ├── colors.ts           # Enterprise color palette
  │   └── components.ts       # Component style overrides
  └── styles/
      └── global.css          # Global resets and utilities
```

**Typography System**:
```typescript
// theme/typography.ts
export const typography = {
  fontFamily: '"Inter", "Segoe UI", "Roboto", "Helvetica", sans-serif',
  fontSize: 14,

  h1: { fontSize: 32, fontWeight: 600, lineHeight: 1.2 },
  h2: { fontSize: 28, fontWeight: 600, lineHeight: 1.3 },
  h3: { fontSize: 24, fontWeight: 600, lineHeight: 1.4 },
  h4: { fontSize: 20, fontWeight: 600, lineHeight: 1.4 },
  h5: { fontSize: 16, fontWeight: 600, lineHeight: 1.5 },
  h6: { fontSize: 14, fontWeight: 600, lineHeight: 1.5 },

  body1: { fontSize: 14, lineHeight: 1.5 },
  body2: { fontSize: 13, lineHeight: 1.5 },
  caption: { fontSize: 12, lineHeight: 1.4 },

  button: { fontSize: 14, fontWeight: 500, textTransform: 'none' }
};
```

**Spacing System**:
```typescript
// theme/spacing.ts
export const spacing = (factor: number) => factor * 8; // 8px base unit

// Usage: spacing(1) = 8px, spacing(2) = 16px, spacing(3) = 24px
```

### 6.2 Component Refinement (2-3 days)
- Reduce all font sizes by 20-30%
- Add proper whitespace (8px grid)
- Implement subtle shadows and borders
- Add hover/focus states
- Improve form field styling
- Add loading skeletons
- Implement empty states

---

## MVP SUCCESS CRITERIA

### Functional Requirements
- [ ] User can send message and get AI response
- [ ] Full LALO workflow executes with visible progress
- [ ] Human-in-the-loop approval at each stage
- [ ] Confidence gating prevents low-quality outputs
- [ ] Web search, RAG, image generation work in chat
- [ ] Admin can create custom agents
- [ ] Admin can connect data sources (SharePoint, S3, etc.)
- [ ] System learns from user feedback
- [ ] Audit logs track all actions
- [ ] RBAC enforces permissions

### Non-Functional Requirements
- [ ] Professional, enterprise-grade UI
- [ ] Response time < 3s for standard queries
- [ ] Mobile responsive design
- [ ] Accessibility (WCAG 2.1 AA)
- [ ] Comprehensive error handling
- [ ] Security: HTTPS, auth, data encryption

### Business Requirements
- [ ] Demo-ready for investors
- [ ] Can showcase to enterprise clients
- [ ] Clear value proposition visible in UI
- [ ] Scalable architecture
- [ ] Documented for future development

---

## TIMELINE SUMMARY

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1-2  | Core Architecture | Professional chat, full workflow, tool integration |
| 3    | Security & Governance | RBAC, audit logs, data governance |
| 4    | Agent Management | Agent builder, execution engine |
| 5    | Data Seeding | Connector framework, SharePoint/S3 connectors |
| 6    | Self-Improvement | Feedback analysis, learning loop |
| 7    | UI Polish | Design system, component refinement |

**Total Time**: 7 weeks to functional MVP
**Team**: 1-2 developers (full-time)

---

## NEXT IMMEDIATE STEPS

1. **Kill all background processes** (clean slate)
2. **Audit existing code** (what can we keep vs rebuild)
3. **Start with Phase 1.1** (professional chat interface)
4. **Build incrementally** (test each piece before moving on)
5. **Get user feedback early** (don't wait 7 weeks for first test)

This is a realistic plan to build a **working enterprise AI platform**, not just a UI mockup.
