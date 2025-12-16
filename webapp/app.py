import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

from flask import Flask, jsonify, render_template, request, send_from_directory, url_for

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_ROOT = BASE_DIR / "outputs"
OUTPUT_ROOT.mkdir(exist_ok=True)

# Make local modules importable
sys.path.extend(
    [
        str(BASE_DIR),
        str(BASE_DIR / "Setup"),
        str(BASE_DIR / "execution"),
        str(BASE_DIR / "functions"),
    ]
)

# Lazy imports for Earth Engine stack
gee_setup = None
ee = None
snow_difference_map = None
IMPORT_ERROR = None

logger = logging.getLogger(__name__)

try:
    import gee_setup  # type: ignore

    ee = gee_setup.ee
except Exception as exc:  # pragma: no cover - import guard
    IMPORT_ERROR = f"Unable to import gee_setup: {exc}"
else:
    if ee is None:
        IMPORT_ERROR = "earthengine-api is not available. Install dependencies and authenticate."

# Import the analysis function directly from its file path to avoid sys.path issues
if ee:
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "grand_file", BASE_DIR / "execution" / "grand_file.py"
        )
        if spec and spec.loader:
            grand_file = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(grand_file)
            snow_difference_map = grand_file.snow_difference_map
        else:  # pragma: no cover - defensive path
            IMPORT_ERROR = "Could not load execution/grand_file.py"
    except Exception as exc:  # pragma: no cover - import guard
        IMPORT_ERROR = f"Unable to import analysis backend: {exc}"

app = Flask(__name__)
app.config["OUTPUT_ROOT"] = OUTPUT_ROOT

gee_ready = False


def ensure_gee_initialized() -> bool:
    """Initialize Earth Engine once and report readiness."""
    global gee_ready
    if gee_ready:
        return True
    if not gee_setup or not ee:
        return False
    try:
        gee_ready = bool(gee_setup.initialize_gee())
    except Exception as exc:  # pragma: no cover - runtime guard
        logger.exception("Failed to initialize Earth Engine: %s", exc)
        gee_ready = False
    return gee_ready


def sanitize_output_name(name: str) -> str:
    """Restrict filenames to safe characters."""
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "_", name).strip("_")
    return cleaned or "snow_analysis"


def polygon_to_ee_geometry(coords: List[List[float]]):
    """Convert coordinate list to EE polygon."""
    return ee.Geometry.Polygon([coords])


def build_output_listing(output_dir: Path, output_name: str) -> Dict[str, object]:
    """Create a JSON-friendly listing of generated output files."""
    def to_url(path: Path) -> str:
        relative = path.relative_to(app.config["OUTPUT_ROOT"])
        return url_for("serve_output", filename=str(relative))

    html_map: Optional[str] = None
    html_path = output_dir / f"{output_name}.html"
    if html_path.exists():
        html_map = to_url(html_path)

    raw_files = []
    raw_dir = output_dir / "raw_data"
    if raw_dir.exists():
        raw_files = [to_url(p) for p in sorted(raw_dir.glob("*")) if p.is_file()]

    visualized_files = []
    vis_dir = output_dir / "visualized"
    if vis_dir.exists():
        visualized_files = [to_url(p) for p in sorted(vis_dir.glob("*")) if p.is_file()]

    return {
        "html_map": html_map,
        "raw_files": raw_files,
        "visualized_files": visualized_files,
    }


@app.route("/")
def index():
    """Main page with map and input form."""
    return render_template("index.html")


@app.route("/outputs/<path:filename>")
def serve_output(filename: str):
    """Serve generated analysis artifacts."""
    return send_from_directory(app.config["OUTPUT_ROOT"], filename, as_attachment=False)


@app.route("/analyze", methods=["POST"])
def analyze():
    """Run the snowpack analysis using provided parameters."""
    if IMPORT_ERROR:
        return jsonify({"status": "error", "message": IMPORT_ERROR}), 500

    if not snow_difference_map:
        return jsonify({"status": "error", "message": "Analysis backend not available."}), 500

    if not ensure_gee_initialized():
        return jsonify(
            {
                "status": "error",
                "message": "Google Earth Engine is not initialized. Run `earthengine authenticate` and restart the app.",
            }
        ), 500

    data = request.get_json(silent=True) or {}
    polygon = data.get("polygon")
    if not polygon or not isinstance(polygon, list) or len(polygon) < 3:
        return jsonify({"status": "error", "message": "A polygon with at least three coordinates is required."}), 400

    try:
        coords: List[List[float]] = [[float(pt[0]), float(pt[1])] for pt in polygon]
    except Exception:
        return jsonify({"status": "error", "message": "Polygon coordinates must be numeric longitude/latitude pairs."}), 400

    # Ensure polygon is closed for EE geometry requirements
    if coords[0] != coords[-1]:
        coords.append(coords[0])

    try:
        params = {
            "historical_start": data.get("historical_start", "1990-01-01"),
            "historical_end": data.get("historical_end", "2000-01-01"),
            "recent_start": data.get("recent_start", "2015-01-01"),
            "recent_end": data.get("recent_end", "2025-01-01"),
            "month": int(data.get("month", 6)),
            "cloud_cover": int(data.get("cloud_cover", 10)),
            "output_name": sanitize_output_name(data.get("output_name", "snow_analysis")),
            "clip_to_region": bool(data.get("clip_to_region", False)),
        }
    except (TypeError, ValueError):
        return jsonify({"status": "error", "message": "Invalid parameter values supplied."}), 400

    output_dir = app.config["OUTPUT_ROOT"] / params["output_name"]
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        region = polygon_to_ee_geometry(coords)
        snow_difference_map(
            region_polygon=region,
            date_range_1=ee.DateRange(params["historical_start"], params["historical_end"]),
            date_range_2=ee.DateRange(params["recent_start"], params["recent_end"]),
            month_int=params["month"],
            cloud_cover=params["cloud_cover"],
            clip_to_region=params["clip_to_region"],
            output_folder=str(output_dir),
            output_filename=params["output_name"],
        )
    except Exception as exc:  # pragma: no cover - runtime guard
        logger.exception("Analysis failed: %s", exc)
        return jsonify({"status": "error", "message": str(exc)}), 500

    outputs = build_output_listing(output_dir, params["output_name"])

    return jsonify(
        {
            "status": "success",
            "message": "Analysis complete. Download links ready.",
            "outputs": outputs,
            "params": params,
        }
    )


if __name__ == "__main__":  # pragma: no cover - manual execution
    app.run(debug=True, port=5000)
