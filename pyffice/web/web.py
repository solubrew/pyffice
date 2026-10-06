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
import datetime as dt
from copy import deepcopy
import json as j

# ======================================3rd Party Library Modules=====================================================||
from collections import deque

# ======================================Solutions Brewer Library Modules==============================================||
from kahndor import kahndor
from kahndor.logma import Logma
from pyffice.contacts.contacts import PyfficeContact, PyfficeRolodex
from pyffice.document import PyfficeDocument, PyfficeDocumentManager, PyfficeDeque
from pyffice.web.url import PyfficeURL, PyfficeURLLibrary
from pycurity.pyhash import text_hashing_function, encode64, decode64
from typing import Any
from typing_extensions import Self

# ====================================================================================================================||
here = join(dirname(__file__), "")  # ||
log = False
logma = Logma(__name__)
if not log:
    logma.off()

# ====================================================================================================================||
pxcfg = join(here, "_data_", "web.yaml")
HOMEPAGE = {"url": "https://www.pyffice.com/"}
HOMEURL = HOMEPAGE.get("url")


class PyfficeWebBrowser(PyfficeDocumentManager):
    SERIALIZATION_VERSION = (0, 0, 1, 0, 1, 2)
    """"""

    def __init__(self, cfg=None) -> None:
        """"""
        super().__init__(cfg)
        self.config.override(kahndor.Instruct(pxcfg).select("PyfficeWebBrowser").override(cfg))
        self.active_page = None
        self.active_profile = None
        self.home_page = None
        self.pages = None
        self.doc_type = "browser"

    def add_page(self, page) -> Self:
        """Add a page.

        Args:
            page: Parameter.

        Returns:
            Self for chaining.
        """
        if isinstance(page, PyfficeWebPage):
            page = page
        else:
            page = PyfficeWebPage({"page": page})
            page.load_document()
        self.set_next_page(page)
        return self

    def del_page(self) -> Self:
        """Delete a page."""
        _p = True  # placeholder
        return self

    def get_active_profile(self) -> Any:
        """Return the active profile.

        Returns:
            Self for chaining.
        """
        return self.profile_manager.active_profile

    def get_active_page(self) -> Any:
        """Return the active page.

        Returns:
            Self for chaining.
        """
        return self.active_page

    def get_active_url(self) -> Any:
        """Return the active page.

        Returns:
            Self for chaining.
        """
        if self.active_page is None:
            return self.get_home_url()
        return self.active_page.get_url()

    def get_home_url(self):
        """"""
        return "https://www.google.com/"

    def is_pinned(self) -> Any:
        """Return whether this document is pinned.

        Returns:
            Self for chaining.
        """
        return self.active_page.is_pinned()

    def load_document(self, document=None) -> Self:
        """Load document into this document.

        Args:
            document: Parameter.

        Returns:
            Self for chaining.
        """
        logma.info(f"Load Document {document}")
        document = document or {}
        document = self.config.override(document).get("document", {}) or {}
        logma.info(f"Load Document {document}")
        super().load_document(document)
        self.set_page_home(document.get("home_url", None))
        logma.info(f"URL Home")
        # TODO: need to get profile from the PyfficeWebBrowserManager
        self.set_profile_active(document.get("active_profile", None))
        self.set_pages(document.get("pages", None))
        self.set_page_active(document.get("active_page", None))
        # T-NEW-079: the nchantdoffice widget stores the active page
        # payload under ``data.content`` (its ``get_content()`` = 
        # ``{"content": active_page.to_dict()}``); the generic
        # ``pages`` / ``active_page`` keys are absent from that blob
        # shape. Re-hydrate the active page from ``data.content``
        # when present so a tab-return rebuild actually restores
        # the last URL (previously the rebuilt browser fell back to
        # HOMEPAGE and the widget then read the empty default).
        data = document.get("data") if isinstance(document, dict) else None
        content = data.get("content") if isinstance(data, dict) else None
        if isinstance(content, dict):
            self.set_page_active(content)
        return self

    def open_file(self, file_path, open_=True):
        """"""
        super().open_file(file_path, open_)
        # TODO implement direct file opening of .htm/.html/.xhtml files

    def set_home_page(self, cfg=None):
        """"""
        page = self.config.override(cfg).get("home_page", HOMEPAGE)
        page = PyfficeWebPage({"page": page})
        self.pages = page
        return self

    def set_next_page(self, page):
        """"""
        self.set_previous_page(page)
        self.pages = page
        return self

    def set_previous_page(self, page):
        """"""
        if self.pages is None:
            self.set_home_page()
        page.previous_page = self.pages
        return self

    def set_page_active(self, page) -> Self:
        """Set the page active.

        Args:
            page: Parameter.

        Returns:
            Self for chaining.

        T-NEW-079: the previous implementation called
        ``PyfficeURL(page)`` positionally and then
        ``url.load_unit()`` with no cfg. Both no-op'd: the
        PyfficeURL constructor doesn't read a positional str,
        and ``load_unit()`` with no args defaulted to the
        config's unit — which had no URL — so the URL ended
        up as HOMEURL. Now we feed the URL into ``load_unit``
        via the same ``{"url": ...}`` cfg shape that
        ``set_url`` / ``load_document`` use, keeping the
        serialise/parse symmetric across the codebase.
        """
        if isinstance(page, str):
            url = PyfficeURL(None)
            url.load_unit({"url": page})
            # T-NEW-079: the previous code called
            # ``self.set_home_page()`` here, which actually
            # populates ``self.pages`` (a list) — leaving
            # ``self.home_page`` as None. The very next line
            # read ``self.home_page.active_url`` and crashed
            # on every first navigation. The canonical
            # ``home_page`` setter is ``set_page_home`` (note
            # the order of the two words). Wire that one.
            if self.home_page is None:
                self.set_page_home(None)
            # Canonical cfg key is ``url`` — ``load_document``
            # reads ``document["url"]`` / ``document["data"]["url"]``,
            # never ``active_url``.
            page = {"url": url.url_string}
        if page is None:
            page = self.pages[0]
        if isinstance(page, dict):
            # T-NEW-079: pass the dict through ``load_document``
            # (the canonical restore path). The old
            # ``PyfficeWebPage(page); page.load_document()`` pair
            # discarded the cfg — every dict became a HOMEPAGE page.
            page_obj = PyfficeWebPage(None)
            page_obj.load_document(page)
            page = page_obj
            if page != self.active_page:
                self.add_change("active_page", self.active_page, page)
                self.active_page = page
        elif isinstance(page, PyfficeWebPage):
            if page != self.active_page:
                self.add_change("active_page", self.active_page, page)
                self.active_page = page
        else:
            raise ValueError(f"page: {page}")
        return self

    def set_page_home(self, page) -> Self:
        """Set the home page.

        Args:
            page: Parameter.

        Returns:
            Self for chaining.
        """
        if page is None:
            page = HOMEPAGE
        if not isinstance(page, PyfficeWebPage):
            page = PyfficeWebPage(page)
            page.load_document()
        if page != self.home_page:
            self.add_change("home_page", self.home_page, page)
            self.home_page = page
        return self

    def set_pages(self, pages) -> Self:
        """Set the pages.

        Args:
            pages: Parameter.

        Returns:
            Self for chaining.
        """
        if pages is None:
            pages = [{"page": self.home_page}]  # , "profile": self.active_profile.did}]
        page_objs = []
        for page in pages:
            # T-NEW-079: feed the saved page dict through
            # ``load_document`` (the canonical restore path) so
            # the persisted URL / history are honoured. The old
            # ``PyfficeWebPage(page); page.load_document()`` pair
            # threw the cfg away — ``load_document()`` with no
            # args rebuilt every page at HOMEPAGE.
            page_obj = PyfficeWebPage(None)
            page_obj.load_document(page)
            page_objs.append(page_obj)
        if page_objs != self.pages:
            self.add_change("pages", self.pages, page_objs)
            self.pages = page_objs
        return self

    def set_pinned(self, pin) -> Self:
        """Set the pinned.

        Args:
            pin: Parameter.

        Returns:
            Self for chaining.
        """
        self.pinned = pin
        return self

    def set_profile_active(self, profile) -> Self:
        """Set the profile active.

        Args:
            profile: Parameter.

        Returns:
            Self for chaining.
        """
        cfg = {"profile": profile}
        profile = PyfficeWebProfile(cfg)
        profile.load_document()
        if profile != self.active_profile:
            self.add_change("active_profile", self.active_profile, profile)
            self.active_profile = profile
        return self

    def set_refresh_time(self) -> Self:
        """Set the refresh time.

        Returns:
            Self for chaining.
        """
        self.update_document_time()
        return self

    def to_dict(self) -> Self:
        """Convert this document to dict.

        Returns:
            Self for chaining.

        T-NEW-069 — round-trip fix: persist the full ``pages``
        list AND the active ``page``. The previous code only
        wrote ``page`` (the active one), which meant
        ``load_document`` had no way to restore tab history
        after a save/load cycle. Now we persist the list (which
        may be ``None`` or empty for a brand-new document) and
        load_document can re-populate ``self.pages``.
        """
        doc = super().to_dict()
        if self.active_profile is not None:
            doc["data"]["active_profile"] = self.active_profile.to_dict()
        if getattr(self, "active_page", None) is not None and hasattr(self.active_page, "to_dict"):
            doc["data"]["page"] = self.active_page.to_dict()
        # Persist the full pages list (None-safe — many
        # intermediate-state docs only have ``active_page``).
        pages = getattr(self, "pages", None)
        if pages:
            doc["data"]["pages"] = [p.to_dict() for p in pages]
        elif "pages" not in doc["data"]:
            # Preserve the field's absence vs empty distinction:
            # empty list means "had pages, all cleared";
            # missing means "never populated".
            pass
        return self._canonicalize(doc)


