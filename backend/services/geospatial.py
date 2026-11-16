import rasterio
from rasterio.io import MemoryFile
from typing import Dict, Any, Tuple

def extract_metadata(image_bytes: bytes) -> Tuple[bool, Dict[str, Any]]:
    """
    Attempts to read geospatial metadata using rasterio.
    Returns a tuple: (is_georeferenced, metadata_dict)
    """
    try:
        with MemoryFile(image_bytes) as memfile:
            with memfile.open() as dataset:
                # Check if it has a coordinate reference system
                if dataset.crs is not None:
                    bounds = dataset.bounds
                    metadata = {
                        "crs": dataset.crs.to_string(),
                        "width": dataset.width,
                        "height": dataset.height,
                        "bounds": {
                            "left": bounds.left,
                            "bottom": bounds.bottom,
                            "right": bounds.right,
                            "top": bounds.top
                        },
                        "transform": [dataset.transform[i] for i in range(6)]
                    }
                    return True, metadata
                else:
                    return False, {"width": dataset.width, "height": dataset.height}
    except Exception as e:
        # If rasterio fails (e.g. it's a standard PNG/JPG), it's not georeferenced
        return False, {}
