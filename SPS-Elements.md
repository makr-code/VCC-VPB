# SPS Elements / SPS-Elemente

**Version:** 0.5.0  
**Status:** Implemented / Implementiert

---

## Overview / Übersicht

VPB supports SPS (Speicherprogrammierbare Steuerung / Programmable Logic Controller) elements for process modeling.

VPB unterstützt SPS-Elemente für die Prozessmodellierung.

---

## Available Elements / Verfügbare Elemente

### 1. COUNTER - Zähler

**Purpose / Zweck:**  
Counting events, cycles, or occurrences with configurable limits.  
Zählen von Ereignissen, Zyklen oder Vorkommnissen mit konfigurierbaren Grenzwerten.

**Key Features:**
- Up/Down counting
- Minimum and maximum limits
- Reset capability
- Overflow detection

**[[Counter-Element]]** - Detailed documentation

---

### 2. CONDITION - Bedingung

**Purpose / Zweck:**  
Conditional branching based on logical expressions.  
Bedingte Verzweigung basierend auf logischen Ausdrücken.

**Key Features:**
- Boolean logic (AND, OR, NOT)
- Comparison operators
- Multiple outputs
- Nested conditions

**[[Condition-Element]]** - Detailed documentation

---

### 3. ERROR_HANDLER - Fehlerbehandlung

**Purpose / Zweck:**  
Error detection, handling, and recovery mechanisms.  
Fehlererkennung, -behandlung und Wiederherstellungsmechanismen.

**Key Features:**
- Error type detection
- Retry logic
- Fallback actions
- Error logging

**[[Error-Handler-Element]]** - Detailed documentation

---

### 4. STATE - Zustand

**Purpose / Zweck:**  
State machine implementation with transitions.  
Zustandsmaschinen-Implementierung mit Übergängen.

**Key Features:**
- Multiple states
- Transition conditions
- Entry/exit actions
- State history

**[[State-Element]]** - Detailed documentation

---

### 5. INTERLOCK - Verriegelung

**Purpose / Zweck:**  
Safety interlocks and mutual exclusion.  
Sicherheitsverriegelungen und gegenseitiger Ausschluss.

**Key Features:**
- Safety conditions
- Lock/unlock logic
- Priority handling
- Timeout protection

**[[Interlock-Element]]** - Detailed documentation

---

## Element Comparison / Elementvergleich

| Element | Use Case | Complexity | Common Usage |
|---------|----------|------------|--------------|
| **COUNTER** | Counting events | Low | Iteration limits, quotas |
| **CONDITION** | Decision making | Medium | Branching, routing |
| **ERROR_HANDLER** | Error management | Medium | Fault tolerance |
| **STATE** | State tracking | High | Workflows, processes |
| **INTERLOCK** | Safety locks | Medium | Resource protection |

---

## Common Properties / Gemeinsame Eigenschaften

All SPS elements share these base properties:

### Basic Properties
- **ID** - Unique identifier
- **Name** - Display name
- **Description** - Element description
- **Type** - Element type
- **Position** - Canvas position (x, y)

### Connection Points
- **Inputs** - Input connections
- **Outputs** - Output connections
- **Error Output** - Error handling connection

### Validation
- **Required** - Mandatory properties
- **Validation Rules** - Type-specific rules
- **Error Messages** - Validation feedback

---

## Using SPS Elements / SPS-Elemente verwenden

### Adding to Process / Zum Prozess hinzufügen

1. **From Palette:**
   - Drag element from "SPS Elements" category
   - Drop on canvas

2. **Configure Properties:**
   - Select element
   - Edit in properties panel
   - Set required values

3. **Connect:**
   - Connect inputs from previous elements
   - Connect outputs to next elements
   - Optional: Connect error output

### Best Practices / Bewährte Praktiken

**1. Clear Naming**
```
✅ Good: "OrderCountExceeded"
❌ Bad: "Counter1"
```

**2. Document Logic**
- Add descriptions to complex elements
- Comment non-obvious conditions