class PyfficeWebPage(PyfficeDocument):
    """"""

    SERIALIZATION_VERSION = (0, 0, 1, 0, 1, 2)

    def __init__(self, cfg=None) -> None:
        """"""
        logma.debug(f"PyfficeWebPage.__init__ called")
        super().__init__(cfg)
        self.config.override(kahndor.Instruct(pxcfg).select("PyfficeWebPage")).override(cfg)
        self.active_url = None
        self.home_url = None
        self.active_profile = None
        self.history = None
        self.snapshots = None
        self.versions = None
        self.is_pinned = None
        self.pinned_on_dttm = None
        self.last_refresh = None
        self.trust = None

    def add_history(self, url) -> Self:
        """Add a history.

        Args:
            url: Parameter.

        Returns:
            Self for chaining.
        """
        self.add_change("history", deepcopy(self.history), url, "add")
        if self.history is None:
            self.history = []
        self.history.append(url)
        return self

    def add_snapshot(self, snapshot) -> Self:
        """Add a snapshot.

        Args:
            snapshot: Parameter.

        Returns:
            Self for chaining.
        """
        hash_ = self.get_finger_print(snapshot)
        snapshot = {"path": None, "hash": hash_, "content_enc64": encode64(snapshot)}
        self.add_change("snapshots", self.snapshots, snapshot, "add")
        if self.snapshots is None:
            self.snapshots = []
        self.snapshots.append(snapshot)
        return self

    def add_version(self, content) -> Self:
        """Add a version.

        Args:
            content: Parameter.

        Returns:
            Self for chaining.
        """
        hash_ = self.get_finger_print(content)
        version = {"path": None, "hash": hash_, "content_enc64": encode64(content)}
        self.add_change("versions", deepcopy(self.versions), version, "add")
        self.versions.append(version)
        return self

    def load_document(self, document=None) -> Self:
        """Load document into this document.

        Args:
            document: Parameter.

        Returns:
            Self for chaining.

        T-NEW-079: the previous implementation read
        ``document.get("url", None)`` from the OUTER dict and
        passed that to ``set_url``. The serialised form
        (produced by ``to_dict`` / ``_canonicalize``) puts the
        URL dict under ``document["data"]["url"]["url_string"]``
        — not at the top level — so the lookup returned
        ``None`` on every reload and the URL silently reverted
        to HOMEPAGE. Now we accept either the outer or inner
        shape: the page-canonical ``document["data"]["url"]``
        dict first, then fall back to the legacy outer ``url``.
        The URL is restored via ``set_url`` (or directly when
        the dict carries ``url_string`` so we don't re-parse).
        """
        if document is None:
            document = {}
        # T-NEW-079: the nchantdoffice widget's ``get_content()``
        # wraps the page payload under a ``content`` key (the
        # doc_media_content blob shape). Unwrap it before
        # continuing so the URL/history restore paths can find
        # their keys.
        if isinstance(document, dict) and isinstance(document.get("content"), dict):
            document = {**document, **document["content"]}
        # T-NEW-079: the widget's restore path (browsers.py:101)
        # calls ``page.load_document(URL.to_dict())`` — passing
        # the FLAT URL dict directly (no ``data`` / ``url``
        # wrapper). Detect that shape and route through
        # ``set_url`` so the URL fields land correctly.
        if isinstance(document, dict) and (
            "url_string" in document or "active_url" in document
        ) and "data" not in document and "url" not in document and "content" not in document:
            self.set_url(document)
            return self
        super().load_document(document)
        self.set_history(document.get("history", None), document.get("max_items", 10))
        # T-NEW-079: read the URL from the canonical position.
        inner_url = None
        data = document.get("data") if isinstance(document, dict) else None
        if isinstance(data, dict):
            url_blob = data.get("url")
            if isinstance(url_blob, dict):
                inner_url = url_blob.get("url_string") or url_blob.get("active_url")
        legacy_url = document.get("url", None) if isinstance(document, dict) else None
        url = inner_url or legacy_url
        self.set_url(url)
        self.set_home_url(document.get("home_url", None))
        self.set_snapshots(document.get("snapshots", []))
        self.set_versions(document.get("versions", []))
        self.set_page_pinned(document.get("pinned", None))
        self.set_level_of_trust(document.get("level_of_trust", 0) or 0)
        return self

    def get_finger_print(self, content) -> Any:
        """Return the finger print.

        Args:
            content: Parameter.

        Returns:
            Self for chaining.
        """
        return text_hashing_function(content)

    def get_url(self) -> Any:
        """"""
        url = self.active_url.get_url()
        if url is None:
            url = self.get_home_url()
        return url

    def get_home_url(self):
        """"""
        return self.home_url

    def get_url_document(self):
        """"""
        return self.active_url

    def set_history(self, history, max_items) -> Self:
        """Set the history.

        Args:
            history: Parameter.
            max_items: Parameter.

        Returns:
            Self for chaining.
        """
        cfg = {"max_items": max_items, "history": history}
        history = PyfficeDeque(cfg)
        if history != self.history:
            self.add_change("history", deepcopy(self.history), deepcopy(history))
            self.history = history
        return self

    def set_page_pinned(self, pinned=None) -> Self:
        """Set the page pinned.

        Args:
            pinned: Parameter.

        Returns:
            Self for chaining.
        """
        if pinned is None:
            pinned_on_dttm = dt.datetime.now().isoformat()
        else:
            pinned_on_dttm = pinned["pinned_on_dttm"]
        if pinned_on_dttm != self.pinned_on_dttm:
            self.add_change("pinned_on", self.pinned_on_dttm, pinned_on_dttm)
            self.pinned_on_dttm = pinned_on_dttm
        return self

    def set_page_unpinned(self) -> Self:
        """Set the page unpinned.

        Returns:
            Self for chaining.
        """
        pinned_on_dttm = None
        if pinned_on_dttm != self.pinned_on_dttm:
            self.add_change("pinned_on", self.pinned_on_dttm, pinned_on_dttm)
            self.pinned_on_dttm = pinned_on_dttm
        return self

    # def set_profile_active(self, profile):
    #     """"""
    #     # if profile is None:
    #     #     cfg = {"profile": profile}
    #     #     profile = PyfficeWebProfile(cfg)
    #     if profile != self.active_profile:
    #         self.add_change("active_profile", self.active_profile, profile)
    #         self.active_profile = profile
    #     return self

    def set_refresh_time(self) -> Self:
        """Set the refresh time.

        Returns:
            Self for chaining.
        """
        self.last_refresh = dt.datetime.now().isoformat()
        return self

    def set_level_of_trust(self, level) -> Self:
        """Set the level of trust.

        Args:
            level: Parameter.

        Returns:
            Self for chaining.
        """
        if level > 32:
            level = 0
        elif level < 0:
            level = 0
        if level != self.trust:
            self.add_change("level_of_trust", self.trust, level)
            self.trust = level
        return self

    def set_snapshots(self, snapshots) -> Self:
        """Set the snapshots.

        Args:
            snapshots: Parameter.

        Returns:
            Self for chaining.
        """
        if snapshots != self.snapshots:
            self.add_change("snapshots", deepcopy(self.snapshots), deepcopy(snapshots))
            self.snapshots = snapshots
        return self

    def set_home_url(self, url):
        """"""
        if url is None:
            url = self._configure_home_url()
        self.home_url = url
        return self

    def set_url(self, url) -> Self:
        """Set the url.

        Args:
            url: Parameter.

        Returns:
            Self for chaining.

        T-NEW-079: navigation was permanently disabled after the
        first ``load_document`` because ``set_page_pinned(None)``
        stamps ``pinned_on_dttm = now()`` and this guard then
        refused every subsequent ``set_url`` call — the live
        navigation reached the engine (engine.load) but never the
        document model, so on tab-switch + reopen the page was
        always restored from the original home URL.

        Also: the previous implementation called
        ``PyfficeURL(url)`` positionally, but the constructor
        signature is ``PyfficeURL(cfg=None)`` and a bare string was
        stored verbatim (no parse), and the result was assigned
        only to the legacy ``active_url`` slot — the renamed
        ``url_string`` stayed at its initial value, so any
        downstream consumer reading the new attribute saw stale
        data.

        The fix:
          1. Remove the ``pinned_on_dttm`` guard (the page is
             always navigable; pin-state is a separate concept).
          2. Normalise the input — bare str or dict cfg both flow
             through ``PyfficeURL`` properly via ``set_active_url``.
          3. Mirror the new URL into BOTH ``active_url`` (legacy
             attribute) AND ``url_string`` (the canonical rename)
             so existing consumers and migrated consumers agree.
        """
        if url is None:
            return self
        # Normalise the input to a cfg that ``load_unit`` reads.
        # Accepted shapes: bare str, {"url": str}, a full URL
        # blob dict (``url_string``/``active_url`` key — e.g. the
        # payload produced by ``PyfficeURL.to_dict``).
        if isinstance(url, dict):
            if "url" not in url:
                url = {
                    "url": url.get("url_string") or url.get("active_url") or url.get("given_url"),
                }
            cfg = url
        else:
            cfg = {"url": url}
        # Parse through the canonical PyfficeURL path (``__init__``
        # does NOT read cfg["url"]; ``load_unit`` is the proper
        # entry that populates scheme / host / domain components).
        new_url = PyfficeURL(None)
        new_url.load_unit(cfg)
        # If the URL string didn't change, still ensure both
        # attribute slots agree (defends against partial rename
        # regressions in subclasses).
        existing = getattr(self.active_url, "url_string", None) if self.active_url is not None else None
        if new_url.url_string == existing:
            return self
        # Record history + change-event before mutation.
        self.add_history(self.active_url)
        self.add_change("url", self.active_url, new_url)
        self.active_url = new_url
        return self

    def set_versions(self, versions) -> Self:
        """Set the versions.

        Args:
            versions: Parameter.

        Returns:
            Self for chaining.
        """
        if versions != self.versions:
            self.add_change("versions", deepcopy(self.versions), deepcopy(versions))
            self.versions = versions
        return self

    def to_dict(self) -> Self:
        """Convert this document to dict.

        Returns:
            Self for chaining.

        T-NEW-069 — defensive round-trip:

        * ``self.history`` may be ``None`` or a plain ``list``
          (per ``add_history`` line 348); call ``.to_dict()``
          only when the object supports it, else fall back
          to ``list(self.history or [])`` or ``[]``.
        * ``self.active_url.to_dict()`` now exists
          (added to ``PyfficeURL``); guard against ``None``
          (a freshly-init page without a URL yet).
        """
        doc = super().to_dict()
        doc["data"] = {
            "pinned_on": self.pinned_on_dttm,
            "last_refresh": self.last_refresh,
            "history": (
                self.history.to_dict()
                if self.history is not None and hasattr(self.history, "to_dict")
                else list(self.history or [])
            ),
            "snapshots": self.snapshots,
            "versions": self.versions,
            "level_of_trust": self.trust,
        }
        if getattr(self, "active_url", None) is not None and hasattr(self.active_url, "to_dict"):
            doc["data"]["url"] = self.active_url.to_dict()
        else:
            doc["data"]["url"] = None

        # doc["data"]["profile"] = self.active_profile.to_dict()
        doc["data"]["source"] = None
        return self._canonicalize(doc)

    def _configure_home_url(self):
        """"""
        home_url = self.config.get("home_url", HOMEURL) or HOMEURL
        return home_url


