"""My Notebook backend."""

import os

# Unstructured OSS ships usage analytics and a promo banner: turn both off
# before any unstructured import (we do not send course data anywhere).
os.environ.setdefault("SCARF_NO_ANALYTICS", "true")
os.environ.setdefault("DO_NOT_TRACK", "true")
os.environ.setdefault("UNSTRUCTURED_DISABLE_NOTICE", "1")