**3. Error Handling**
- Always connect error outputs
- Implement fallback logic
- Log errors appropriately

**4. Validation**
- Test edge cases
- Validate limits
- Check boundary conditions

---

## Element Patterns / Element-Muster

### Pattern 1: Counter with Condition

```
[COUNTER] → [CONDITION] → [Action if limit reached]
    ↓
[Continue if below limit]
```

**Use Case:** Process with iteration limit

---

### Pattern 2: State Machine with Error Handler

```
[STATE] → [ERROR_HANDLER] → [Recovery State]
   ↓
[Normal Flow]
```

**Use Case:** Workflow with fault tolerance

---

### Pattern 3: Interlock Protection

```
[Check Resource] → [INTERLOCK] → [Use Resource]
                        ↓
                   [Resource Busy]
```

**Use Case:** Resource contention management

---

## Examples / Beispiele

### Simple Counter Example

**Scenario:** Approve up to 3 requests, then escalate

```
Start → [COUNTER: max=3] → [CONDITION: count < 3?]
                                    ↓ YES        ↓ NO
                              [Approve]    [Escalate]
```

**Properties:**
- Counter initial value: 0
- Counter max: 3
- Condition: `counter.value < 3`

### State Machine Example

**Scenario:** Order processing workflow

```
[STATE: New] → [STATE: Processing] → [STATE: Shipped] → [STATE: Delivered]
     ↓ ERROR            ↓ ERROR
[STATE: Cancelled]  [STATE: Failed]
```

**States:**
- New (initial)
- Processing
- Shipped
- Delivered
- Cancelled (error state)
- Failed (error state)

**More Examples:** [[Examples]]

---

## Element Reference / Element-Referenz

### Detailed Documentation

Each element has comprehensive documentation:

- **[[Counter-Element]]**
  - Properties reference
  - Configuration examples
  - Validation rules
  - Common patterns

- **[[Condition-Element]]**
  - Logic operators
  - Expression syntax
  - Boolean algebra
  - Testing conditions

- **[[Error-Handler-Element]]**
  - Error types
  - Recovery strategies
  - Retry logic
  - Logging

- **[[State-Element]]**
  - State definitions
  - Transitions
  - Actions
  - State diagrams

- **[[Interlock-Element]]**
  - Lock mechanisms
  - Priority rules
  - Timeout handling
  - Safety features

---

## Implementation Status / Implementierungsstatus

| Element | Implemented | Tested | Documented |
|---------|-------------|--------|------------|
| COUNTER | ✅ | ✅ | ✅ |
| CONDITION | ✅ | ✅ | ✅ |
| ERROR_HANDLER | ✅ | ✅ | ✅ |
| STATE | ✅ | ✅ | ✅ |
| INTERLOCK | ✅ | ✅ | ✅ |

**Verification:** All elements are fully implemented and tested as of v0.5.0

---

## Testing SPS Elements / SPS-Elemente testen

### Validation

Run process validation to check:
- Property completeness
- Connection validity
- Logic correctness
- Type compatibility

### Testing in Designer

1. Create test process
2. Configure element
3. Run validation (F5)
4. Check results

### Unit Tests

See test files in repository:
- `test_counter_element.py`
- `test_condition_element.py`
- `test_counter_validation.py`

**Developer Guide:** [[Testing]]

---

## Advanced Topics / Erweiterte Themen

### Custom Elements

Learn how to create custom SPS elements:
- **[[Extension-Development]]**

### Element Templates

Save configured elements as templates:
1. Configure element
2. Right-click → "Save as Template"
3. Reuse in future processes

### Scripting

Script element behavior:
- Python expressions
- Custom validators
- Event handlers

---

## Related Documentation

- **[[User-Guide]]** - Using elements in processes
- **[[Examples]]** - Example processes
- **[[API-Reference]]** - Programmatic access
- **[[Development-Guide]]** - Creating custom elements

---

[[Home]] | [[User-Guide]] | [[Examples]]
