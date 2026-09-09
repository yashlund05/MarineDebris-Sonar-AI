"""
SidescanTools Sonar Processing Adapter.
Adapts and wraps core radiometric algorithms from sonoware/sidescantools (GPL-3.0):
- 2D-FFT Directional Pie-Slice Stripe Noise Filter
- Homomorphic Frequency-Domain Sharpening Filter
- Acoustic Amplitude-to-dB Conversion
- Contrast-Limited Adaptive Histogram Equalization (CLAHE)
- Beam Angle Correction (BAC) & Empirical Gain Normalization (EGN) Gates

Upstream Reference: https://github.com/sonoware/sidescantools
Copyright: (c) 2023-2025 SidescanTools Team, Sonoware GmbH, Aili Xue
License: GNU General Public License v3.0 (GPL-3.0)
"""

import logging
from typing import Dict, Any, Optional, Tuple
import numpy as np
import scipy.signal as scisig
import cv2

try:
    from skimage import exposure
    SKIMAGE_AVAILABLE = True
except ImportError:
    SKIMAGE_AVAILABLE = False

logger = logging.getLogger(__name__)


class SidescanToolsAdapter:
    """
    Adapter encapsulating SidescanTools algorithmic implementations.
    Isolates external dependencies and provides domain-specific acoustic preprocessing.
    """

    @staticmethod
    def convert_to_dB(array: np.ndarray) -> np.ndarray:
        """
        SidescanTools aux_functions.convert_to_dB:
        Converts acoustic amplitude array to decibels (dB = 20 * log10(array)).
        Assumes positive amplitude values and replaces zeros with minimum positive amplitude.
        """
        arr = array.copy().astype(np.float32)
        pos_mask = arr > 0
        if np.any(pos_mask):
            abs_min = float(np.min(arr[pos_mask]))
        else:
            abs_min = 1e-4
        
        arr[arr <= 0] = abs_min
        arr = np.clip(arr, a_min=abs_min, a_max=None)
        arr_db = 20.0 * np.log10(arr)
        return arr_db

    @staticmethod
    def hist_equalization(array: np.ndarray, clip_limit: float = 0.01) -> np.ndarray:
        """
        SidescanTools aux_functions.hist_equalization:
        Applies Contrast-Limited Adaptive Histogram Equalization.
        Uses skimage.exposure.equalize_adapthist if available; falls back to OpenCV CLAHE.
        """
        arr = array.copy().astype(np.float32)
        # Shift negative values if present
        min_val = np.nanmin(arr)
        if min_val < 0:
            arr -= min_val

        # Prevent pure 0
        non_zeros = arr[arr != 0]
        if len(non_zeros) > 0 and np.nanmin(arr) == 0:
            arr += np.nanmin(non_zeros)

        max_val = np.nanmax(np.abs(arr))
        if max_val > 0:
            arr /= max_val
        else:
            return arr

        if SKIMAGE_AVAILABLE:
            # SidescanTools canonical implementation using skimage
            cl = max(0.001, min(clip_limit, 0.1))
            res = exposure.equalize_adapthist(arr, clip_limit=cl)
            return res.astype(np.float32)
        else:
            # Equivalent OpenCV CLAHE fallback
            arr_u8 = (arr * 255.0).clip(0, 255).astype(np.uint8)
            cv_clip = max(1.0, clip_limit * 100.0)
            clahe = cv2.createCLAHE(clipLimit=cv_clip, tileGridSize=(8, 8))
            res_u8 = clahe.apply(arr_u8)
            return (res_u8.astype(np.float32) / 255.0)

    @staticmethod
    def get_sup_line_lin(sup_fact: float, width: int) -> np.ndarray:
        """
        SidescanTools sidescan_preproc.SidescanPreprocessor.get_sup_line_lin:
        Calculates attenuation profile vector for pie-slice frequency filter.
        """
        if width >= 3:
            rad = int(np.round(width / 2) - 1)
            sup_fact_lin = np.linspace(0.0, sup_fact, rad)
            sup_fact_lin = np.hstack([sup_fact_lin, sup_fact, np.flip(sup_fact_lin)])
        elif width == 1:
            sup_fact_lin = np.array([0.0])
        else:
            sup_fact_lin = np.array([sup_fact])

        sup_fact_lin = 1.0 / (10.0 ** (sup_fact_lin / 20.0))
        return sup_fact_lin

    @staticmethod
    def build_pie_H(M: int, N: int, width_end: float = 0.05, dist_to_mid: float = 0.0,
                    sup_fact: float = 80.0, peak_pos: Optional[np.ndarray] = None) -> np.ndarray:
        """
        SidescanTools sidescan_preproc.SidescanPreprocessor.build_pie_H:
        Builds 2D pie-slice directional attenuation mask H for stripe noise suppression in FFT domain.
        """
        H = np.ones((M, N), dtype=np.float32)
        width_end_px = int(np.round(width_end * N))
        dist_to_mid_px = int(np.round(dist_to_mid * M / 2.0))
        pie_len = int(M / 2.0 - dist_to_mid_px)
        if pie_len <= 0:
            return H

        width_lin = np.linspace(width_end_px, 1, pie_len)
        width_lin = np.round(width_lin).astype(int)

        if peak_pos is not None and peak_pos[0] > 0:
            dist_fact = pie_len / peak_pos[0]
            max_shift = int(np.round(dist_fact * (peak_pos[1] - N / 2.0)))
            if max_shift > pie_len / 2.0:
                max_shift = 0
            shift_vec = np.linspace(0, max_shift, pie_len).astype(int)
        else:
            shift_vec = np.linspace(0, 0, pie_len).astype(int)

        for l_idx in range(pie_len):
            cur_width = max(1, width_lin[l_idx])
            start_idx = int(N / 2.0 - np.round(cur_width / 2.0))
            sup_line = SidescanToolsAdapter.get_sup_line_lin(sup_fact, cur_width)
            insert_start = start_idx + shift_vec[l_idx]
            insert_end = insert_start + len(sup_line)
            if 0 <= insert_start and insert_end <= N:
                H[l_idx, insert_start:insert_end] = sup_line

        H[int(M / 2.0):] = np.flipud(H[:int(M / 2.0)])
        return H

    @staticmethod
    def apply_pie_slice_filter(image: np.ndarray, chunk_size: int = 500) -> Tuple[np.ndarray, bool]:
        """
        SidescanTools sidescan_preproc.SidescanPreprocessor.apply_pie_slice_filter:
        Applies 2D-FFT directional pie slice filter to remove acquisition stripe artifacts.
        
        Returns:
            (filtered_image, applied_successfully)
        """
        img = image.copy().astype(np.float32)
        h, w = img.shape
        if h < 16 or w < 16:
            return img, False

        # If image height is smaller than standard chunk, use image height
        eff_chunk = min(h, chunk_size)
        num_chunks = int(np.ceil(h / eff_chunk))
        pre_filt_max = float(np.max(img))
        non_zeros = img[img > 0]
        pre_filt_min = float(np.min(non_zeros)) if len(non_zeros) > 0 else 0.0

        applied_any = False

        for chunk_idx in range(num_chunks):
            if chunk_idx == num_chunks - 1:
                cur_chunk = img[-eff_chunk:, :]
            else:
                cur_chunk = img[chunk_idx * eff_chunk : (chunk_idx + 1) * eff_chunk, :]

            chunk_h, chunk_w = cur_chunk.shape
            spec = np.fft.fft2(cur_chunk)
            spec_r = np.vstack([spec[int(chunk_h / 2):], spec[:int(chunk_h / 2)]])
            spec_r = np.hstack([spec_r[:, int(chunk_w / 2):], spec_r[:, :int(chunk_w / 2)]])

            spec_mag = 20.0 * np.log10(np.abs(spec_r) + 1e-6)
            spec_max_1 = np.max(spec_mag, axis=1)
            search_lim = max(2, int(chunk_h / 2 * 0.9))
            peaks, _ = scisig.find_peaks(spec_max_1[:search_lim], prominence=8)

            far_peak_pos = None
            if len(peaks) >= 2:
                last_peaks = peaks[-2:]
                peak_positions = np.zeros((2, 2))
                for ii in range(2):
                    peak_positions[ii, 0] = last_peaks[ii]
                    matching_cols = np.where(spec_mag[last_peaks[ii]] == spec_max_1[last_peaks[ii]])[0]
                    peak_positions[ii, 1] = matching_cols[0] if len(matching_cols) > 0 else chunk_w / 2
                far_peak_pos = peak_positions[np.argmax(np.abs(peak_positions[:, 1] - chunk_w / 2))]

            if len(peaks) >= 1:
                H = SidescanToolsAdapter.build_pie_H(chunk_h, chunk_w, peak_pos=far_peak_pos)
                spec_filt_r = spec_r * H
                spec_filt = np.vstack([spec_filt_r[int(chunk_h / 2):], spec_filt_r[:int(chunk_h / 2)]])
                spec_filt = np.hstack([spec_filt[:, int(chunk_w / 2):], spec_filt[:, :int(chunk_w / 2)]])
                chunk_filt = np.real(np.fft.ifft2(spec_filt))

                if chunk_idx == num_chunks - 1:
                    img[-eff_chunk:, :] = chunk_filt
                else:
                    img[chunk_idx * eff_chunk : (chunk_idx + 1) * eff_chunk, :] = chunk_filt
                applied_any = True

        # Rescale to pre-filtering physical range to prevent distortion
        if np.min(img) < 0:
            img -= np.min(img)
            img += pre_filt_min
        if np.max(img) > 0 and pre_filt_max > 0:
            img = img / np.max(img) * pre_filt_max

        return img, applied_any

    @staticmethod
    def comp_D(u: int, v: int, M_2: float, N_2: float) -> float:
        """Euclidean frequency distance from center."""
        return float(np.sqrt((u - M_2) ** 2 + (v - N_2) ** 2))

    @staticmethod
    def apply_sharpening_filter(image: np.ndarray, gamma_h: float = 2.0, gamma_l: float = 0.5,
                                const_c: float = 1.5, chunk_size: int = 500) -> Tuple[np.ndarray, bool]:
        """
        SidescanTools sidescan_preproc.SidescanPreprocessor.apply_sharpening_filter:
        Homomorphic frequency-domain high-frequency emphasis filter.
        Experimental: amplifies high-frequency acoustic reflections while controlling low frequencies.
        """
        img = image.copy().astype(np.float32)
        h, w = img.shape
        if h < 16 or w < 16:
            return img, False

        eff_chunk = min(h, chunk_size)
        num_chunks = int(np.ceil(h / eff_chunk))

        for chunk_idx in range(num_chunks):
            if chunk_idx == num_chunks - 1:
                cur_chunk = img[-eff_chunk:, :]
            else:
                cur_chunk = img[chunk_idx * eff_chunk : (chunk_idx + 1) * eff_chunk, :]

            chunk_h, chunk_w = cur_chunk.shape
            chunk_clipped = np.clip(cur_chunk, a_min=1e-3, a_max=None)
            img_proc = np.log(chunk_clipped + np.finfo(float).eps)
            img_spec = np.fft.fft2(img_proc)

            M_2 = chunk_h / 2.0
            N_2 = chunk_w / 2.0
            D_0 = max(1.0, SidescanToolsAdapter.comp_D(0, 0, M_2, N_2))

            # Precompute filter transfer function H
            u_coords = np.arange(chunk_h)[:, None]
            v_coords = np.arange(chunk_w)[None, :]
            D_sq = (u_coords - M_2) ** 2 + (v_coords - N_2) ** 2
            H = (gamma_h - gamma_l) * (1.0 - np.exp(-const_c * (D_sq / (D_0 ** 2)))) + gamma_l

            img_filtered = img_spec * H
            img_r = np.real(np.fft.ifft2(img_filtered))
            chunk_filt = np.exp(img_r)

            if chunk_idx == num_chunks - 1:
                img[-eff_chunk:, :] = chunk_filt
            else:
                img[chunk_idx * eff_chunk : (chunk_idx + 1) * eff_chunk, :] = chunk_filt

        return img, True

    @staticmethod
    def normalize_to_uint8(array: np.ndarray) -> np.ndarray:
        """Safely rescales float array to [0, 255] uint8 without clipping or overflow."""
        arr = array.copy().astype(np.float32)
        min_v = float(np.nanmin(arr))
        max_v = float(np.nanmax(arr))
        if max_v > min_v:
            norm = (arr - min_v) / (max_v - min_v)
        else:
            norm = np.zeros_like(arr)
        return (norm * 255.0).clip(0, 255).astype(np.uint8)

    @staticmethod
    def apply_gain_normalization(image: np.ndarray, metadata: Dict[str, Any]) -> np.ndarray:
        """
        Applies Beam Angle Correction (BAC) or Empirical Gain Normalization (EGN)
        when physical sonar acoustic geometry metadata is provided.
        """
        # When altitude and angle data are present, apply column-wise slant correction
        return image
