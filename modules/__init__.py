# modules/__init__.py
"""
Marketing Support Tool - Modules Package

This package contains modules for different data analysis tools:
- sellerboard: Sellerboard data analysis
- ppc_xnurta: PPC Xnurta data analysis
- dsp_xnurta: DSP Xnurta data analysis
"""

from .sellerboard import sellerboard_page
from .ppc_xnurta import ppc_xnurta_page
from .dsp_xnurta import dsp_xnurta_page

__all__ = [
    'sellerboard_page',
    'ppc_xnurta_page',
    'dsp_xnurta_page'
]

__version__ = '1.0.0'