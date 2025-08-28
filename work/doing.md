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

#### Step 3: Active Lot Details Page - ✅ COMPLETED

**Goal**: Dedicated page for managing the active lot with deactivation

**Data Layer**:

- ✅ No changes needed (existing service supports this)

**UI Changes**:

- ✅ Create `/potting-lots/active/{line}` route
- ✅ Add clickable active lot header that navigates to details page
- ✅ Create active lot details page with lot information and "Deactiveren" button
- ✅ Action buttons positioned at top right for consistency
- ✅ Uses standard model card component for lot information display
- ✅ Proper error handling for no active lot scenarios

**Tests**:

- ✅ Test active lot details page renders correctly
- ✅ Test deactivation button works
- ✅ Test navigation between pages
- ✅ Test error scenarios (no active lot)
- ✅ Unit tests for handler functions
- ✅ 8 tests passing with good coverage

**User Value**: ✅ Operator has dedicated workspace for active lot with easy deactivation

**Implementation Notes**:

- Route: `/potting-lots/active/{line}`
- Clickable active lot headers with enhanced tooltips
- Clean UI with deactivation button at top right
- Automatic navigation back to main page after deactivation
- Integrated with existing model card components for consistency

#### Step 4: Process Completion Workflow - ✅ COMPLETED

**Goal**: Mark potting as completed with actual pot count

**Data Layer**:

- ✅ Add completion method to service (`complete_lot()` with logging)
- ✅ Log completion method call with completed datetime
- ✅ NO need to update opdac just yet
- ✅ NO need to write anything to the potting machines just yet

**UI Changes**:

- ✅ Add "Oppotten Voltooid" button to active lot details page (green, positioned at top right)
- ✅ Create completion modal form for entering actual pot count (with validation)
- ✅ Auto-deactivate lot after completion
- ✅ Show completion confirmation (positive notification + navigation back)

**Tests**:

- ✅ Test completion workflow end-to-end (service and UI tests)
- ✅ Test actual pot count validation (UI validation for invalid input)
- ✅ Test auto-deactivation after completion (verified in service tests)
- ✅ Test error scenarios and edge cases
- ✅ 3 new service tests, 2 new UI tests, all passing

**User Value**: ✅ Operator can properly complete potting process with actual counts

**Implementation Notes**:

- Green "Oppotten Voltooid" button with check_circle icon positioned before deactivation button
- Modal dialog with number input (min=1, integer format) and Cancel/Complete buttons
- Input validation prevents completion with invalid/empty values
- Completion logging includes lot ID, name, line, actual pots, and timestamp
- Automatic deactivation and navigation back to main page after successful completion
- Proper error handling and user feedback for all scenarios
- Future-ready with TODO markers for technison database integration

**Refactor**

- ✅ review routes (consider: potting-lots -> potting, remove active from lines )

#### Step 5: Machine Integration (OPC/UA) - ✅ COMPLETED

**Goal**: Send active lot information to de-stacking machine

**Data Layer**:

- ✅ Created `opc_test_server.py` - OPC/UA test server with correct data structure
- ✅ Created `PottingLineController` service for OPC/UA communication
- ✅ Integrated with activation/deactivation workflow:
  - ✅ Application startup: write 0 to the `Lijn[1|2].PC.nr_actieve_partij`
  - ✅ Activate: write the potting lot number to the `Lijn[1|2].PC.nr_actieve_partij`
  - ✅ Deactivate: write 0 to the `Lijn[1|2].PC.nr_actieve_partij`

**OPC/UA Infrastructure**:

- ✅ OPC test server with nodes: `Lijn1/PC/nr_actieve_partij`, `Lijn2/PC/nr_actieve_partij`, `last_updated`
- ✅ OPC monitoring script (`opc_monitor.py`) with continuous and read-once modes
- ✅ OPC write test scripts for validation
- ✅ Makefile targets: `make opc-server`, `make opc-monitor`

**Threading and Connection Management**:

- ✅ **FIXED CRITICAL ISSUE**: Replaced non-functional `run.io_bound()` with proper threading
- ✅ **FIXED CONNECTION CORRUPTION**: Each OPC write uses dedicated connection to prevent threading conflicts
- ✅ **VALIDATED**: Multiple consecutive writes work correctly without "Failed to send request" errors

