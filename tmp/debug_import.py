
import sys
try:
    print("Importing tui.cli...")
    import tui.cli
    print("Import success!")
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
