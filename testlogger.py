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