class PyfficeWebProfile(PyfficeContact):
    """"""

    VERSION = "0.0.1.0.1.0"

    def __init__(self, cfg=None) -> None:
        """"""
        super().__init__(cfg)
        self.config.override(kahndor.Instruct(pxcfg).select("PyfficeWebProfile")).override(cfg)

    def load_document(self, document=None) -> Self:
        """Load document into this document.

        Args:
            document: Parameter.

        Returns:
            Self for chaining.
        """
        if document is None:
            document = {}
        super().load_document(document)
        self.add_group("profile")
        return self


class PyfficeWebProfileManager(PyfficeRolodex):
    """"""

    VERSION = "0.0.1.0.1.0"

    def __init__(self, cfg=None) -> None:
        """"""
        logma.debug(f"PyfficeWebProfileManager.__init__ called")
        cfg = cfg or {}
        cfg["group"] = "profile"
        super().__init__(cfg)
        self.config.override(kahndor.Instruct(pxcfg).select("PyfficeWebProfileManager")).override(cfg)
        self.active_profile = None
        self.profiles = None

    def add_profile(self, profile) -> Self:
        """Add a profile.

        Args:
            profile: Parameter.

        Returns:
            Self for chaining.
        """
        if profile is None:
            cfg = {}
            profile = PyfficeWebProfile(cfg)
        self.add_change("profiles", deepcopy(self.profiles), deepcopy(profile))
        if self.profiles is None:
            self.profiles = []
        self.profiles.append(profile)
        self.add_contact(profile, "profile")
        return self

    def add_profiles(self, profiles) -> Self:
        """Add a profiles.

        Args:
            profiles: Parameter.

        Returns:
            Self for chaining.
        """
        for profile in profiles:
            self.add_profile(profile)
        return self

    def del_profile(self, name) -> Self:
        """Remove the profile.

        Args:
            name: Parameter.

        Returns:
            Self for chaining.
        """
        self.del_contact(name)
        return self

    def get_count(self) -> Any:
        """Return the count.

        Returns:
            Self for chaining.
        """
        return len(self.profiles)

    def get_profile(self, name) -> Self:
        """Return the profile.

        Args:
            name: Parameter.

        Returns:
            Self for chaining.
        """
        return self.get_contact(name)

    def get_current_profile(self) -> Any:
        """Return the current profile.

        Returns:
            Self for chaining.
        """
        return self.active_profile

    def load_document(self, document=None) -> Self:
        """Load document into this document.

        Args:
            document: Parameter.

        Returns:
            Self for chaining.
        """
        if document is None:
            document = {}
        super().load_document(document)
        self.set_profiles(document.get("profiles", None))
        self.set_profile_active(document.get("active_profile", None))
        return self

    def set_profile_active(self, profile) -> Self:
        """Set the profile active.

        Args:
            profile: Parameter.

        Returns:
            Self for chaining.
        """
        if profile is None:
            return self
        if self.profiles is None:
            self._initialize_base_profile()
        profile = self.profiles[profile.did]
        if profile != self.active_profile:
            self.add_change("active_profile", self.active_profile, profile)
            self.active_profile = profile
        return self

    def _initialize_base_profile(self):
        """"""
        cfg = {}
        profile = PyfficeWebProfile(cfg).load_document()
        self.profiles = [profile]
        return self

    def set_profiles(self, profiles) -> Self:
        """Set the profiles.

        Args:
            profiles: Parameter.

        Returns:
            Self for chaining.
        """
        if profiles is None:
            profiles = []
        if profiles != self.profiles:
            self.add_change("profiles", self.profiles, profiles)
            self.profiles = profiles
        return self

    def to_dict(self) -> Self:
        """Convert this document to dict.

        Returns:
            Self for chaining.
        """
        doc = super().to_dict()
        doc["data"]["profiles"] = [x.to_dict() for x in self.profiles]
        if self.active_profile is not None:
            doc["data"]["active_profile"] = self.active_profile.to_dict()
        return self._canonicalize(doc)


