# WebSocket Live Preview Implementation Plan

## Overview

Replace the current file-based auto-refresh preview system with a WebSocket-based live preview server that provides instant, event-driven updates to the browser without polling.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐    ┌─────────────────┐
│   SOP Builder   │     │  Preview Server  │    │    Browser      │
│      App        │     │   (WebSocket)    │    │   (Client)      │
├─────────────────┤     ├──────────────────┤    ├─────────────────┤
│ • Document      │───▶│ • HTTP Server    │───▶│ • HTML Content  │
│   Changes       │     │ • WebSocket      │    │ • WebSocket     │
│ • Event-driven  │     │   Handler        │    │   Client        │
│   Updates       │     │ • Content Cache  │    │ • Auto-update   │
└─────────────────┘     └──────────────────┘    └─────────────────┘
```

## Implementation Steps

### Step 1: Create Preview Server Component

**File**: `utils/preview_server.py`

*COMPLETE!*

### Step 2: Enhance DocumentPreviewManager

**File**: `gui/preview_manager.py` (modifications)

*COMPLETE!*

### Step 3: Dependencies and Installation

*COMPLETE!*

### Step 4: Integration with Main App

**File**: `app/sop_builder.py` (minimal changes needed)

*COMPLETE!*

## Error Handling

### Port Conflicts
- Automatically finds free ports starting from defaults
- Tries up to 100 ports before failing
- Clear error messages if no ports available

### Connection Issues
- Graceful WebSocket reconnection with exponential backoff
- Maximum reconnection attempts to prevent infinite loops
- Visual status indicators for connection state

### Server Failures
- Automatic fallback to file-based preview
- Proper cleanup of server resources
- Thread-safe server shutdown

### Browser Issues
- Handles multiple browser tabs gracefully
- Manages disconnected clients automatically
- Prevents memory leaks from stale connections

## Future Enhancements

### Incremental Updates
- Send only changed sections instead of full page reload
- Highlight modified areas with subtle animations
- Preserve form inputs and scroll positions

### Advanced Features
- **Multi-device Preview**: Preview on mobile devices
- **Collaborative Editing**: Multiple users viewing same preview
- **Performance Metrics**: Show update latency and connection stats
- **Custom Themes**: Real-time theme switching in preview

### Development Tools
- **Debug Mode**: Detailed WebSocket message logging
- **Health Monitoring**: Server status dashboard
- **Update Analytics**: Track update frequency and performance
