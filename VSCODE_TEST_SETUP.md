# VS Code Test Setup Guide

## Issue Fixed ✅

Your tests weren't showing in VS Code because the test discovery settings were pointing to the wrong directory.

### What Was Wrong

```json
{
    "python.testing.unittestArgs": [
        "-s",
        "./tests",  // ❌ Looking in ./tests directory
        "-p",
        "*test.py"
    ]
}
```

### What Was Fixed

```json
{
    "python.testing.unittestArgs": [
        "-s",
        ".",  // ✅ Now looking in root directory
        "-p",
        "test_*.py"  // ✅ Correct pattern for your test files
    ]
}
```

## How to View Tests in VS Code

### Method 1: Testing Sidebar
1. Click the **flask/beaker icon** in the left sidebar (Testing view)
2. Or press `Cmd+Shift+T` (macOS) or `Ctrl+Shift+T` (Windows/Linux)
3. You should now see your test files and test cases

### Method 2: Test Explorer
- The tests should appear in a tree view:
  ```
  📁 akamai-cache-tester
    📄 test_batching_unittest.py
      ✓ TestBatchProcessing
        ▶ test_batch_processing_with_delay
        ▶ test_batch_size_configuration
        ▶ test_exact_multiple_batches
        ▶ test_single_batch_no_delay
    📄 test_headers.py
    📄 test_summary.py
  ```

### Method 3: Refresh Test Discovery
If tests still don't appear:
1. Open Command Palette: `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
2. Type: "Python: Refresh Tests"
3. Press Enter

## Running Tests

### From VS Code UI
- **Run all tests**: Click the play button at the top of Testing view
- **Run single test**: Click the play button next to individual test
- **Debug test**: Click the debug icon next to test
- **Run failed tests only**: Click the "Run Failed Tests" button

### From Terminal
```bash
# Run all tests
python3 -m unittest discover -v

# Run specific test file
python3 -m unittest test_batching_unittest -v

# Run specific test case
python3 -m unittest test_batching_unittest.TestBatchProcessing.test_batch_processing_with_delay -v
```

## Test Files in Your Project

| File | Type | Status |
|------|------|--------|
| `test_batching_unittest.py` | Unit tests (unittest) | ✅ VS Code compatible |
| `test_batching.py` | Standalone function | ⚠️ Won't show in VS Code |
| `test_headers.py` | Manual test script | ⚠️ Won't show in VS Code |
| `test_summary.py` | Manual test script | ⚠️ Won't show in VS Code |

## Why test_batching.py Won't Show

Your original `test_batching.py` uses a standalone function:

```python
def test_batch_processing_with_delay():  # ❌ Not a unittest.TestCase
    # test code
    pass

if __name__ == '__main__':
    test_batch_processing_with_delay()
```

VS Code test discovery requires `unittest.TestCase` classes:

```python
class TestBatchProcessing(unittest.TestCase):  # ✅ Proper test class
    def test_batch_processing_with_delay(self):
        # test code
        pass
```

## Converting Other Test Files

If you want `test_headers.py` and `test_summary.py` to show in VS Code, convert them to unittest format:

### Before (Standalone)
```python
def test_something():
    # test code
    assert something == expected
```

### After (unittest)
```python
import unittest

class TestSomething(unittest.TestCase):
    def test_something(self):
        # test code
        self.assertEqual(something, expected)
```

## Test Output

### View Test Results
- **Output Panel**: View → Output → Select "Python Test Log"
- **Test Results**: Shows pass/fail status inline
- **Problems Panel**: Shows test failures as problems

### Debug Tests
1. Set breakpoints in your test code
2. Right-click on test → "Debug Test"
3. Use VS Code debugger controls

## Troubleshooting

### Tests Still Not Showing?

1. **Check Python Interpreter**
   - Bottom left status bar shows Python version
   - Click to change if needed
   - Should be Python 3.13

2. **Check Output for Errors**
   - View → Output
   - Select "Python Test Log" from dropdown
   - Look for import errors or syntax errors

3. **Verify Test Discovery**
   ```bash
   python3 -m unittest discover -v
   ```
   If this works in terminal but not VS Code, there's a VS Code configuration issue.

4. **Reload Window**
   - `Cmd+Shift+P` → "Developer: Reload Window"

### Common Issues

| Issue | Solution |
|-------|----------|
| "No tests discovered" | Check `-s` path in settings.json |
| Import errors | Ensure `app.py` is in same directory |
| Tests grayed out | Python interpreter not selected |
| Tests not updating | Refresh test discovery |

## Current Settings

Your `.vscode/settings.json` is now configured as:

```json
{
    "python.testing.unittestArgs": [
        "-v",              // Verbose output
        "-s",              // Start directory
        ".",               // Current directory (root)
        "-p",              // Pattern
        "test_*.py"        // Match test_*.py files
    ],
    "python.testing.pytestEnabled": false,
    "python.testing.unittestEnabled": true,
    "python.testing.autoTestDiscoverOnSaveEnabled": true
}
```

## Next Steps

1. **Open Testing View**: Click flask icon in sidebar or press `Cmd+Shift+T`
2. **Refresh Tests**: Command Palette → "Python: Refresh Tests"
3. **Run Tests**: Click play button to run all tests
4. **Verify**: You should see `test_batching_unittest.py` with 4 tests

Your tests should now be visible and runnable from VS Code! 🎉
