import functools
import inspect
import logging
import sys
import threading
from enum import Enum, auto

###############################################################################
#                       STYLES (Strategy Pattern)
###############################################################################

class LogStyle(Enum):
    SIMPLE = auto()
    DASHED_BOX = auto()
    NO_PIPES = auto()
    DISABLED = auto()

class BaseStyle:
    """
    Base interface for a 'style'. Subclasses must implement:
      - start_call(func_signature, logger, indent_level, auto_log_level)
      - end_call(logger, indent_level, auto_log_level)
      - prefix_for_message(indent_level)
    """
    def start_call(self, func_signature, logger, indent_level, auto_log_level):
        raise NotImplementedError()

    def end_call(self, logger, indent_level, auto_log_level):
        raise NotImplementedError()

    def prefix_for_message(self, indent_level):
        raise NotImplementedError()

class SimpleStyle(BaseStyle):
    """
    Minimal style, e.g.:
    funName(...):
    │ fun2(...):
    │ │ ...
    No explicit end line.
    """
    def start_call(self, func_signature, logger, indent_level, auto_log_level):
        prefix = "│ " * indent_level
        logger.log(auto_log_level, f"{prefix}{func_signature}:")
    def end_call(self, logger, indent_level, auto_log_level):
        pass
    def prefix_for_message(self, indent_level):
        return "│ " * indent_level

class DashedBoxStyle(BaseStyle):
    """
    Fancy ASCII box style with fixed right-edge alignment for the dashed line.
    Example total line width = 60 columns. If the prefix + .--func(...) etc.
    already use 30 chars, we only add 30 dashes so that the line ends at col 60.
    """

    def __init__(self, dash_line_length=60):
        # dash_line_length is our total target line width
        self.dash_line_length = dash_line_length

    def _make_dashed_line(self, prefix: str, line_core: str) -> str:
        """
        Build a line that starts with `prefix + line_core` and
        then fills the rest up to dash_line_length (if any space remains).
        """
        # Count how many chars we've used
        used_chars = len(prefix) + len(line_core)
        # Remaining space
        remain = self.dash_line_length - used_chars
        if remain > 0:
            return prefix + line_core + ("-" * remain)
        else:
            # If there's no space left, no dashes
            return prefix + line_core

    def start_call(self, func_signature, logger, indent_level, auto_log_level):
        # Build prefix (the left indentation for nesting)
        prefix = "│   " * indent_level

        # 1) The first line: .--funName(...) plus trailing dashes
        #    e.g. ".--fun2(num=123):"
        line_core = f".--{func_signature}:"
        line = self._make_dashed_line(prefix, line_core)
        logger.log(auto_log_level, line)

        # 2) The next line is just prefix + "|"
        logger.log(auto_log_level, prefix + "|")

    def end_call(self, logger, indent_level, auto_log_level):
        # The closing line is prefix + "'" plus trailing dashes
        prefix = "│   " * indent_level
        line_core = "'"
        line = self._make_dashed_line(prefix, line_core)
        logger.log(auto_log_level, line)

    def prefix_for_message(self, indent_level):
        # Normal log lines (inside a function call)
        return "│   " * indent_level


class NoPipesStyle(BaseStyle):
    """
    Same as SimpleStyle, but uses only spaces:
    funName(...):
      fun2(...):
        ...
    """
    def start_call(self, func_signature, logger, indent_level, auto_log_level):
        prefix = "  " * indent_level
        logger.log(auto_log_level, f"{prefix}{func_signature}:")
    def end_call(self, logger, indent_level, auto_log_level):
        pass
    def prefix_for_message(self, indent_level):
        return "  " * indent_level

class DisabledStyle(BaseStyle):
    """
    Logs nothing at all.
    """
    def start_call(self, func_signature, logger, indent_level, auto_log_level):
        pass
    def end_call(self, logger, indent_level, auto_log_level):
        pass
    def prefix_for_message(self, indent_level):
        return ""


###############################################################################
#                       MAIN LOGGING WRAPPER
###############################################################################

