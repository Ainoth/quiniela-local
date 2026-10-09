"""Medición reproducible del motor v0.1; no utiliza datos del usuario."""
import json
import platform
import os
from pathlib import Path
import sys
import threading
import time
import tracemalloc
from quiniela_studio.engine import generate, Cancelled
from quiniela_studio import __version__

tracemalloc.start()
start=time.perf_counter()
columns=generate(('1X2',)*10+('1',)*4,'M0')
elapsed=time.perf_counter()-start
_,peak=tracemalloc.get_traced_memory()
tracemalloc.stop()
event=threading.Event();threading.Timer(.02,event.set).start()
start=time.perf_counter()
try:generate(('1X2',)*10+('1',)*4,'M0',cancelled=event.is_set)
except Cancelled:pass
latency=time.perf_counter()-start
print(json.dumps(dict(version=__version__,python=sys.version.split()[0],os=platform.platform(),
                     cpu=next((line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')), platform.processor()) if Path('/proc/cpuinfo').exists() else platform.processor(),
                     ram_gib=round(os.sysconf('SC_PAGE_SIZE')*os.sysconf('SC_PHYS_PAGES')/1024**3,2) if hasattr(os,'sysconf') else None,columns=len(columns),elapsed_seconds=round(elapsed,4),
                     peak_python_mib=round(peak/1024**2,3),cancel_seconds=round(latency,4)),indent=2))
assert peak<256*1024**2
assert latency<1
