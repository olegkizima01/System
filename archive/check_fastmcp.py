import fastmcp
print(dir(fastmcp))
try:
    from fastmcp import Image
    print("Image imported successfully")
except ImportError as e:
    print(f"Import failed: {e}")
