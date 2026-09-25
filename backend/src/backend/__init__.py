"""Website Archaeologist backend package."""

def main() -> None:
    """Run the API with ``python -m backend.main``."""
    from .main import app
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
