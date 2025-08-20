# Doing

## Goal: Operator Oto can activate a potting lot and all the systems and people know what should be done

## Refined Stories

### Core Activation Features

- **Lot Activation**: Operator can activate a lot from the potting list with an "Activeren" button
- **Active Lot Display**: The currently active lot shows prominently at the top of the page for each line
- **Machine Integration**: The active lot number is written to the de-stacking machine through OPC/UA
- **Active Lot Details**: The operator can click on the active lot to display a details page

### Active Lot Details Page

- **Deactivation**: A "Deactiveren" button that deactivates the lot
- **Lot Information**: Complete potting details of the lot (ID, name, bulb code, etc.)
- **Process Completion**: A "Oppotten Voltooid" button that:
  - Requires entering the actual number of potted plants
  - Marks the potting process step as done
  - Automatically deactivates the lot after completion

### Business Rules

- **Two Potting Lines**: Line 1 and Line 2 operate independently
- **Single Active Lot per Line**: There can only be one active lot at a time per line
- **Cross-Line Activation**: The same lot can be active on both lines simultaneously
- **Automatic Deactivation**: Activating a new lot automatically deactivates the previously active lot on that line

## Design

### Data Model

#### Active Potting Lot Model

```python
from pydantic import BaseModel

class ActivePottingLot(BaseModel):
    """Runtime state for tracking active potting lots per line."""
    
    line: int  # Potting line number (1 or 2)
    potting_lot_id: int  # ID of the active potting lot
    potting_lot: PottingLot  # Full potting lot details for display
```

### Repository Extensions

#### ActivePottingLotService

```python
class ActivePottingLotService:
    """In-memory service for managing active potting lots."""
    
    def __init__(self, potting_lot_repository: PottingLotRepository):
        self._active_lots: Dict[int, ActivePottingLot] = {}  # line -> active lot
        self._potting_lot_repository = potting_lot_repository
    
    def activate_lot(self, line: int, potting_lot_id: int) -> ActivePottingLot:
        """Activate a lot on a specific line. Deactivates any previously active lot on that line."""
        
    def deactivate_lot(self, line: int) -> bool:
        """Deactivate the currently active lot on a specific line."""
        
    def get_active_lot_for_line(self, line: int) -> Optional[ActivePottingLot]:
        """Get the currently active lot for a specific line."""
        
    def get_all_active_lots(self) -> List[ActivePottingLot]:
        """Get all currently active lots across all lines."""
        
    def complete_lot(self, line: int, actual_pots: int) -> bool:
        """Mark the active lot as completed and deactivate it."""
```

### User Interface Changes

#### Enhanced Potting Lots List Page

1. **Line Selection Tabs**: Tabs for "Lijn 1" and "Lijn 2" at the top
1. **Active Lot Header**: Prominent display of currently active lot for selected line
1. **Activation Buttons**: "Activeren" button in row actions for each lot
1. **Visual Status**: Different styling for active lots in the table

#### New Active Lot Details Page (`/potting-lots/active/{line}`)

1. **Lot Information Card**: Complete details of the active lot
1. **Action Buttons**:
   - "Deactiveren" (red button)
   - "Oppotten Voltooid" (green button)
1. **Completion Form**: Modal for entering actual pot count

#### Enhanced Lot Detail Page

- Show activation status and history
- Display completion information if available

### Integration Points

#### OPC/UA Communication

- Service class `PottingLineController` for machine communication
- Method `send_active_lot_to_machine(line: int, lot_id: int)`
- Error handling and retry logic for connection issues

#### Navigation Flow

1. **List Page** → Activate → **Active Lot Details**
1. **Active Lot Header** → Click → **Active Lot Details**
1. **Active Lot Details** → Complete/Deactivate → **List Page**

### Technical Implementation

#### Step 1: Basic Lot Activation (Minimal Viable Feature) - ✅ COMPLETED

**Goal**: Operator can activate one lot at a time (single line, no UI tabs yet)

**Data Layer**:

