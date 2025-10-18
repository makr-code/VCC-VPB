# INTERLOCK Element - Comprehensive Documentation

**Version:** 1.0  
**Status:** ✅ Released  
**Element Type:** `INTERLOCK`  
**Category:** Elemente – Logik (Logic Elements)  
**Purpose:** Resource locking and synchronization using MUTEX and SEMAPHORE mechanisms

---

## Table of Contents

1. [Overview](#overview)
2. [Key Concepts](#key-concepts)
3. [MUTEX vs SEMAPHORE](#mutex-vs-semaphore)
4. [Properties Reference](#properties-reference)
5. [Visual Representation](#visual-representation)
6. [Usage Examples](#usage-examples)
7. [Resource Management](#resource-management)
8. [Deadlock Prevention](#deadlock-prevention)
9. [Best Practices](#best-practices)
10. [Validation Rules](#validation-rules)
11. [Implementation Details](#implementation-details)
12. [API Reference](#api-reference)
13. [FAQ](#faq)
14. [Roadmap](#roadmap)

---

## Overview

### What is INTERLOCK?

The **INTERLOCK** element provides process synchronization and resource locking mechanisms in VPB workflows. It enables processes to coordinate access to shared resources, preventing race conditions, data corruption, and resource conflicts.

**Core Capabilities:**
- 🔒 **Exclusive Access (MUTEX):** One process at a time can access a resource
- 🔓 **Limited Concurrent Access (SEMAPHORE):** Up to N processes can access simultaneously
- ⏱️ **Timeout Handling:** Configurable wait times with fallback behavior
- 🔄 **Automatic Release:** Optional auto-release after process completion
- 🎯 **Fallback Routing:** Define alternative paths when locks are unavailable

### When to Use INTERLOCK

**Use INTERLOCK when:**
- ✅ Multiple processes need to access the same database connection
- ✅ API rate limiting requires controlled concurrent requests
- ✅ File access must be serialized to prevent corruption
- ✅ Shared resources (printers, hardware) need coordination
- ✅ Thread pool or connection pool management is needed
- ✅ Preventing duplicate processing of the same data

**Don't use INTERLOCK when:**
- ❌ Process flow is entirely sequential (no parallelism)
- ❌ Resources are stateless and don't require coordination
- ❌ Simple conditional branching is sufficient (use CONDITION instead)

---

## Key Concepts

### Resource Identification

Every INTERLOCK protects a **resource** identified by a unique **Resource-ID**:

```
Resource-ID: "db_connection_pool"
             └─ Unique identifier for the protected resource
```

**Multiple INTERLOCK elements with the same Resource-ID coordinate access to the same resource.**

### Lock Acquisition Flow

```
Process arrives at INTERLOCK
    ↓
Is lock available?
    ├─ YES → Acquire lock → Continue process → Release lock (if auto-release)
    └─ NO → Wait or timeout?
           ├─ Wait (timeout=0) → Block until available
           └─ Timeout (timeout>0) → Wait N seconds → Route to fallback target
```

### Lock Types Comparison

| Feature | MUTEX | SEMAPHORE |
|---------|-------|-----------|
| **Max Concurrent** | 1 (exclusive) | N (configurable) |
| **Use Case** | Single resource access | Limited pool of resources |
| **Icon** | 🔒 | 🔓 |
| **Example** | Database write lock | API rate limit (10 req/sec) |

---

## MUTEX vs SEMAPHORE

### MUTEX (Mutual Exclusion)

**Definition:** Only ONE process can hold the lock at any time.

**Configuration:**
- `interlock_type = "MUTEX"`
- `interlock_max_count = 1`

**Visual:**
```
🔒 MUTEX
Resource: db_connection
```

**Use Cases:**

1. **Database Single Connection**
   ```
   Problem: Multiple processes writing to DB simultaneously → corruption
   Solution: MUTEX on "db_connection" → sequential writes
   ```

2. **File Write Access**
   ```
   Problem: Concurrent writes to same file → data loss
   Solution: MUTEX on "logfile_write" → one writer at a time
   ```

3. **Configuration File Updates**
   ```
   Problem: Multiple processes updating config.json → invalid JSON
   Solution: MUTEX on "config_update" → atomic updates
   ```

4. **Hardware Device Access**
   ```
   Problem: Multiple print jobs to one printer → garbled output
   Solution: MUTEX on "printer_device_1" → sequential printing
   ```

**Characteristics:**
- ✅ Strongest isolation guarantee
- ✅ Prevents all concurrent access
- ⚠️ Can become bottleneck if held too long
- ⚠️ Risk of deadlock if multiple MUTEXes required

---

### SEMAPHORE (Counting Semaphore)

**Definition:** Up to N processes can hold the lock simultaneously.

**Configuration:**
- `interlock_type = "SEMAPHORE"`
- `interlock_max_count = N` (where N > 1)

**Visual:**
```
🔓 SEMAPHORE Max: 10
Resource: api_rate_limit
```

**Use Cases:**

1. **API Rate Limiting**
   ```
   Problem: External API allows max 10 concurrent requests
   Solution: SEMAPHORE with max_count=10 on "external_api"
   ```

2. **Database Connection Pool**
   ```
   Problem: DB supports 20 concurrent connections
   Solution: SEMAPHORE with max_count=20 on "db_pool"
   ```

3. **Thread Pool Management**
   ```
   Problem: CPU has 8 cores, want to limit parallel tasks
   Solution: SEMAPHORE with max_count=8 on "cpu_pool"
   ```

4. **Bandwidth Control**
   ```
   Problem: Network can handle 5 large downloads simultaneously
   Solution: SEMAPHORE with max_count=5 on "download_slots"
   ```

**Characteristics:**
- ✅ Allows controlled parallelism
- ✅ Better throughput than MUTEX for sharable resources
- ⚠️ More complex to reason about than MUTEX
- ⚠️ Requires careful tuning of max_count

---

### Choosing Between MUTEX and SEMAPHORE

**Decision Tree:**

```
Can the resource be safely shared by multiple processes?
    ├─ NO → Use MUTEX (max_count=1)
    │       Examples: file write, exclusive DB lock, config update
    │
    └─ YES → Use SEMAPHORE (max_count>1)
            Examples: read-only access, connection pool, rate limiting
```

**Performance Considerations:**

| Scenario | MUTEX Throughput | SEMAPHORE (N=5) Throughput | Winner |
|----------|------------------|---------------------------|--------|
| Sequential writes | 100% | 100% | Equal |
| Parallel reads | 20% (1 at a time) | 100% (5 at a time) | SEMAPHORE |
| Mixed read/write | 20% | 60-80% | SEMAPHORE |

---

## Properties Reference

### Complete Property List

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `interlock_type` | str | `"MUTEX"` | Yes | Lock type: `MUTEX` or `SEMAPHORE` |
| `interlock_resource_id` | str | `""` | **Yes** | Unique resource identifier |
| `interlock_max_count` | int | `1` | Yes | Max concurrent holders (1 for MUTEX, >1 for SEMAPHORE) |
| `interlock_timeout` | int | `0` | No | Wait timeout in seconds (0 = wait indefinitely) |
| `interlock_on_locked_target` | str | `""` | No | Element-ID to route to when lock unavailable |
| `interlock_auto_release` | bool | `True` | No | Auto-release lock after element execution |

---

### Property Details

#### 1. `interlock_type`

**Type:** `str`  
**Values:** `"MUTEX"` or `"SEMAPHORE"`  
**Default:** `"MUTEX"`

Determines the locking behavior:
- **MUTEX:** Exclusive access (max 1 holder)
- **SEMAPHORE:** Shared access (max N holders)

**Example:**
```json
{
  "interlock_type": "SEMAPHORE"
}
```

**Validation:**
- ❌ ERROR if not in `["MUTEX", "SEMAPHORE"]`

---

#### 2. `interlock_resource_id`

**Type:** `str`  
**Required:** ✅ **YES**  
**Default:** `""` (empty = validation error)

Unique identifier for the protected resource. Multiple INTERLOCK elements with the same `resource_id` coordinate access to the same logical resource.

**Naming Conventions:**
```
✅ Good:
- "db_connection"
- "api_rate_limit_external"
- "file_write_config_json"
- "printer_device_hp_01"

❌ Bad:
- "" (empty)
- "lock" (too generic)
- "resource123" (unclear purpose)
```

**Example:**
```json
{
  "interlock_resource_id": "db_connection_pool"
}
```

**Validation:**
- ❌ ERROR if empty
- ⚠️ WARNING if duplicate (informational - duplicates are intentional for coordination)

---

#### 3. `interlock_max_count`

**Type:** `int`  
**Range:** `> 0`  
**Default:** `1`

Maximum number of processes that can hold the lock simultaneously.

**Configuration:**
- **MUTEX:** Always `1`
- **SEMAPHORE:** Any integer `> 1`

**Examples:**
```json
// MUTEX - exclusive access
{
  "interlock_type": "MUTEX",
  "interlock_max_count": 1
}

// SEMAPHORE - up to 10 concurrent
{
  "interlock_type": "SEMAPHORE",
  "interlock_max_count": 10
}
```

**Validation:**
- ❌ ERROR if `<= 0`
- ⚠️ WARNING if SEMAPHORE with `max_count = 1` (behaves like MUTEX)
- ℹ️ INFO if MUTEX with `max_count != 1` (unusual)

---

#### 4. `interlock_timeout`

**Type:** `int`  
**Unit:** Seconds  
**Range:** `>= 0`  
**Default:** `0` (wait indefinitely)

How long to wait for lock acquisition before timing out.

**Values:**
- `0`: Wait indefinitely until lock becomes available
- `> 0`: Wait N seconds, then route to `on_locked_target` or fail

**Timeout Behavior:**
```
timeout = 0:
  Wait → Wait → Wait → ... → Lock acquired → Continue

timeout = 30:
  Wait (0s) → Wait (10s) → Wait (20s) → Wait (30s) → Timeout!
                                                      ↓
                                          Route to on_locked_target
```

**Examples:**
```json
// Wait indefinitely
{
  "interlock_timeout": 0
}

// Wait max 30 seconds
{
  "interlock_timeout": 30,
  "interlock_on_locked_target": "timeout_handler"
}
```

**Validation:**
- ❌ ERROR if `< 0`
- ⚠️ WARNING if `> 0` but `on_locked_target` is empty (timeout has no fallback)

---

#### 5. `interlock_on_locked_target`

**Type:** `str`  
**Default:** `""` (no fallback)

Element-ID to route to when lock cannot be acquired (either immediately or after timeout).

**Use Cases:**

1. **Graceful Degradation**
   ```json
   {
     "interlock_timeout": 10,
     "interlock_on_locked_target": "use_cache_instead"
   }
   ```

2. **Retry Queue**
   ```json
   {
     "interlock_timeout": 5,
     "interlock_on_locked_target": "add_to_retry_queue"
   }
   ```

3. **Error Handling**
   ```json
   {
     "interlock_timeout": 30,
     "interlock_on_locked_target": "lock_timeout_error"
   }
   ```

**Validation:**
- ⚠️ WARNING if target element doesn't exist

---

#### 6. `interlock_auto_release`

**Type:** `bool`  
**Default:** `True`

Whether to automatically release the lock after the element completes execution.

**Values:**
- `true`: Lock is automatically released when process moves to next element
- `false`: Lock must be manually released by explicit logic

**When to disable auto-release:**
- Lock must be held across multiple process steps
- Manual release control needed for complex workflows
- Lock lifetime spans external system interactions

**Example:**
```json
// Auto-release (recommended)
{
  "interlock_auto_release": true
}

// Manual release (advanced)
{
  "interlock_auto_release": false
  // Must explicitly release later
}
```

**Validation:**
- ℹ️ INFO if `false` (reminder to implement manual release logic)

---

## Visual Representation

### Canvas Appearance

#### MUTEX
```
┌─────────────────────────┐
│  🔒 MUTEX               │
│  db_connection          │
│                         │
│  Resource: db_conn      │
└─────────────────────────┘
```

#### SEMAPHORE
```
┌─────────────────────────┐
│  🔓 SEMAPHORE Max: 10   │
│  api_rate_limit         │
│                         │
│  Resource: ext_api      │
└─────────────────────────┘
```

### Color Scheme

- **Fill Color:** `#FFF3E0` (Light Orange)
- **Border Color:** `#FF9800` (Orange)
- **Shape:** Rounded Rectangle
- **Icons:** 🔒 (MUTEX) / 🔓 (SEMAPHORE)

### Palette Location

**Category:** "Elemente – Logik"  
**Position:** After STATE element

---

## Usage Examples

### Example 1: Database Connection Pool

**Scenario:** Multiple processes need to query a database that supports max 5 concurrent connections.

**Configuration:**
```json
{
  "element_type": "INTERLOCK",
  "name": "DB Pool Lock",
  "interlock_type": "SEMAPHORE",
  "interlock_resource_id": "postgres_pool",
  "interlock_max_count": 5,
  "interlock_timeout": 30,
  "interlock_on_locked_target": "db_busy_error",
  "interlock_auto_release": true
}
```

**Process Flow:**
```
Request 1 → [INTERLOCK] → Acquire (1/5) → Query DB → Release → Done
Request 2 → [INTERLOCK] → Acquire (2/5) → Query DB → Release → Done
Request 3 → [INTERLOCK] → Acquire (3/5) → Query DB → Release → Done
Request 4 → [INTERLOCK] → Acquire (4/5) → Query DB → Release → Done
Request 5 → [INTERLOCK] → Acquire (5/5) → Query DB → Release → Done
Request 6 → [INTERLOCK] → WAIT (pool full) → ... → Acquire → Query DB
```

**Benefits:**
- ✅ Never exceeds DB connection limit
- ✅ Graceful queueing of excess requests
- ✅ Timeout prevents indefinite waits

---

### Example 2: External API Rate Limiting

**Scenario:** External API allows max 10 requests per second. Process needs to call API 100 times.

**Configuration:**
```json
{
  "element_type": "INTERLOCK",
  "name": "API Rate Limit",
  "interlock_type": "SEMAPHORE",
  "interlock_resource_id": "external_api_rate",
  "interlock_max_count": 10,
  "interlock_timeout": 60,
  "interlock_on_locked_target": "api_throttled",
  "interlock_auto_release": true
}
```

**Process Flow:**
```
API Call 1-10  → [INTERLOCK] → All acquire (10/10) → Call API → Release
API Call 11    → [INTERLOCK] → WAIT (all slots full) → Wait for release
API Call 12-20 → [INTERLOCK] → Queue behind call 11
...
API Call 100   → [INTERLOCK] → Eventually processes
```

**Benefits:**
- ✅ Respects API rate limits
- ✅ Prevents 429 (Too Many Requests) errors
- ✅ Automatic throttling without code changes

---

### Example 3: Log File Write Access

**Scenario:** Multiple processes writing to same log file. File writes must be serialized.

**Configuration:**
```json
{
  "element_type": "INTERLOCK",
  "name": "Log File Lock",
  "interlock_type": "MUTEX",
  "interlock_resource_id": "application_log",
  "interlock_max_count": 1,
  "interlock_timeout": 0,
  "interlock_on_locked_target": "",
  "interlock_auto_release": true
}
```

**Process Flow:**
```
Process A → [INTERLOCK] → Acquire → Write "Entry A" → Release
Process B → [INTERLOCK] → WAIT (locked) → ... → Acquire → Write "Entry B"
Process C → [INTERLOCK] → WAIT (locked) → ... → Acquire → Write "Entry C"

Result: Clean, sequential log entries (no corruption)
```

**Benefits:**
- ✅ Prevents file corruption
- ✅ Maintains log integrity
- ✅ Simple exclusive access pattern

---

### Example 4: Configuration File Update

**Scenario:** Multiple processes need to update shared configuration. Updates must be atomic.

**Configuration:**
```json
{
  "element_type": "INTERLOCK",
  "name": "Config Update Lock",
  "interlock_type": "MUTEX",
  "interlock_resource_id": "config_json",
  "interlock_max_count": 1,
  "interlock_timeout": 10,
  "interlock_on_locked_target": "config_busy",
  "interlock_auto_release": true
}
```

**Process Flow:**
```
Update Request 1:
  [INTERLOCK] → Acquire → Read config → Modify → Write → Release

Update Request 2 (during Update 1):
  [INTERLOCK] → WAIT → (after 10s) → Timeout → Route to "config_busy"
```

**Benefits:**
- ✅ Atomic read-modify-write
- ✅ Prevents lost updates
- ✅ Timeout prevents indefinite waits

---

### Example 5: Thread Pool Management

**Scenario:** CPU-intensive tasks should run max 8 in parallel (8-core CPU).

**Configuration:**
```json
{
  "element_type": "INTERLOCK",
  "name": "CPU Pool",
  "interlock_type": "SEMAPHORE",
  "interlock_resource_id": "cpu_threads",
  "interlock_max_count": 8,
  "interlock_timeout": 0,
  "interlock_on_locked_target": "",
  "interlock_auto_release": true
}
```

**Process Flow:**
```
Task 1-8   → [INTERLOCK] → All acquire (8/8) → Execute in parallel
Task 9     → [INTERLOCK] → WAIT (all cores busy) → Queue
Task 1     → Complete → Release (7/8 in use)
Task 9     → Acquire (8/8 again) → Execute
```

**Benefits:**
- ✅ CPU utilization optimized
- ✅ No oversubscription
- ✅ Automatic task scheduling

---

## Resource Management

### Resource Lifecycle

```
1. DEFINITION
   ↓
   INTERLOCK element defines resource_id: "my_resource"
   
2. ACQUISITION
   ↓
   Process arrives at INTERLOCK
   → Check: Is lock available?
      ├─ YES → Acquire lock (increment counter)
      └─ NO  → Wait or timeout
   
3. USAGE
   ↓
   Process holds lock while executing
   → Protected resource access happens here
   
4. RELEASE
   ↓
   Process completes
   → Auto-release (if enabled) or manual release
   → Decrement counter
   → Notify waiting processes
```

### Multiple INTERLOCKs on Same Resource

**Multiple INTERLOCK elements can share the same `resource_id` to coordinate access:**

```
Process Flow 1:
  [INTERLOCK A] → resource_id: "db_pool"
         ↓
    Acquire slot 1/5

Process Flow 2:
  [INTERLOCK B] → resource_id: "db_pool"  (SAME RESOURCE!)
         ↓
    Acquire slot 2/5

Both INTERLOCKs coordinate access to the shared "db_pool" resource.
```

**Use Cases:**
- Different entry points to same resource
- Multiple workflows accessing shared infrastructure
- Coordination across process boundaries

**Validation:**
- ⚠️ WARNING when duplicate `resource_id` detected (informational only)

---

### Resource Naming Strategy

**Best Practices:**

1. **Be Descriptive**
   ```
   ✅ "postgres_connection_pool"
   ❌ "pool1"
   ```

2. **Include Resource Type**
   ```
   ✅ "api_external_weather"
   ❌ "weather"
   ```

3. **Use Consistent Naming**
   ```
   ✅ "file_write_config"
   ✅ "file_read_config"
   ❌ "config_file_write"
   ❌ "read_config_file"
   ```

4. **Avoid Ambiguity**
   ```
   ✅ "printer_hp_laserjet_01"
   ❌ "printer"
   ```

**Naming Patterns:**

| Pattern | Example | Use Case |
|---------|---------|----------|
| `{resource}_{location}` | `db_production` | Environment-specific |
| `{type}_{resource}` | `api_external_weather` | Type categorization |
| `{action}_{resource}` | `write_log_file` | Action-specific |
| `{resource}_{instance}` | `printer_01` | Multiple instances |

---

### Resource Contention Monitoring

**Key Metrics to Track:**

1. **Average Wait Time**
   ```
   If increasing → Consider increasing max_count or optimizing resource usage
   ```

2. **Timeout Rate**
   ```
   If > 5% → Resource is bottleneck, need capacity increase
   ```

3. **Lock Hold Duration**
   ```
   If increasing → Processes are taking longer, investigate why
   ```

4. **Queue Depth**
   ```
   If consistently high → Resource is undersized for workload
   ```

**Example Monitoring Setup:**
```
Resource: "db_pool" (max_count=5)

Metrics:
- Current holders: 5/5 (100% utilization)
- Waiting processes: 12 (queue depth)
- Average wait time: 8.5 seconds (increasing ⚠️)
- Timeout rate: 8% (above threshold ⚠️)

Action: Increase max_count to 8 or optimize query performance
```

---

## Deadlock Prevention

### What is Deadlock?

**Deadlock occurs when two or more processes wait for each other indefinitely:**

```
Process A holds Lock 1, wants Lock 2
Process B holds Lock 2, wants Lock 1

Result: Both wait forever ⚠️
```

### Deadlock Example

**BAD Process Design:**
```
Process Flow 1:
  [INTERLOCK A] resource: "db"   → Acquired
       ↓
  [INTERLOCK B] resource: "file" → WAIT (held by Flow 2)

Process Flow 2:
  [INTERLOCK C] resource: "file" → Acquired
       ↓
  [INTERLOCK D] resource: "db"   → WAIT (held by Flow 1)

DEADLOCK! Both flows wait forever.
```

---

### Prevention Strategies

#### 1. Lock Ordering

**Always acquire locks in the same order:**

```
✅ CORRECT:
Process Flow 1:
  [INTERLOCK] resource: "db"   (order 1)
  [INTERLOCK] resource: "file" (order 2)

Process Flow 2:
  [INTERLOCK] resource: "db"   (order 1)
  [INTERLOCK] resource: "file" (order 2)

Both flows acquire in same order → No deadlock possible
```

**Establish Global Lock Order:**
```
1. Database locks
2. File system locks
3. API locks
4. Hardware locks
```

---

#### 2. Use Timeouts

**Always configure `interlock_timeout` for multi-lock scenarios:**

```json
{
  "interlock_timeout": 30,
  "interlock_on_locked_target": "deadlock_recovery"
}
```

**Timeout breaks potential deadlocks:**
```
Process A holds Lock 1, wants Lock 2 → Timeout after 30s → Release Lock 1 → Retry
Process B gets Lock 1 → Completes → Releases both locks
Process A retries → Success
```

---

#### 3. Avoid Nested Locks

**Design processes to minimize lock nesting:**

```
❌ BAD (nested locks):
[INTERLOCK A] → [INTERLOCK B] → [INTERLOCK C] → Work

✅ GOOD (sequential locks):
[INTERLOCK A] → Work → Release
[INTERLOCK B] → Work → Release
[INTERLOCK C] → Work → Release
```

---

#### 4. Use Single Lock for Related Resources

**Combine related resources under one lock:**

```
❌ BAD (multiple locks):
[INTERLOCK A] resource: "db"
[INTERLOCK B] resource: "db_index"
[INTERLOCK C] resource: "db_cache"

✅ GOOD (single lock):
[INTERLOCK] resource: "db_subsystem" (covers all DB components)
```

---

#### 5. Implement Deadlock Detection

**Runtime detection pattern:**

```python
# Pseudocode
class DeadlockDetector:
    def check_cycle(lock_graph):
        # Build dependency graph of waiting processes
        # Detect cycles (A waits for B, B waits for A)
        if cycle_detected:
            # Break cycle by timing out oldest waiter
            oldest_waiter.timeout()
```

---

### Deadlock Recovery

**When deadlock is detected:**

1. **Timeout Oldest Request**
   ```
   Process with longest wait time gets timeout
   → Releases held locks
   → Other processes can proceed
   → Timed-out process retries later
   ```

2. **Priority-Based Preemption**
   ```
   Low-priority process holding lock
   → Forced to release lock
   → High-priority process acquires lock
   → Low-priority process retries
   ```

3. **Rollback and Retry**
   ```
   Process involved in deadlock
   → Rollback to last safe state
   → Release all locks
   → Retry with backoff delay
   ```

---

## Best Practices

### 1. Choose Appropriate Lock Type

```
Decision Matrix:

Resource can be safely shared?
  ├─ NO  → MUTEX
  │       - File writes
  │       - Database updates
  │       - Hardware exclusive access
  │
  └─ YES → SEMAPHORE
          - Read-only database queries
          - API rate limiting
          - Connection/thread pools
```

---

### 2. Always Configure Timeout

**Recommendation:** Always set `interlock_timeout > 0` except for truly indefinite waits.

```json
✅ GOOD:
{
  "interlock_timeout": 30,
  "interlock_on_locked_target": "timeout_handler"
}

⚠️ RISKY:
{
  "interlock_timeout": 0  // Waits forever
}
```

**Timeout Guidelines:**
- **Interactive processes:** 5-30 seconds
- **Background jobs:** 60-300 seconds
- **Batch processes:** 300-3600 seconds

---

### 3. Use Auto-Release by Default

**Keep `interlock_auto_release = true` unless you have specific reason:**

```json
✅ DEFAULT (recommended):
{
  "interlock_auto_release": true
}

⚠️ ADVANCED (requires manual release):
{
  "interlock_auto_release": false
  // Must implement explicit release logic!
}
```

**Manual release is only needed for:**
- Lock spans multiple process elements
- External system controls lock lifetime
- Complex multi-phase transactions

---

### 4. Monitor Lock Metrics

**Track these metrics for each resource:**

| Metric | Target | Action if Exceeded |
|--------|--------|-------------------|
| Average wait time | < 5 seconds | Increase max_count or optimize |
| Timeout rate | < 5% | Increase timeout or capacity |
| Lock hold duration | < 10 seconds | Optimize process logic |
| Queue depth | < 10 | Increase max_count |

---

### 5. Document Resource Constraints

**For each INTERLOCK, document:**

```yaml
Resource: "postgres_pool"
Type: SEMAPHORE
Max Count: 10
Reason: PostgreSQL max_connections = 100, reserve 90 for other apps
Shared By:
  - "customer_query_flow"
  - "order_processing_flow"
  - "reporting_flow"
Owner: Database Team
Contact: db-team@example.com
```

---

### 6. Test Under Load

**Stress test scenarios:**

1. **Capacity Test**
   ```
   Simulate max_count + 10 concurrent requests
   → Verify graceful queuing
   → Check timeout behavior
   ```

2. **Timeout Test**
   ```
   Hold lock artificially long
   → Verify timeout triggers
   → Check fallback routing works
   ```

3. **Deadlock Test**
   ```
   Create circular wait conditions
   → Verify timeout breaks deadlock
   → Check recovery behavior
   ```

---

### 7. Use Descriptive Names

**INTERLOCK element names should be clear:**

```
✅ GOOD:
- "DB Connection Pool Semaphore"
- "Config File Write Mutex"
- "API Rate Limit (10 req/sec)"

❌ BAD:
- "Lock 1"
- "Semaphore"
- "Interlock"
```

---

### 8. Plan for Failures

**Always define `on_locked_target` for production:**

```json
{
  "interlock_timeout": 30,
  "interlock_on_locked_target": "lock_timeout_handler"
}

// lock_timeout_handler element:
- Log timeout incident
- Notify monitoring
- Route to fallback logic
- OR add to retry queue
```

---

### 9. Minimize Lock Scope

**Hold locks for shortest time possible:**

```
❌ BAD (long lock):
[INTERLOCK] → Validate → Transform → Call API → Store Result → [Release]

✅ GOOD (short lock):
Validate → Transform → [INTERLOCK] → Call API → [Release] → Store Result
```

**Only protect the critical section that requires synchronization.**

---

### 10. Version Resource IDs

**For evolving systems, version resource identifiers:**

```
✅ VERSIONED:
- "db_pool_v1"
- "db_pool_v2"  (new connection limits)

Allows gradual migration:
- Old processes use "db_pool_v1"
- New processes use "db_pool_v2"
- Eventually retire "db_pool_v1"
```

---

## Validation Rules

The InterlockValidator enforces these rules:

### ERROR Level

| Rule | Description | Example |
|------|-------------|---------|
| **1. Resource-ID Required** | `interlock_resource_id` must not be empty | `""` → ERROR |
| **2. Type Valid** | `interlock_type` must be `MUTEX` or `SEMAPHORE` | `"INVALID"` → ERROR |
| **3. Max Count Positive** | `interlock_max_count` must be `> 0` | `0` → ERROR |
| **4. Timeout Non-Negative** | `interlock_timeout` must be `>= 0` | `-5` → ERROR |

### WARNING Level

| Rule | Description | Example |
|------|-------------|---------|
| **5. Target Exists** | `on_locked_target` must reference existing element | `"nonexistent"` → WARNING |
| **6. Duplicate Resource-ID** | Multiple INTERLOCKs with same resource_id (informational) | 2 with `"db"` → WARNING |
| **7. Timeout Without Fallback** | Timeout > 0 but no `on_locked_target` set | timeout=30, target="" → WARNING |
| **8. SEMAPHORE=1** | SEMAPHORE with max_count=1 behaves like MUTEX | SEMAPHORE, max=1 → WARNING |

### INFO Level

| Rule | Description | Example |
|------|-------------|---------|
| **9. Manual Release** | `auto_release=false` requires explicit release logic | auto_release=false → INFO |
| **10. MUTEX Max Count** | MUTEX with max_count != 1 is unusual | MUTEX, max=5 → INFO |

---

## Implementation Details

### Schema (VPBElement)

**File:** `vpb/models/element.py`

**Properties Added:**
```python
@dataclass
class VPBElement:
    # ... existing properties ...
    
    # INTERLOCK properties
    interlock_type: str = "MUTEX"
    interlock_resource_id: str = ""
    interlock_max_count: int = 1
    interlock_timeout: int = 0
    interlock_on_locked_target: str = ""
    interlock_auto_release: bool = True
```

**Serialization:**
```python
def to_dict(self):
    d = {
        # ... standard fields ...
    }
    
    # Conditional INTERLOCK serialization
    if self.element_type == "INTERLOCK":
        d["interlock_type"] = self.interlock_type
        d["interlock_resource_id"] = self.interlock_resource_id
        d["interlock_max_count"] = self.interlock_max_count
        d["interlock_timeout"] = self.interlock_timeout
        d["interlock_on_locked_target"] = self.interlock_on_locked_target
        d["interlock_auto_release"] = self.interlock_auto_release
    
    return d
```

---

### Palette (default_palette.json)

**File:** `palettes/default_palette.json`

**Definition:**
```json
{
  "id": "INTERLOCK",
  "name": "Sperre (Interlock)",
  "element_type": "INTERLOCK",
  "description": "Resource locking (MUTEX/SEMAPHORE)",
  "category": "Elemente – Logik",
  "shape": "rounded",
  "color": "#FFF3E0",
  "border_color": "#FF9800",
  "text_color": "#000000"
}
```

---

### Canvas Rendering (canvas.py)

**File:** `vpb/ui/canvas.py`

**Rendering Logic:**
```python
if el.element_type == "INTERLOCK":
    interlock_type = getattr(el, "interlock_type", "MUTEX")
    resource_id = getattr(el, "interlock_resource_id", "")
    max_count = getattr(el, "interlock_max_count", 1)
    
    # Choose icon
    type_icons = {"MUTEX": "🔒", "SEMAPHORE": "🔓"}
    icon = type_icons.get(interlock_type, "🔒")
    
    # Display text
    type_text = f"{icon} {interlock_type}"
    if interlock_type == "SEMAPHORE":
        type_text += f" Max: {max_count}"
    
    # Draw text
    self.canvas.create_text(
        text_x, text_y,
        text=type_text,
        font=("Arial", 10, "bold"),
        fill="black"
    )
    
    # Draw resource ID if set
    if resource_id:
        self.canvas.create_text(
            text_x, text_y + 15,
            text=f"Resource: {resource_id}",
            font=("Arial", 8),
            fill="#555555"
        )
```

---

### Properties Panel (properties_panel.py)

**File:** `vpb/ui/properties_panel.py`

**UI Section:**
```python
# INTERLOCK-Section
self.interlock_section = LabelFrame(
    frame, text="🔒 INTERLOCK-Properties", padx=10, pady=5
)

# Type Dropdown
self.interlock_type_combo = ttk.Combobox(
    self.interlock_section,
    values=["MUTEX", "SEMAPHORE"],
    state="readonly",
    width=15
)

# Resource-ID Entry
self.interlock_resource_id_entry = Entry(
    self.interlock_section, width=30
)

# Max Count Entry (numeric)
self.interlock_max_count_entry = Entry(
    self.interlock_section, width=10
)

# Timeout Entry (seconds)
self.interlock_timeout_entry = Entry(
    self.interlock_section, width=10
)

# On Locked Target Entry (Element-ID)
self.interlock_on_locked_target_entry = Entry(
    self.interlock_section, width=30
)

# Auto-Release Checkbox
self.interlock_auto_release_var = BooleanVar(value=True)
self.interlock_auto_release_check = Checkbutton(
    self.interlock_section,
    text="Auto-release after execution",
    variable=self.interlock_auto_release_var
)
```

---

### Validation (validation_service.py)

**File:** `vpb/services/validation_service.py`

**InterlockValidator Class:**
```python
class InterlockValidator:
    """Validiert INTERLOCK-Elemente (Mutex/Semaphore)."""
    
    VALID_TYPES = ["MUTEX", "SEMAPHORE"]
    
    def validate_interlock(self, element, doc, result):
        # Rule 1: Resource-ID not empty [ERROR]
        resource_id = getattr(element, "interlock_resource_id", "").strip()
        if not resource_id:
            result.add_error(...)
        
        # Rule 2: Type valid [ERROR]
        interlock_type = getattr(element, "interlock_type", "MUTEX")
        if interlock_type not in self.VALID_TYPES:
            result.add_error(...)
        
        # Rule 3: Max-Count > 0 [ERROR]
        max_count = getattr(element, "interlock_max_count", 1)
        if max_count <= 0:
            result.add_error(...)
        
        # Rule 4: Timeout >= 0 [ERROR]
        timeout = getattr(element, "interlock_timeout", 0)
        if timeout < 0:
            result.add_error(...)
        
        # Rule 5: Locked-Target exists [WARNING]
        locked_target = getattr(element, "interlock_on_locked_target", "").strip()
        if locked_target:
            target_element = doc.get_element(locked_target)
            if not target_element:
                result.add_warning(...)
        
        # ... additional rules ...
```

---

## API Reference

### Element Creation

```python
from vpb.models.element import VPBElement

# Create MUTEX
mutex = VPBElement(
    element_id="lock_1",
    element_type="INTERLOCK",
    name="DB Write Lock",
    x=100, y=100
)
mutex.interlock_type = "MUTEX"
mutex.interlock_resource_id = "db_connection"
mutex.interlock_max_count = 1
mutex.interlock_timeout = 30
mutex.interlock_on_locked_target = "timeout_handler"
mutex.interlock_auto_release = True

# Create SEMAPHORE
semaphore = VPBElement(
    element_id="lock_2",
    element_type="INTERLOCK",
    name="API Rate Limit",
    x=250, y=100
)
semaphore.interlock_type = "SEMAPHORE"
semaphore.interlock_resource_id = "external_api"
semaphore.interlock_max_count = 10
semaphore.interlock_timeout = 60
semaphore.interlock_on_locked_target = "api_throttled"
semaphore.interlock_auto_release = True
```

---

### Serialization

```python
# To JSON
interlock_dict = mutex.to_dict()
# {
#   "element_id": "lock_1",
#   "element_type": "INTERLOCK",
#   "name": "DB Write Lock",
#   "interlock_type": "MUTEX",
#   "interlock_resource_id": "db_connection",
#   "interlock_max_count": 1,
#   "interlock_timeout": 30,
#   "interlock_on_locked_target": "timeout_handler",
#   "interlock_auto_release": true
# }

# From JSON
interlock = VPBElement.from_dict(interlock_dict)
```

---

### Validation

```python
from vpb.services.validation_service import InterlockValidator, ValidationResult
from vpb.models.document import DocumentModel

# Create document
doc = DocumentModel()
doc.add_element(mutex)

# Validate
validator = InterlockValidator()
result = ValidationResult()
validator.validate_interlock(mutex, doc, result)

# Check results
if result.errors:
    print("Errors:", [e.message for e in result.errors])
if result.warnings:
    print("Warnings:", [w.message for w in result.warnings])
```

---

### Programmatic Configuration

```python
# Configure MUTEX
def create_db_mutex():
    lock = VPBElement(
        element_id=f"db_lock_{uuid.uuid4()}",
        element_type="INTERLOCK",
        name="Database Mutex",
        x=100, y=100
    )
    lock.interlock_type = "MUTEX"
    lock.interlock_resource_id = "postgres_main"
    lock.interlock_max_count = 1
    lock.interlock_timeout = 30
    lock.interlock_on_locked_target = "db_timeout"
    lock.interlock_auto_release = True
    return lock

# Configure SEMAPHORE
def create_api_semaphore(max_requests=10):
    lock = VPBElement(
        element_id=f"api_lock_{uuid.uuid4()}",
        element_type="INTERLOCK",
        name=f"API Semaphore ({max_requests})",
        x=250, y=100
    )
    lock.interlock_type = "SEMAPHORE"
    lock.interlock_resource_id = "external_api_v1"
    lock.interlock_max_count = max_requests
    lock.interlock_timeout = 60
    lock.interlock_on_locked_target = "api_overload"
    lock.interlock_auto_release = True
    return lock
```

---

## FAQ

### Q1: When should I use MUTEX vs SEMAPHORE?

**A:** Use **MUTEX** when the resource cannot be safely shared (e.g., file writes, database updates). Use **SEMAPHORE** when limited concurrent access is safe (e.g., read-only queries, API rate limits).

---

### Q2: Can multiple INTERLOCK elements share the same resource_id?

**A:** Yes! This is intentional and correct. Multiple INTERLOCK elements with the same `resource_id` coordinate access to the same logical resource. Example: Different process flows all accessing "db_pool".

---

### Q3: What happens if timeout is 0?

**A:** The process waits **indefinitely** until the lock becomes available. Use with caution - can cause hangs if lock is never released.

---

### Q4: Should I always enable auto_release?

**A:** Yes, unless you have a specific reason not to. Manual release (`auto_release=false`) requires explicit release logic and is error-prone.

---

### Q5: How do I prevent deadlocks?

**A:** Follow these rules:
1. Always acquire locks in the same order
2. Use timeouts on all locks
3. Minimize lock nesting
4. Keep lock hold time short
5. Test under concurrent load

---

### Q6: What's the difference between INTERLOCK and CONDITION?

**A:** **CONDITION** evaluates expressions and branches based on results. **INTERLOCK** coordinates resource access across concurrent processes. Use CONDITION for business logic, INTERLOCK for resource synchronization.

---

### Q7: Can I change max_count at runtime?

**A:** No, `max_count` is static configuration. To change capacity, you must update the INTERLOCK element and reload the process.

---

### Q8: What happens when on_locked_target doesn't exist?

**A:** Validation produces a **WARNING** (not an error). The process will fail at runtime when trying to route to the non-existent target.

---

### Q9: How do I monitor INTERLOCK performance?

**A:** Track these metrics:
- Average wait time per resource
- Timeout rate
- Lock hold duration
- Queue depth
- Utilization (current holders / max_count)

Implement logging in process execution to capture these metrics.

---

### Q10: Can SEMAPHORE have max_count = 1?

**A:** Technically yes, but validation produces a **WARNING** because it's equivalent to MUTEX. Use MUTEX type instead for clarity.

---

### Q11: What's the recommended timeout value?

**A:** Depends on context:
- **Interactive:** 5-30 seconds
- **Background:** 60-300 seconds
- **Batch:** 300-3600 seconds

Always set timeout > 0 to prevent indefinite hangs.

---

### Q12: How do I implement manual release?

**A:** Set `auto_release=false` and add explicit release logic:
```python
# Pseudocode
acquire_lock("my_resource")
try:
    # Do work
    process_data()
finally:
    # Always release in finally block
    release_lock("my_resource")
```

---

### Q13: Can I nest INTERLOCKs?

**A:** Yes, but it increases deadlock risk. Always acquire in consistent order and use timeouts.

---

### Q14: What happens if a process crashes while holding a lock?

**A:** This depends on runtime implementation. Best practice: Use timeouts and monitoring to detect and recover from stuck locks.

---

### Q15: How many concurrent processes can wait for a lock?

**A:** Unlimited. INTERLOCK queues all waiting processes. Monitor queue depth to identify capacity issues.

---

## Roadmap

### v1.0 (Current - Released) ✅

- ✅ MUTEX and SEMAPHORE support
- ✅ Resource-ID based coordination
- ✅ Timeout configuration
- ✅ Fallback routing (on_locked_target)
- ✅ Auto-release mechanism
- ✅ Comprehensive validation (9 rules)
- ✅ Canvas rendering with icons
- ✅ Properties panel UI
- ✅ Full documentation

---

### v1.1 (Planned)

**Priority-Based Locking**
- Assign priorities to processes
- High-priority processes acquire locks first
- Preemption support (force lower-priority release)

**Lock Metrics Dashboard**
- Real-time monitoring of lock utilization
- Queue depth visualization
- Timeout statistics
- Deadlock detection alerts

**Advanced Timeout Strategies**
- Exponential backoff
- Progressive timeout (increase on retries)
- Smart retry scheduling

---

### v1.2 (Future)

**Read/Write Locks**
- Separate read and write locks
- Multiple readers OR single writer
- Better throughput for read-heavy workloads

**Distributed Locking**
- Cross-server lock coordination
- Redis/etcd backend support
- Fault-tolerant lock management

**Lock Hierarchies**
- Parent-child lock relationships
- Automatic acquisition order enforcement
- Hierarchical deadlock prevention

---

### v2.0 (Long-term)

**Adaptive Locking**
- ML-based lock optimization
- Dynamic max_count adjustment
- Predictive queueing

**Lock Composition**
- Combine multiple locks (AND/OR)
- Complex coordination patterns
- Transaction-style lock sets

**Blockchain Integration**
- Immutable lock audit trail
- Distributed consensus locking
- Smart contract integration

---

## Summary

The **INTERLOCK** element is a powerful tool for coordinating access to shared resources in VPB workflows:

✅ **Two Lock Types:** MUTEX (exclusive) and SEMAPHORE (limited concurrent)  
✅ **Resource Coordination:** Multiple INTERLOCKs share resource_id  
✅ **Timeout Protection:** Configurable wait times with fallback routing  
✅ **Automatic Management:** Auto-release simplifies usage  
✅ **Comprehensive Validation:** 9 rules ensure correct configuration  
✅ **Production Ready:** Tested and documented

**Key Takeaways:**
1. Use MUTEX for exclusive access, SEMAPHORE for limited sharing
2. Always configure timeouts to prevent indefinite waits
3. Follow lock ordering to prevent deadlocks
4. Monitor lock metrics to optimize capacity
5. Keep lock hold time minimal

**Next Steps:**
- Review the [Usage Examples](#usage-examples) for your use case
- Follow [Best Practices](#best-practices) for production deployment
- Implement [Deadlock Prevention](#deadlock-prevention) strategies
- Monitor with recommended metrics

For questions or issues, refer to the [FAQ](#faq) or contact the VPB team.

---

**Document Version:** 1.0  
**Last Updated:** October 18, 2025  
**Authors:** VPB Development Team  
**Status:** ✅ Released
