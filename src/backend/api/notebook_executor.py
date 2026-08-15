"""Execute Jupyter notebooks with custom parameters and return results."""

import os
import tempfile
from pathlib import Path
from typing import Any

import papermill as pm
from nbconvert import HTMLExporter
from nbformat import read as read_notebook

# Project root: two levels above this file (src/backend/api → project root)
_PROJECT_ROOT = Path(__file__).resolve().parents[3]


def execute_notebook(
    notebook_path: Path, symbol: str, timeout: int = 300
) -> dict[str, Any]:
    """
    Execute a notebook with a custom SYMBOL parameter.
    
    Args:
        notebook_path: Path to the .ipynb file
        symbol: The stock symbol to analyze (replaces SYMBOL variable)
        timeout: Maximum execution time in seconds
    
    Returns:
        Dictionary containing:
        - html: HTML representation of executed notebook
        - cells_output: Key outputs from each cell
        - success: Whether execution succeeded
        - error: Error message if failed
    """
    try:
        # Create a temporary output notebook
        with tempfile.NamedTemporaryFile(
            suffix=".ipynb", delete=False
        ) as tmp_file:
            output_path = Path(tmp_file.name)

        # Use non-interactive backend so matplotlib doesn't try to open a window.
        # This must be set before the kernel spawns so it inherits the variable.
        os.environ.setdefault("MPLBACKEND", "Agg")

        # Execute notebook with custom parameters, run from the project root so
        # relative imports (src.backend.*) resolve correctly.
        # timeout is per-cell; total runtime is bounded by cell_count * timeout.
        pm.execute_notebook(
            str(notebook_path),
            str(output_path),
            parameters={"SYMBOL": symbol},
            timeout=60,
            cwd=str(_PROJECT_ROOT),
            progress_bar=False,
        )

        # Convert executed notebook to HTML
        html_exporter = HTMLExporter()
        html_content, _ = html_exporter.from_filename(str(output_path))

        # Extract key outputs from cells
        notebook = read_notebook(str(output_path), as_version=4)
        cells_output = _extract_cell_outputs(notebook)

        # Clean up temporary file
        output_path.unlink()

        return {
            "success": True,
            "html": html_content,
            "cells_output": cells_output,
            "symbol": symbol,
            "error": None,
        }

    except Exception as exc:
        return {
            "success": False,
            "html": None,
            "cells_output": None,
            "symbol": symbol,
            "error": str(exc),
        }


def _extract_cell_outputs(notebook: Any) -> dict[str, list[Any]]:
    """Extract text and data outputs from notebook cells."""
    outputs = {}

    for idx, cell in enumerate(notebook.cells):
        if cell.cell_type == "code" and hasattr(cell, "outputs"):
            cell_outputs = []
            for output in cell.outputs:
                if hasattr(output, "data"):
                    # Extract various output formats
                    if "text/plain" in output.data:
                        cell_outputs.append(output.data["text/plain"])
                    elif "text/html" in output.data:
                        cell_outputs.append({"html": output.data["text/html"]})
                    elif "image/png" in output.data:
                        cell_outputs.append({"image": output.data["image/png"]})
                elif hasattr(output, "text"):
                    cell_outputs.append(output.text)

            if cell_outputs:
                outputs[f"cell_{idx}"] = cell_outputs

    return outputs