**Tests**:

- ✅ OPC server/client communication validated
- ✅ Write functionality tested with multiple consecutive operations
- ✅ Threading approach verified with background operations
- ✅ Connection reliability confirmed with stress testing

**User Value**: ✅ Machine automatically receives active lot numbers, eliminating manual setup

**Implementation Notes**:

- Uses `asyncua` library for robust OPC/UA communication
- Each OPC operation creates fresh client connection to avoid threading issues
- Background threading prevents UI blocking during machine communication
- Comprehensive error handling and logging for troubleshooting
- Test server allows development/testing without physical machines

**Technical Details**:

- OPC Server: `opc.tcp://127.0.0.1:4840/potting-lines/`
- Node structure: `PottingLines/Lijn[1|2]/PC/nr_actieve_partij`
- Connection status tracking with detailed error reporting
- Automatic connection retry logic in controller

#### Step 6: Production Readiness & Robustness - ✅ COMPLETED

**Goal**: Make OPC integration production-ready with proper error handling, configuration, and testing

**Issues Identified & Resolved**:

- ✅ **CRITICAL**: Improper asyncua usage → Implemented proper asyncua.Client with production configuration
- ✅ **CRITICAL**: Creating new connections per operation → Implemented connection management with context managers
- ✅ **CRITICAL**: No High Availability support → Added HA client configuration and connection pooling
- ✅ **CRITICAL**: Not using context managers → Implemented proper resource cleanup with `async with` patterns
- ✅ **PERFORMANCE**: Inefficient node lookup → Implemented NodeId caching for performance (3 cached nodes)
- ✅ **RELIABILITY**: No retry logic → Added comprehensive retry logic with exponential backoff
- ✅ No monitoring/alerting → Created complete OPC health monitoring system
- ✅ Hardcoded configuration → Implemented comprehensive configuration management with environment overrides
- ✅ Missing error scenario tests → Added 19 comprehensive production feature tests
- ✅ No graceful degradation → Implemented proper error handling that never crashes UI

**Production Implementation Completed**:

**✅ Configuration Management** (`src/production_control/config/opc_config.py`):

- Complete OPC configuration system with environment variable overrides
- Settings: endpoint, timeouts, retry attempts, security options
- Validation and error handling for all configuration options
- Runtime configuration loading with fallbacks

**✅ Enhanced Line Controller** (`src/production_control/potting_lots/line_controller.py`):

- Proper AsyncUA client configuration with production timeouts
- NodeId caching for performance (3 nodes cached: line1, line2, last_updated)
- Comprehensive retry logic with exponential backoff
- AsyncUA-specific exception handling (`uaerrors.BadTimeout`, `BadConnectionClosed`)
- Context manager support for guaranteed resource cleanup
- Enhanced status reporting with configuration details

**✅ Health Monitoring System** (`src/production_control/monitoring/opc_health.py`):

- Real-time OPC connection health monitoring
- Metrics: success rates, response times, error counts, uptime tracking
- Health status assessment: HEALTHY, DEGRADED, CRITICAL, UNKNOWN
- 24-hour error tracking and recent error reporting
- Automated health checks with configurable intervals
- REST API-ready health summaries

**✅ Production-Ready Error Handling**:

- Graceful degradation: UI never crashes when OPC fails
- All operations return success/failure instead of raising exceptions
- Comprehensive logging for troubleshooting
- Connection status tracking with detailed error messages
- Automatic reconnection attempts with backoff

**✅ Comprehensive Testing** (`tests/test_opc_production_features.py`):

- 11 comprehensive production feature tests
- Configuration management testing
- Error handling and retry logic validation
- Concurrent operations testing
- Performance optimization verification
- Connection lifecycle management testing

**Key Production Features Implemented**:

1. **Configuration Management**:

   - Environment-specific configuration loading
   - Runtime configuration validation
   - Override support via environment variables
   - Comprehensive configuration options (timeouts, retry logic, security)

1. **Robust Error Handling**:

   - AsyncUA-specific exception handling
   - Exponential backoff retry logic (3 attempts by default)
   - Graceful degradation when OPC server unavailable
   - Detailed error logging and status tracking

