# SOP Builder Code Cleanup Action Plan

## High Impact Actions (>500 lines reduction)

### 1. **Create a Shared Widget Safety Utility Class** (~800 lines)
The `_safe_widget_exists`, `_safe_destroy_widget`, and `_is_child_of` methods are duplicated across multiple files:
- `gui/canvas_panel.py`
- `gui/handlers/canvas_drag_drop_handler.py` 
- `gui/handlers/library_drag_drop_handler.py`
- `gui/main_window.py`

**Action:** Create `gui/utils/widget_safety.py`:

### 2. **Consolidate File Path Normalization** (~600 lines)
Multiple modules have their own `_normalize_file_path` or `_normalize_media_path` methods:
- `modules/media_module.py`
- `modules/issue_card_module.py`
- `modules/media_grid_module.py`
- `modules/base_module.py`
- `utils/media_discovery.py`

**Action:** Move to a single utility in `utils/path_utils.py`:

### 3. **Remove Debug Print Statements** (~500 lines)
Extensive debugging prints throughout:
- `utils/module_content_updater.py` (50+ debug prints)
- `utils/preview_server.py` (30+ debug prints)
- `utils/html_generator.py` (20+ debug prints)
- `modules/media_module.py` (15+ debug prints)
- Many other files

**Action:** Remove all temporary debug print statements or convert critical ones to proper logging.

## Medium Impact Actions (200-500 lines reduction)

### 4. **Create Shared Media Rendering Utility** (~400 lines)
Similar media rendering logic appears in multiple modules:
- `modules/media_module.py` (`render_to_html`)
- `modules/issue_card_module.py` (`_render_media_container`)
- `modules/media_grid_module.py` (media item rendering)

**Action:** Create `utils/media_renderer.py`:

### 5. **Consolidate Tab Module Operations** (~350 lines)
Tab-specific operations are scattered across:
- `gui/renderers/tab_widget_manager.py`
- `gui/canvas_panel.py`
- `gui/properties_panel.py`
- `app/sop_builder.py`

**Action:** Create cleaner interfaces and reduce duplication in tab handling logic.

### 6. **Unify File Dialog Operations** (~300 lines)
File selection dialogs are implemented similarly in multiple places:
- `gui/properties_panel.py` (multiple browse methods)
- `app/sop_builder.py`

**Action:** Create `gui/utils/file_dialogs.py`:

### 7. **Consolidate Media Type Validation** (~250 lines)
Media type checking is duplicated in:
- `utils/media_discovery.py`
- `utils/base64_embedder.py`
- Various module files

**Action:** Create a single source of truth for media type definitions and validation.

## Low Impact Actions (50-200 lines reduction)

### 8. **Extract Module Preview Text Generation** (~150 lines)
Preview text generation logic appears in:
- `gui/renderers/module_widget_manager.py`
- `gui/properties_panel.py`

**Action:** Create a single `get_module_preview_text` method in `Module` base class.

### 9. **Consolidate Import Groups** (~100 lines)
Many files have similar import patterns that could be standardized.

**Action:** Create common import utilities for frequently used combinations.

### 10. **Remove Redundant Comments and Docstrings** (~100 lines)
Many obvious methods have extensive docstrings that don't add value.

**Action:** Keep docstrings only for complex or public API methods.

### 11. **Simplify Property Field Creation** (~80 lines)
The `_create_input_widget` method in `properties_panel.py` is very long and could use helper methods.

**Action:** Break down into smaller, focused methods.

### 12. **Remove Unused Imports** (~50 lines)
Several files import modules that aren't used.

**Action:** Run a linter to identify and remove unused imports.

## Additional Optimizations

### 13. **Use Constants for Magic Strings**
Create a `constants.py` file for repeated strings like:
- File type extensions
- CSS color values
- Widget dimensions
- Error messages

### 14. **Simplify Exception Handling**
Many try/except blocks catch generic exceptions or have identical handling.

**Action:** Create exception handling utilities for common patterns.

### 15. **Extract CSS Generation**
HTML/CSS generation strings are embedded throughout. Consider template files or a CSS builder utility.

## Implementation Priority

1. **Start with #3** (Remove debug prints) - Easy win, immediate impact
2. **Then #1** (Widget safety) - High impact, clear boundaries
3. **Follow with #2** (Path normalization) - High impact, improves consistency
4. **Continue with #4** (Media rendering) - Good abstraction opportunity
5. Work through remaining items based on current development needs

## Estimated Total Reduction
- **Conservative estimate:** 2,500-3,000 lines (~15-20% of codebase)
- **Aggressive refactoring:** 4,000-5,000 lines (~25-30% of codebase)

## Testing Recommendations
- Create unit tests before major refactoring
- Test drag-and-drop functionality thoroughly after widget safety changes
- Verify all media types still render correctly after consolidation
- Ensure file paths work on both Windows and Unix systems
