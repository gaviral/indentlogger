# indentlogger

**indentlogger** is an indentation-based logging library for Python, offering:

- **Function-call tracing** with nested indentation or ASCII-box style.
- **Automatic decoration** for modules/classes (no manual decorators needed).
- **Optional** replacement for `print` (use `logger.info()`, etc.).

## Installation

**From PyPI** (once published):
```bash
pip install indentlogger
```

## Quick Start

```python
import logging
from indentlogger import IndentLogger, LogStyle

logger = IndentLogger()
logger.configure(
    style=LogStyle.DASHED_BOX, 
    level=logging.DEBUG,         # integer constant from logging
    auto_log_level=logging.DEBUG # function entry/exit logs
)

@logger.log_entry_exit
def sample_function(x):
    logger.info(f"Inside sample_function with x={x}")

sample_function(42)
```

When run, you’ll see ASCII “boxes” showing function entry, your log, and function exit.

## Configuration

- **`style`**: `SIMPLE`, `DASHED_BOX`, `NO_PIPES`, or `DISABLED`.
- **`level`**: Overall logging threshold (e.g., `logging.INFO`, `logging.DEBUG`).  
- **`auto_log_level`**: Logging level for function entry/exit calls.  
- **`dash_line_length`**: (default `60`) ASCII-box width in `DASHED_BOX` mode.  
- **`stream`**: Output stream (`sys.stdout`, file, etc.).

Example:
```python
logger.configure(style=LogStyle.SIMPLE, level=logging.INFO, auto_log_level=logging.DEBUG)
```

## Automatic Logging (No Decorators)

### Auto-Log an Entire Module

If you **don’t** want to decorate each function, let the logger scan and decorate everything for you:

```python
import logging
from indentlogger import IndentLogger, LogStyle

logger = IndentLogger()
logger.configure(style=LogStyle.DASHED_BOX, level=logging.DEBUG)

def fun1():
    logger.info("Hello from fun1")
    fun2(x=42)

def fun2(x):
    logger.debug(f"fun2 got x={x}")
    fun3(y=100)
    fun4()

def fun3(y):
    logger.info(f"fun3 got y={y}")

def fun4():
    logger.info("Hello from fun4")

def fun5():
    logger.info("Hello from fun5")

# No manual decorators here!
if __name__ == "__main__":
    # This decorates all top-level functions except those starting with '_'
    logger.auto_log_module(__name__)
    fun1()
    fun5()
```

Output:

```
.--fun1():--------------------------------------------------
|
│   Hello from fun1
│   .--fun2(x=42):------------------------------------------
│   |
│   │   fun2 got x=42
│   │   .--fun3(y=100):-------------------------------------
│   │   |
│   │   │   fun3 got y=100
│   │   '---------------------------------------------------
│   │   .--fun4():------------------------------------------
│   │   |
│   │   │   Hello from fun4
│   │   '---------------------------------------------------
│   '-------------------------------------------------------
'-----------------------------------------------------------
.--fun5():--------------------------------------------------
|
│   Hello from fun5
'-----------------------------------------------------------
```

### Auto-Log a Class

```python
class DataProcessor:
    def process(self, data):
        logger.info(f"Processing data={data}")
        return data * 2

# Decorate all public methods
logger.auto_log_class(DataProcessor)

dp = DataProcessor()
dp.process("Hello")
```

## Styles

1. **SIMPLE** – Minimal indentation with `│ `, no explicit end line.  
2. **DASHED_BOX** – ASCII boxes (top line: `.--fun(...):`, bottom line: `'--...`).  
3. **NO_PIPES** – Same as SIMPLE but uses spaces instead of `│ `.  
4. **DISABLED** – Skips all logging entirely.

## Example Outputs

### SIMPLE
```
fun1():
│ fun2(num=123):
│ │ Inside fun2
│ fun3():
│ │ Inside fun3
```

### DASHED_BOX
```
.--fun1():--------------------------------------
|
│   .--fun2(num=123):---------------------------
│   |
│   │   Inside fun2
│   |
│   '-------------------------------------------
│   .--fun3():----------------------------------
│   |
│   │   Inside fun3
│   |
│   '-------------------------------------------
|
'-----------------------------------------------
```

### NO_PIPES
```
fun1():
  fun2(num=123):
    Inside fun2
  fun3():
    Inside fun3
```

### DISABLED
No output at all.

## License

**MIT**. Free to use, extend, and modify.