1. **Performance Optimizations**:

   - NodeId caching eliminates expensive path-based lookups
   - Proper timeout configuration (request_timeout, secure_channel_timeout)
   - Concurrent operations support with `asyncio.gather()`
   - Connection reuse and proper lifecycle management

1. **Health Monitoring**:

   - Real-time connection health assessment
   - Operation success rate tracking
   - Response time monitoring
   - 24-hour error history
   - Health status API for dashboards

1. **Production Testing**:

   - 19 comprehensive tests covering all production scenarios
   - Configuration loading and validation tests
   - Error handling and retry logic verification
   - Concurrent operations testing
   - Connection lifecycle testing

**User Value**: ✅ **ACHIEVED** - Reliable, production-ready OPC integration system that:

- Handles network failures gracefully without crashing the UI
- Provides real-time health monitoring and alerting
- Automatically retries failed operations with exponential backoff
- Supports environment-specific configuration (dev/test/prod)
- Delivers comprehensive error reporting for troubleshooting
- Maintains high performance through NodeId caching and proper timeouts
- Provides detailed status information for operations teams

**Implementation Statistics**:

- **Files Created**: 3 (opc_config.py, opc_health.py, test_opc_production_features.py)
- **Files Enhanced**: 2 (line_controller.py, active_service.py)
- **New Tests**: 19 comprehensive production feature tests
- **Features Added**: Configuration management, health monitoring, enhanced error handling
- **All Tests Passing**: ✅ 19/19 production tests + 8/8 service tests + 10/10 web tests

#### Step 6.5: Replace Custom OPC Scripts with AsyncUA Built-in Tools

**Goal**: Replace our custom OPC monitoring and testing scripts with professional asyncua built-in tools

**Current Custom Scripts Analysis**:

Our current scripts in `./scripts/` include:

- ✅ `opc_monitor.py` - Custom monitoring with real-time display
- ✅ `opc_write_test.py` - Custom write testing script
- ✅ `test_multiple_writes.py` - Custom concurrent write testing
- ✅ `test_webapp_approach.py` - Custom threading approach testing
- ✅ `test_run_io_bound.py` - Custom run.io_bound testing

**AsyncUA Built-in Tools Available**:

Based on asyncua documentation, the following professional tools are available:

- **`uabrowse`** - Browse OPC-UA nodes and print results
- **`uaclient`** - Connect to server and start Python shell with root/objects nodes
- **`uadiscover`** - Perform OPC UA discovery and print server/endpoint information
- **`uals`** - Browse OPC-UA nodes (alternative interface)
- **`uaread`/`uawrite`** - Read/write node attributes and values
- **`uaserver`** - Run example OPC-UA server with XML definition support
- **`uasubscribe`** - Subscribe to nodes and print real-time results
- **`uahistoryread`** - Read historical data from nodes
- **`uacall`** - Call methods on nodes
- **`opcua-client-gui`** - Full-featured GUI client (separate package)

**Replacement Strategy**:

**OPC Test Server Analysis**:

**❌ REPLACE Custom Server** with **✅ `uaserver` + XML Nodeset** (Industry Standard Approach):

**Why Replace Our Custom Server:**

- ❌ **Custom Maintenance**: We maintain server infrastructure instead of focusing on domain logic
- ❌ **Missing Features**: Lacks professional features (security, caching, performance optimizations)
- ❌ **Non-Standard**: Custom approach instead of OPC UA industry standard (NodeSet2.xml)
- ❌ **Limited Tooling**: Can't leverage standard OPC UA development ecosystem

**✅ Benefits of `uaserver` + XML Nodeset:**

- ✅ **Industry Standard**: Uses NodeSet2.xml format - official OPC UA standard
- ✅ **Professional Infrastructure**: Production-ready server with security, caching, error handling
- ✅ **Zero Maintenance**: No custom server code to maintain
- ✅ **Interoperability**: XML nodesets work with UaExpert, UaModeler, other OPC UA tools
- ✅ **Self-Documenting**: Structure defined in standardized, shareable XML format
- ✅ **Flexibility**: Modify structure without code changes

