#!/usr/bin/env python3
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@||
"""
---
<(META)>:
        docid:
        name:
        description: >
        version: 0.0.0.0.0.0
        authority: filesystem
        security: seclvl2
        <(WT)>: -32
"""

# -*- coding: utf-8 -*
# ======================================Standard Library Modules======================================================||
from os.path import abspath, dirname, join
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

# ======================================3rd Party Library Modules=====================================================||


# ======================================Solutions Brewer Library Modules==============================================||
from kahndor import kahndor
from kahndor.logma import Logma
from pyffice import pyffice
from pyffice.config.config import PyfficeConfig

# ====================================================================================================================||
HERE = join(dirname(__file__), "")  # ||
log = True
logma = Logma(__name__)
if not log:
    logma.off()
# ====================================================================================================================||
PXCFG = join(HERE, "_data_", "web_config.yaml")


class PyfficeWebConfig(PyfficeConfig):
    """"""

    def __init__(self, cfg=None, parent=None) -> None:
        """"""
        self.parent = parent
        super().__init__(cfg)
        self.config.override(kahndor.Instruct(PXCFG).select("PyfficeConfig").override(cfg))
        self.library = None
        self.profile_manager = None

    def load_document(self, document=None) -> Any:
        """ """
        document = document or {}
        document = self.config.override(document).get("document", {}) or {}
        super().load_document(document)
        return self

    def save(self, path=None, format_=None, encrypt=None):
        """"""
        super().save(path, format_, encrypt)

    def to_dict(self):
        """"""
        doc = super().to_dict()
        return self._canonicalize(doc)


# ====================================================================================================================||

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@||