- ✅ Create `ActivePottingLot` Pydantic model
- ✅ Create `ActivePottingLotService` with in-memory storage
- ✅ Add service to dependency injection

**UI Changes**:

- ✅ Add "Activeren" button to potting lots popup (eye icon)
- ✅ Show currently active lot in header above the table (both lines)
- ✅ Add activation/deactivation handlers with reactive UI updates
- ✅ Use NiceGUI reactive patterns instead of page reloads

**Tests**:

- ✅ Test model creation and validation
- ✅ Test service activation/deactivation logic
- ✅ UI tests created but need test data setup refinement

**Code improvements**

- ✅ Use a bindable property for the service state to propagate changes correctly across tabs
- ❌ use app.storage instead of a global service variable  
- ✅ fix the UI unit tests
- review code

**User Value**: ✅ Operator can activate a lot via popup and see which lot is currently active on each line with deactivation buttons

**Implementation Notes**:

- Uses global service instances for state management
- Popup shows activation buttons at top, then lot details
- Header shows active lots for both lines with individual deactivation
- Reactive UI updates without page reloads
- **ENHANCED**: Uses NiceGUI bindable properties for automatic cross-tab synchronization
- **SIMPLIFIED**: Direct binding to dictionary eliminates complex callback chains and container clearing
- **FIXED**: Restored working activation/deactivation functionality with proper binding

#### Step 2: Dual Line Support

**Goal**: ✅ Support independent operation of Line 1 and Line 2

**Data Layer**:

- Extend service to handle line parameter (1 or 2)
- Add validation for line numbers

**UI Changes**:

- ✅ Add line selection tabs ("Lijn 1" and "Lijn 2")
- ✅ Show active lot header per selected line
- ✅ Update activation button to activate on specific line

**Tests**:

- ✅ Test independent line operation
- ✅ Test same lot can be active on both lines
- ✅ Test UI tab switching and line-specific activation

**User Value**: Operators can manage both potting lines independently

#### Step 3: Active Lot Details Page

**Goal**: Dedicated page for managing the active lot with deactivation

**Data Layer**:

- No changes needed (existing service supports this)

**UI Changes**:

- Create `/potting-lots/active/{line}` route
- Add clickable active lot header that navigates to details page
- Create active lot details page with lot information and "Deactiveren" button
- Add navigation back to main list

**Tests**:

- Test active lot details page renders correctly
- Test deactivation button works
- Test navigation between pages

**User Value**: Operator has dedicated workspace for active lot with easy deactivation

#### Step 4: Process Completion Workflow

**Goal**: Mark potting as completed with actual pot count

**Data Layer**:

- Add completion method to service
- Track completion state (for future audit/reporting)

**UI Changes**:

- Add "Oppotten Voltooid" button to active lot details page
- Create completion modal form for entering actual pot count
- Auto-deactivate lot after completion
- Show completion confirmation

**Tests**:

- Test completion workflow end-to-end
- Test actual pot count validation
- Test auto-deactivation after completion

**User Value**: Operator can properly complete potting process with actual counts

#### Step 5: Machine Integration (OPC/UA)

**Goal**: Send active lot information to de-stacking machine

**Data Layer**:

- Create `PottingLineController` service for OPC/UA communication
- Integrate with activation/deactivation workflow

**UI Changes**:

- Add connection status indicator
- Show machine communication errors in notifications
- Add manual retry option if communication fails

**Tests**:

- Test OPC/UA service integration
- Test error handling for communication failures
- Test manual retry functionality

**User Value**: Machine automatically knows which lot is active, reducing manual setup

#### Step 6: Enhanced Visual Feedback

**Goal**: Better visual indicators for active lots and process status

**Data Layer**:

- No changes needed

**UI Changes**:

- Highlight active lots in the main table with different styling
- Add status indicators (active, completed)
- Improve visual hierarchy of active lot header
- Add progress indicators during activation/completion

**Tests**:

- Test visual styling for active lots
- Test status indicators display correctly
- Test UI responsiveness during operations

**User Value**: Clearer visual feedback makes it easier to understand current state