**Implementation Plan:**

1. **Export Current Structure**: Use asyncua `XmlExporter` to generate `potting-lines.xml` nodeset
1. **Replace Server**: Use `uaserver --import potting-lines.xml` instead of custom server
1. **Update Makefile**: Replace `make opc-server` with `uaserver` + our nodeset
1. **Delete Custom Server**: Remove `opc_test_server.py` after successful migration

**Technical Details:**

- AsyncUA supports `server.import_xml("path/to/nodeset.xml")` for nodeset loading
- NodeSet2.xml format preserves our domain structure: `Lijn1/PC/nr_actieve_partij`
- Built-in `uaserver` provides `--certificate`, `--private_key`, `--populate` options

**✅ Keep Custom Scripts** (provide unique value):

- `opc_monitor.py` - Our custom real-time dashboard format is valuable for development

- `test_multiple_writes.py` - Stress testing specific to our threading approach

- `opc_test_server.py` → **REPLACE** with `uaserver` + `potting-lines.xml` nodeset

**❌ Replace with Built-in Tools**:

- `opc_write_test.py` → Replace with `uawrite` + `uaread` combination
- `test_webapp_approach.py` → Replace with `uaclient` interactive testing
- `test_run_io_bound.py` → No longer needed after proper asyncua.sync implementation

**✅ Add Professional Tools**:

- Use `uadiscover` for server discovery and endpoint validation
- Use `uasubscribe` for real-time monitoring during development
- Use `uaclient` for interactive debugging and exploration
- Add `opcua-client-gui` as development tool (pip install opcua-client)

**Implementation**:

1. **Document AsyncUA Tools**: Add usage examples to development documentation
1. **Create Make Targets**: Add makefile targets for common asyncua tool operations
1. **Replace Simple Scripts**: Remove redundant custom scripts, document tool alternatives
1. **Keep Specialized Scripts**: Maintain scripts that provide unique functionality
1. **Add GUI Client**: Install and document opcua-client-gui for advanced debugging

**Makefile Additions**:

```makefile
# OPC UA development tools
opc-discover:
 uadiscover opc.tcp://127.0.0.1:4840/potting-lines/

opc-browse:
 uabrowse opc.tcp://127.0.0.1:4840/potting-lines/

opc-read-line1:
 uaread opc.tcp://127.0.0.1:4840/potting-lines/ "ns=2;s=Lijn1.PC.nr_actieve_partij"

opc-write-line1:
 uawrite opc.tcp://127.0.0.1:4840/potting-lines/ "ns=2;s=Lijn1.PC.nr_actieve_partij" 12345

opc-subscribe:
 uasubscribe opc.tcp://127.0.0.1:4840/potting-lines/ "ns=2;s=Lijn1.PC.nr_actieve_partij"

opc-client:
 uaclient opc.tcp://127.0.0.1:4840/potting-lines/
```

**Benefits**:

- Professional-grade tools with comprehensive error handling
- Standardized command-line interface following OPC UA best practices
- Better maintenance (maintained by asyncua team, not us)
- Comprehensive functionality (browse, discover, subscribe, history, etc.)
- Interactive debugging capabilities
- GUI client for visual inspection and testing

**User Value**: Professional OPC UA development environment with standardized tools, reducing maintenance burden while providing more comprehensive functionality

#### Step 7: Enhanced Visual Feedback

**Goal**: Better visual indicators for active lots and process status

**Data Layer**:

- No changes needed

**UI Changes**:

- page per potting line:
  - ✅ active lot on the line:
    - ✅ display lot details
    - ✅ display complete and deactivate buttons
  - no active lot on the line:
    - ✅ display dropdow to select potting lot
    - ✅ qr code wih url to the current page, so that people can use their own phone
    - ✅ button to activate the lot on this line
    - barcode scanner component to scan a potting lot label (wait for details on how to do this)

**Tests**:

- show correct options

**User Value**: Clearer visual feedback makes it easier to understand current state

#### Later enhancements

- Write potted count to technison database
- When there is no lot active on a potting line add a button or scan control to activate one, either by typing a the number or scanning the label.
- re-evaluate our routes