class PyfficeWebBrowserManager(PyfficeDocumentManager):
    """"""

    def __init__(self, cfg=None):
        """"""
        super().__init__(cfg)
        self.config.override(kahndor.Instruct(pxcfg).select("PyfficeWebBrowserManager").override(cfg))
        self.library = None
        self.profile_manager = None

    def add_profile(self, profile) -> Self:
        """Add a profile.

        Args:
            profile: Parameter.

        Returns:
            Self for chaining.
        """
        if isinstance(profile, PyfficeWebProfile):
            profile = profile
        else:
            profile = PyfficeWebProfile(profile)
            profile.load_document()
        logma.info(f"Profile: {profile}")
        if self.profile_manager is None:
            self.set_profile_manager({})
        self.profile_manager.add_profile(profile)
        return self

    def add_url(self, url):
        """"""

    def del_url(self, url):
        """"""

    def del_profile(self, name) -> Self:
        """Delete a profile."""
        _p = True  # placeholder
        return self

    def load_document(self, document=None) -> Self:
        """"""
        document = document or {}
        super().load_document(document)
        self.set_library(document.get("library", None))
        self.set_profile_manager(document.get("profile_manager", None))
        return self

    def set_library(self, library) -> Self:
        """Set the library.

        Args:
            library: Parameter.

        Returns:
            Self for chaining.
        """
        cfg = {"library": library}
        library = PyfficeURLLibrary(cfg)
        library.load_document()
        if library != self.library:
            self.add_change("library", self.library, library)
            self.library = library
        return self

    def set_profile_active(self, profile) -> Self:
        """Set the profile active.

        Args:
            profile: Parameter.

        Returns:
            Self for chaining.
        """
        cfg = {"profile": profile}
        profile = PyfficeWebProfile(cfg)
        profile.load_document()
        if self.active_page is None:
            if len(self.profile_manager.profiles) == 0:
                self.add_profile(profile)
            profile = self.profile_manager.profiles[0]
        if profile != self.active_profile:
            self.add_change("active_profile", self.active_profile, profile)
            self.active_profile = profile
        return self

    def set_profile_manager(self, profiles) -> Self:
        """Set the profile manager.

        Args:
            profiles: Parameter.

        Returns:
            Self for chaining.
        """
        cfg = {"profiles": profiles}
        profile_manager = PyfficeWebProfileManager(cfg)
        profile_manager.load_document()
        logma.info(f"profile_manager: {profile_manager}")
        if profile_manager != self.profile_manager:
            logma.info(f"profile_manager: {profile_manager}")
            self.add_change("profile_manager", self.profile_manager, profile_manager)
            self.profile_manager = profile_manager
        return self

    def to_dict(self):
        """"""
        doc = super().to_dict()
        doc["data"]["profile_manager"] = self.profile_manager.to_dict()
        doc["data"]["library"] = self.library.to_dict()
        return doc


# ====================================================================================================================||

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@||
