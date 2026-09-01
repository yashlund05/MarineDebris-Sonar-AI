import numpy as np
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TileInfo:
    tile: np.ndarray
    row_offset: int
    col_offset: int
    chunk_index: int
    ping_offset: int
    tile_row: int
    tile_col: int

def generate_tiles(image: np.ndarray, tile_size: int = 640, overlap: float = 0.2, chunk_index: int = 0, ping_offset: int = 0) -> list[TileInfo]:
    """
    Slice image into tile_size x tile_size tiles with overlap.
    Pads the image if necessary to make complete tiles.
    """
    if image.size == 0:
        return []

    H, W = image.shape
    stride = int(tile_size * (1.0 - overlap))
    if stride <= 0:
        stride = 1

    # Calculate padded size
    num_tiles_y = max(1, int(np.ceil((H - tile_size) / stride) + 1) if H > tile_size else 1)
    num_tiles_x = max(1, int(np.ceil((W - tile_size) / stride) + 1) if W > tile_size else 1)

    pad_h = max(0, (num_tiles_y - 1) * stride + tile_size - H)
    pad_w = max(0, (num_tiles_x - 1) * stride + tile_size - W)

    if pad_h > 0 or pad_w > 0:
        image = np.pad(image, ((0, pad_h), (0, pad_w)), mode='constant')

    tiles = []
    
    for r in range(num_tiles_y):
        for c in range(num_tiles_x):
            r_start = r * stride
            c_start = c * stride
            tile = image[r_start:r_start+tile_size, c_start:c_start+tile_size].copy()
            
            info = TileInfo(
                tile=tile,
                row_offset=r_start,
                col_offset=c_start,
                chunk_index=chunk_index,
                ping_offset=ping_offset,
                tile_row=r,
                tile_col=c
            )
            tiles.append(info)

    logger.info(f"Generated {len(tiles)} tiles.")
    return tiles