class IndentLogger:
    """
    A logger that can:
      - function as a near-complete replacement for print and standard logging,
      - auto-decorate function calls for indentation or ASCII-box formatting,
      - keep track of indent levels (thread-local for concurrency),
      - be turned off entirely (DISABLED).
    """

    def __init__(self, name="indent_logger"):
        self._logger = logging.getLogger(name)
        self._style = SimpleStyle()  # default
        self._enabled = True
        self._auto_log_level = logging.DEBUG
        self._threadlocal = threading.local()
        self._threadlocal.indent_level = 0

    def configure(
        self,
        style=LogStyle.SIMPLE,
        level=logging.INFO,
        auto_log_level=logging.DEBUG,
        dash_line_length=60,
        stream=None
    ):
        """
        Configure the logger's style, log level, line length for dashes, etc.
        If no handlers exist, attach a basic StreamHandler to `stream`.
        """
        self._style = self._resolve_style(style, dash_line_length)
        self._enabled = (style != LogStyle.DISABLED)
        self._auto_log_level = auto_log_level

        if not self._logger.handlers:
            if stream is None:
                stream = sys.stdout
            handler = logging.StreamHandler(stream)
            handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(handler)

        self._logger.setLevel(level)

    def _resolve_style(self, style_enum, dash_line_length):
        if style_enum == LogStyle.SIMPLE:
            return SimpleStyle()
        elif style_enum == LogStyle.DASHED_BOX:
            return DashedBoxStyle(dash_line_length)
        elif style_enum == LogStyle.NO_PIPES:
            return NoPipesStyle()
        elif style_enum == LogStyle.DISABLED:
            return DisabledStyle()
        else:
            return SimpleStyle()

    @property
    def indent_level(self):
        return getattr(self._threadlocal, "indent_level", 0)

    @indent_level.setter
    def indent_level(self, value):
        setattr(self._threadlocal, "indent_level", value)

    def disable(self):
        """Fully disable logging (equivalent to style=DISABLED)."""
        self._enabled = False
        self._style = DisabledStyle()

    # Standard log-level methods
    def debug(self, msg, *args, **kwargs):
        self._log(msg, logging.DEBUG, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._log(msg, logging.INFO, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._log(msg, logging.WARNING, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._log(msg, logging.ERROR, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._log(msg, logging.CRITICAL, *args, **kwargs)

    def _log(self, msg, level, *args, **kwargs):
        if not self._enabled:
            return
        prefix = self._style.prefix_for_message(self.indent_level)
        self._logger.log(level, prefix + str(msg), *args, **kwargs)

    # Decorator for function calls
    def log_entry_exit(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not self._enabled:
                return func(*args, **kwargs)

            # Build call signature
            param_names = list(inspect.signature(func).parameters.keys())
            sig_parts = []
            for i, arg_val in enumerate(args):
                if i < len(param_names):
                    pname = param_names[i]
                    if pname == "self":
                        sig_parts.append("self")
                    else:
                        sig_parts.append(f"{pname}={repr(arg_val)}")
            sig_parts.extend(f"{k}={repr(v)}" for k, v in kwargs.items())
            call_sig = f"{func.__name__}({', '.join(sig_parts)})"

            self._style.start_call(call_sig, self._logger, self.indent_level, self._auto_log_level)
            self.indent_level += 1

            try:
                return func(*args, **kwargs)
            finally:
                self.indent_level = max(0, self.indent_level - 1)
                self._style.end_call(self._logger, self.indent_level, self._auto_log_level)
        return wrapper

    def auto_log_module(self, module_name, excluded_functions=None):
        if not self._enabled:
            return
        import sys
        excluded_functions = excluded_functions or []
        module = sys.modules[module_name]

        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if (obj.__module__ == module_name
                and name not in excluded_functions
                and not name.startswith("_")):
                setattr(module, name, self.log_entry_exit(obj))

    def auto_log_class(self, cls, excluded_methods=None):
        if not self._enabled:
            return cls
        excluded_methods = excluded_methods or []
        for name, method in inspect.getmembers(cls, inspect.isfunction):
            if not name.startswith("_") and name not in excluded_methods:
                setattr(cls, name, self.log_entry_exit(method))
        return cls
