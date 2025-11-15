# Collapsible Configuration Section

## Overview

The batch processing configuration options (Batch Size, Pause Between Batches, Max URLs) are now grouped in a collapsible section that is **hidden by default**. This provides a cleaner user interface while still allowing power users to customize settings when needed.

## UI Layout

### Default View (Collapsed)

```
┌──────────────────────────────────────────────────────────┐
│  🚀 Akamai Cache Tester                                  │
│  Test your sitemap URLs for Akamai cache performance     │
├──────────────────────────────────────────────────────────┤
│  Sitemap.xml URL                                         │
│  ┌────────────────────────────────────────────────────┐ │
│  │ https://example.com/sitemap.xml                    │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ☑ Check for Adobe Experience Manager (AEM)             │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ ⚙️ Configuration (Batch size, delays, limits)  ▼  │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  [Test Sitemap]                                          │
└──────────────────────────────────────────────────────────┘
```

### Expanded View (Open)

```
┌──────────────────────────────────────────────────────────┐
│  🚀 Akamai Cache Tester                                  │
│  Test your sitemap URLs for Akamai cache performance     │
├──────────────────────────────────────────────────────────┤
│  Sitemap.xml URL                                         │
│  ┌────────────────────────────────────────────────────┐ │
│  │ https://example.com/sitemap.xml                    │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ☑ Check for Adobe Experience Manager (AEM)             │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ ⚙️ Configuration (Batch size, delays, limits)  ▲  │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │                                                    │ │
│  │  Batch Size                                        │ │
│  │  ┌──────┐                                          │ │
│  │  │  3   │                                          │ │
│  │  └──────┘                                          │ │
│  │                                                    │ │
│  │  Pause Between Batches (seconds)                   │ │
│  │  ┌──────┐                                          │ │
│  │  │ 1.0  │                                          │ │
│  │  └──────┘                                          │ │
│  │                                                    │ │
│  │  Max URLs (optional)                               │ │
│  │  ┌──────────────────────┐                         │ │
│  │  │ No limit             │                         │ │
│  │  └──────────────────────┘                         │ │
│  │                                                    │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  [Test Sitemap]                                          │
└──────────────────────────────────────────────────────────┘
```

## Features

### 1. Toggle Button
- **Location**: Between AEM checkbox and Test Sitemap button
- **Label**: "⚙️ Configuration (Batch size, delays, limits)"
- **Icon**: ▼ when collapsed, ▲ when expanded (with rotation animation)
- **Behavior**: Click to expand/collapse configuration section

### 2. Visual Feedback
- **Hover Effect**: Light gray background on hover
- **Animation**: Smooth slide-down/slide-up animation (0.3s)
- **Icon Rotation**: Arrow icon rotates 180° when toggling
- **Background**: Light gray (#f8f9fa) for subtle grouping

### 3. Default State
- **Collapsed by default**: Configuration section is hidden when page loads
- **Preserves values**: Input values are retained even when section is collapsed
- **Clean UI**: Reduces visual clutter for casual users

## CSS Implementation

### Key Styles

**Toggle Button:**
```css
.config-toggle {
    background: #f8f9fa;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 20px;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.config-toggle:hover {
    background: #e9ecef;
}
```

**Collapsible Content:**
```css
.config-content {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.3s ease-out;
}

.config-content.open {
    max-height: 500px;
}
```

**Icon Rotation:**
```css
.config-toggle-icon {
    transition: transform 0.3s;
}

.config-toggle-icon.open {
    transform: rotate(180deg);
}
```

## JavaScript Implementation

### Toggle Function

```javascript
function toggleConfiguration() {
    const content = document.getElementById('configContent');
    const icon = document.getElementById('configToggleIcon');

    content.classList.toggle('open');
    icon.classList.toggle('open');
}
```

**How it works:**
1. Toggles the `open` class on the content container
2. When `open` class is added, `max-height` expands from 0 to 500px
3. Icon rotates 180° by toggling `open` class
4. CSS transitions create smooth animations

## User Experience Benefits

### 1. Simplified First Impression
- New users see a clean, uncluttered interface
- Only essential fields (sitemap URL and AEM checkbox) are visible
- Reduces cognitive load and decision fatigue

### 2. Progressive Disclosure
- Advanced options are available but not overwhelming
- Users discover configuration when they need it
- Clear labeling indicates what's inside

### 3. Flexible for Different Users
- **Casual users**: Can ignore configuration and use defaults
- **Power users**: Can expand and customize settings
- **Returning users**: Settings are preserved across form submissions

### 4. Visual Clarity
- Gear icon (⚙️) universally indicates settings/configuration
- Descriptive subtitle explains what's inside
- Arrow indicator shows current state

## Accessibility Considerations

### Current Implementation
- ✅ Clickable with mouse
- ✅ Visual indicator of state
- ✅ Smooth animation for visual feedback
- ✅ Descriptive text labels

### Future Improvements
- Add keyboard support (Enter/Space to toggle)
- Add ARIA attributes (aria-expanded, aria-controls)
- Add screen reader announcements
- Add focus indicator for keyboard navigation

## Testing

### Manual Test Checklist

**Toggle Functionality:**
- [ ] Click toggle button to expand
- [ ] Click again to collapse
- [ ] Verify smooth animation
- [ ] Verify icon rotates correctly

**State Persistence:**
- [ ] Enter values in configuration fields
- [ ] Collapse the section
- [ ] Expand again
- [ ] Verify values are still there

**Form Submission:**
- [ ] Enter sitemap URL
- [ ] Expand configuration and change values
- [ ] Collapse configuration
- [ ] Submit form
- [ ] Verify custom values are used

**Visual:**
- [ ] Hover over toggle shows hover effect
- [ ] Collapsed state shows only toggle button
- [ ] Expanded state shows all fields
- [ ] Animation is smooth (no jank)

## Browser Compatibility

**Tested and working:**
- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari

**Requirements:**
- CSS transitions
- CSS transforms (for icon rotation)
- JavaScript classList API
- CSS max-height animation

All modern browsers support these features.

## Performance

### Efficient Implementation
- **No JavaScript frameworks**: Pure vanilla JS
- **CSS-driven animations**: Hardware-accelerated
- **Minimal reflows**: Uses max-height instead of height
- **No AJAX calls**: Pure client-side interaction

### Optimization Notes
- Using `max-height` instead of `height` avoids measuring element size
- Transition limited to specific properties (not `all`)
- `overflow: hidden` prevents content overflow during animation

## Comparison: Before vs After

### Before (All Fields Always Visible)
```
Sitemap URL: [input]
AEM Checkbox: [checkbox]
Batch Size: [input]
Pause Between Batches: [input]
Max URLs: [input]
[Button]
```
**Issues:**
- Too many fields visible at once
- Overwhelming for new users
- No visual grouping of advanced options

### After (Collapsible Configuration)
```
Sitemap URL: [input]
AEM Checkbox: [checkbox]
⚙️ Configuration ▼
[Button]
```
**Benefits:**
- Cleaner initial view
- Advanced options discoverable
- Clear grouping of related settings
- Progressive disclosure pattern

## Summary

The collapsible configuration section improves the user interface by:
1. **Reducing visual clutter** - Advanced options hidden by default
2. **Maintaining flexibility** - Power users can still customize
3. **Improving discoverability** - Clear labeling and icon
4. **Preserving values** - Settings retained when collapsed
5. **Smooth interaction** - Animated expand/collapse with visual feedback

This is a common UX pattern (progressive disclosure) that balances simplicity with power.
