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
from urllib.parse import urlparse, urljoin, urlencode

# ======================================3rd Party Library Modules=====================================================||
import furl

# ======================================Solutions Brewer Library Modules==============================================||
from kahndor import kahndor
from kahndor.logma import Logma
from pyffice.document import PyfficeUnit, PyfficeDocumentManager
from pycurity.pyhash import text_hashing_function
from typing import Any
from typing_extensions import Self

# ====================================================================================================================||
here = join(dirname(__file__), "")  # ||
log = True
logma = Logma(__name__)
logma.off()

# ====================================================================================================================||
pxcfg = join(here, "_data_", "url.yaml")
HOMEPAGE = "https://www.pyffice.com/"


class PyfficeURL(PyfficeUnit):
    SERIALIZATION_VERSION = (1, 0, 0)
    """URL handling and parsing functionality for Pyffice system."""

    # URL scheme constants
    HTTP_PREFIX = "http://"
    HTTPS_PREFIX = "https://"
    HTTP_PREFIX_LEN = 7
    HTTPS_PREFIX_LEN = 8

    # Default values
    DEFAULT_SEARCH_URL = "https://www.duckduckgo.com/"

    def __init__(self, cfg=None) -> None:
        """Initialize PyfficeURL with configuration."""
        super().__init__(cfg)
        self.config.override(kahndor.Instruct(pxcfg).select("PyfficeURL").override(cfg))

        # Initialize all URL-related attributes
        self._initialize_attributes()

        if self.active_url is not None:
            self._parse(self.active_url)
        self.doc_type = "url"

    def check_pattern(self, pattern) -> Any:
        """Check if pattern exists in any URL variant."""
        urls_to_check = [self.given_url, self.active_url, self.found_url]
        return any(pattern in url for url in urls_to_check if url)

    def expand_url(self, url) -> Any:
        """Add http:// prefix if no scheme is present."""
        if not (url.startswith(self.HTTP_PREFIX) or url.startswith(self.HTTPS_PREFIX)):
            url = f"{self.HTTP_PREFIX}{url}"
        return url

    def filter(self, url) -> Any:
        """Apply filters to URL."""
        if not self.filters:
            return False

        for filter_ in self.filters:
            if filter_ in url:
                return url
        return False

    def get_domain_and_subdomain(self, netloc) -> Any:
        """Extract domain and subdomain from netloc."""
        if ":" in netloc:  # Remove port number if present
            netloc = netloc.split(":")[0]

        parts = netloc.split(".")
        if len(parts) >= 3:  # Has subdomain
            subdomain = ".".join(parts[:-2])
            domain = ".".join(parts[-2:])
        elif len(parts) == 2:  # No subdomain
            subdomain = None
            domain = netloc
        else:  # Malformed netloc
            subdomain = None
            domain = None
        return domain, subdomain

    def get_parameters(self) -> Any:
        """Get URL parameters."""
        self._ensure_parsed()
        return self.parameters

    def get_domain(self) -> Any:
        """Get domain component."""
        self._ensure_parsed()
        return self.domain

    def get_sub_domain(self) -> Any:
        """Get subdomain component."""
        self._ensure_parsed()
        return self.sub_domain

    def get_url(self) -> Any:
        """Build and return processed URL."""
        url = f"{self.scheme}{self.netloc}{self.path}{self.parameters}{self.query}{self.fragment}"
        if self.block_ads and hasattr(self, "block_patterns"):
            self.check_pattern(self.block_patterns)
        if self.redirect_affiliates and hasattr(self, "affiliate_patterns"):
            self.check_pattern(self.affiliate_patterns)
        return self.found_url

    def initialize_ad_blocking(self) -> Self:
        """Enable ad blocking."""
        return self.set_block_ads(True)

    def is_changed(self) -> Any:
        """Check if URL has been modified."""
        return self.found_url != self.given_url

    def is_valid(self) -> Any:
        """Validate URL structure."""
        return self.active_url is not None and self.get_domain() is not None

    def load_unit(self, unit=None) -> Self:
        """Load configuration from unit dictionary."""
        if unit is None:
            unit = self.config.dikt.get("unit", {})

        logma.info(f"Unit {unit}")
        super().load_unit(unit)

        # Load URL attributes
        self._load_url_attributes(unit)

        # Set active URL
        self.set_active_url(self.given_url)
        active_url = unit.get("active_url", unit.get("url", None))
        if active_url is not None:
            self.set_active_url(active_url)

        # Set geofence
        self.set_geofence(unit.get("geofence_region", None), unit.get("geofence_active", False))

        # Parse the final URL
        parse_url = self.active_url or self.config.dikt.get("url", self.default_url)
        self._parse(parse_url)

        return self

    def sanitize_url(self) -> Self:
        """Ensure URL uses HTTPS and apply filters."""
        if self.found_url and not self.found_url.startswith("https"):
            self.found_url = f"https://{self.found_url}"
        self.found_url = self.filter(self.found_url)
        return self

    # Simplified setter methods using the generic pattern
    def set_active_url(self, url=None) -> Self:
        """Set active URL with validation and expansion."""
        if url is None:
            url = self.default_url

        if url != self.active_url:
            self.add_change("active_url", self.active_url, url)
            self.active_url = self.expand_url(url)
            self.set_secure()

        logma.info(f"Active Url {self.active_url}")
        return self

    def set_block_ads(self, block_ads) -> Self:
        """Set ad blocking preference."""
        return self._set_attribute("block_ads", block_ads)

    def set_block_adult(self, block_adult) -> Self:
        """Set adult content blocking preference."""
        return self._set_attribute("block_adult", block_adult)

    def set_default_url(self, url) -> Self:
        """Set default URL."""
        return self._set_attribute("default_url", url)

    def set_domain(self, domain) -> Self:
        """Set domain component."""
        return self._set_attribute("domain", domain)

    def set_filters(self, filters) -> Self:
        """Set URL filters."""
        return self._set_attribute("filters", filters)

    def set_fragment(self, fragment) -> Self:
        """Set URL fragment."""
        return self._set_attribute("fragment", fragment)

    def set_geofence(self, region, active=True) -> Self:
        """Set geofencing configuration."""
        self.geofence_active = active
        self.geofence_region = region
        return self

    def set_given_url(self, url=None) -> Self:
        """Set the originally given URL."""
        if url != self.given_url:
            self.add_change("given_url", self.given_url, url)
            self.given_url = url
        logma.info(f"Given URL {self.given_url}")
        return self

    def set_hostname(self, hostname) -> Self:
        """Set hostname component."""
        return self._set_attribute("hostname", hostname)

    def set_level_of_trust(self, level_of_trust) -> Self:
        """Set trust level."""
        return self._set_attribute("level_of_trust", level_of_trust)

    def set_link_style(self, link_style) -> Self:
        """Set link style preference."""
        return self._set_attribute("link_style", link_style)

    def set_netloc(self, netloc) -> Self:
        """Set network location."""
        return self._set_attribute("netloc", netloc)

    def set_path(self, path) -> Self:
        """Set URL path."""
        return self._set_attribute("path", path)

    def set_parameters(self, parameters) -> Self:
        """Set URL parameters."""
        return self._set_attribute("parameters", parameters)

    def set_parsed(self, parsed) -> Self:
        """Set parsed status."""
        return self._set_attribute("parsed", parsed)

    def set_query(self, query) -> Self:
        """Set URL query string."""
        return self._set_attribute("query", query)

    def set_password(self, password) -> Self:
        """Set password with hashing."""
        if password is None:
            password = ""
        return self._set_attribute("password", password, text_hashing_function)

    def set_port(self, port) -> Self:
        """Set port number."""
        return self._set_attribute("port", port)

    def set_redirect_affiliates(self, redirect_affiliates) -> Self:
        """Set affiliate redirection preference."""
        return self._set_attribute("redirect_affiliates", redirect_affiliates)

    def set_secure(self) -> Self:
        """Convert URL to HTTPS."""
        logma.info(f"Active Url {self.active_url}")
        if self.active_url.startswith(self.HTTP_PREFIX):
            self.secure_url = self.active_url.replace(self.HTTP_PREFIX, self.HTTPS_PREFIX)
        elif self.active_url.startswith(self.HTTPS_PREFIX):
            self.secure_url = self.active_url
        else:
            self.secure_url = f"{self.HTTPS_PREFIX}{self.active_url}"
        self.active_url = self.secure_url
        return self

    def set_scheme(self, scheme) -> Self:
        """Set URL scheme."""
        return self._set_attribute("scheme", scheme)

    def set_sub_domain(self, sub_domain) -> Self:
        """Set subdomain component."""
        return self._set_attribute("sub_domain", sub_domain)

    # def set_twofdns(self, twofdns):
    #     """Set TwoFDNS preference."""
    #     return self._set_attribute("twofdns", twofdns)

    def set_username(self, username) -> Self:
        """Set username component."""
        return self._set_attribute("username", username)

    def set_whois(self, whois) -> Self:
        """Set WHOIS information."""
        self.whois = whois
        return self

    def remove_www(self) -> Self:
        """Remove www prefix from URL."""
        if self.active_url.startswith("www."):
            self.no_www = self.active_url[4:]
        elif self.active_url.startswith("http://www."):
            self.no_www = f"http://{self.active_url[11:]}"
        elif self.active_url.startswith("https://www."):
            self.no_www = f"https://{self.active_url[12:]}"
        return self

    def validate(self) -> None:
        """Ensure that URL is validly constructed."""
        pass

    def verify(self) -> Any:
        """Attempt to ensure web address is correct."""
        if hasattr(self, "library") and self.library.verify(self.active_url):
            return True
        return False

    def verify_full_address(self, url) -> Any:
        """Verify full URL address."""
        return url

    def _ensure_parsed(self) -> None:
        """Ensure URL is parsed before accessing components."""
        if not self.parsed and self.active_url:
            self._parse(self.active_url)

    def _initialize_attributes(self) -> None:
        """Initialize all URL component attributes to None."""
        url_attributes = [
            "active_url",
            "block_ads",
            "block_adult",
            "default_url",
            "domain",
            "filters",
            "found_url",
            "fragment",
            "geofence_active",
            "geofence_region",
            "given_url",
            "hostname",
            "level_of_trust",
            "link_style",
            "netloc",
            "path",
            "parameters",
            "parsed",
            "query",
            "password",
            "port",
            "redirect_affiliates",
            "scheme",
            "sub_domain",
            "twofdns",
            "username",
            "whois",
        ]
        for attr in url_attributes:
            setattr(self, attr, None)

    def _load_url_attributes(self, unit) -> None:
        """Load URL-specific attributes from unit configuration."""
        url_mappings = {
            "given_url": unit.get("original_path", unit.get("url", self.default_url)),
            "block_ads": unit.get("block_ads", False),
            "block_adult": unit.get("block_adult", True),
            "default_url": unit.get("default_url", self.DEFAULT_SEARCH_URL),
            "domain": unit.get("domain", ""),
            "filters": unit.get("filters", []),
            "fragment": unit.get("fragment", ""),
            "hostname": unit.get("hostname", ""),
            "level_of_trust": unit.get("level_of_trust", 0),
            "link_style": unit.get("link_style", "path"),
            "netloc": unit.get("netloc", ""),
            "path": unit.get("path", ""),
            "parameters": unit.get("parameters", ""),
            "query": unit.get("query", ""),
            "password": unit.get("password", ""),
            "port": unit.get("port", ""),
            "redirect_affiliates": unit.get("redirect_affiliates", True),
            "scheme": unit.get("scheme", ""),
            "sub_domain": unit.get("sub_domain", ""),
            # "twofdns": unit.get("twofdns", False),
            "username": unit.get("username", ""),
        }

        for attr, value in url_mappings.items():
            getattr(self, f"set_{attr}")(value)

    def _parse(self, url) -> Self:
        """Parse URL into components."""
        try:
            parsed = urlparse(url)
        except (ValueError, TypeError) as e:
            logma.warning(f"Failed to parse URL {url}: {e}")
            return self

        # Set netloc and derive domain/subdomain
        self._safe_set_attribute("set_netloc", parsed.netloc)

        try:
            domain, sub = self.get_domain_and_subdomain(self.netloc)
            self._safe_set_attribute("set_domain", domain)
            self._safe_set_attribute("set_sub_domain", sub)
        except (ValueError, AttributeError) as e:
            logma.warning(f"Error parsing domain/subdomain: {e}")

        # Set all other URL components
        url_components = [
            ("set_scheme", parsed.scheme),
            ("set_hostname", parsed.hostname),
            ("set_port", parsed.port),
            ("set_path", parsed.path),
            ("set_query", parsed.query),
            ("set_parameters", parsed.params),
            ("set_fragment", parsed.fragment),
            ("set_username", parsed.username),
            ("set_password", parsed.password),
        ]

        for setter_name, value in url_components:
            self._safe_set_attribute(setter_name, value)

        self._safe_set_attribute("set_parsed", True)
        return self

    def _safe_set_attribute(self, setter_name, value) -> None:
        """Safely set attribute with error handling."""
        try:
            getattr(self, setter_name)(value)
        except (AttributeError, TypeError) as e:
            logma.warning(f"Error setting {setter_name}: {e}")

    def _set_attribute(self, attr_name, new_value, transform_func=None) -> Self:
        """Generic setter method to reduce code duplication."""
        if transform_func:
            new_value = transform_func(new_value)

        current_value = getattr(self, attr_name)
        if new_value != current_value:
            self.add_change(attr_name, current_value, new_value)
            setattr(self, attr_name, new_value)
        return self


class PyfficeURLLibrary(PyfficeDocumentManager):
    """URL Library is a data object for integrating affiliate links into the web apps and browsing features provided
    SERIALIZATION_VERSION = (1, 0, 0)
    within Pyffice"""

    def __init__(self, cfg=None) -> None:
        """Initialize URL Library with configuration."""
        super().__init__(cfg)
        self.config.override(kahndor.Instruct(pxcfg).select("PyfficeURLLibrary").override(cfg))
        self.urls = None
        self.affiliate_patterns = None
        self.block_patterns = None

    def add_url(self, url) -> Self:
        """Add a URL to the library."""
        self.add_document(PyfficeURL(url))
        return self

    def _find_link(self, link, urllib) -> Self:
        """Common method to find and process links."""
        self.found_data = urllib.search(link)
        self.found_link = self.found_data[self.link_style]
        self.sanitize_link()
        return self

    def find_affiliate_link(self, link=None, urllib=None) -> Self:
        """Find and process affiliate links."""
        self.given_link = link
        return self._find_link(link, urllib)

    def find_webapp_link(self, link=None, urllib=None) -> Self:
        """Find and process webapp links."""
        if link is None:
            link = self.given_link
        return self._find_link(link, urllib)

    def get_malware_ad_patterns(self) -> None:
        """Get malware and ad patterns from services."""
        for service in self.services:
            if service.get("key", False):
                self.given_malware += get_data(service)

    def get_url_by_id(self, url_id) -> Any:
        """Get URL by its ID."""
        url = self.known_urls[url_id].found_url
        return url

    def get_urls(self) -> None:
        """Get URLs from database."""
        table = "urls"
        cfg = {"table": table}
        params = {table: {"WHERE": {"EQUAL": {"substitute_bit": 1}}}}
        reader = self.app.model.store.docs["db"].read(cfg, params)
        self.urls = next(reader).dikt[table]["df"]

    def load_document(self, document=None) -> Self:
        """Load document configuration."""
        if document is None:
            document = self.config.dikt.get("document", {})
            if document is None:
                document = {}
        super().load_document(document)
        self.set_urls(document.get("urls", {}))
        return self

    def lookup(self, code) -> Self:
        """Lookup URL by code."""
        if self.known_urls is None:
            self.known_urls = self.app.model.store["db"].get_urls()
        url = self.known_urls.get(code, None)
        if url is not None:
            self.url = url
        return self

    def search(self, url) -> Any:
        """Search for URL in the library."""
        if self.urls is None:
            self.get_urls()
        logma.info(f"URLs {self.urls}")
        url_data = self.urls[self.urls["code_txt"] == url]
        logma.info(f"URL Data {url_data}")
        if not url_data.empty:
            url_row = url_data.iloc[0]
            return url_row

    def set_affiliate_patterns(self, patterns) -> Self:
        """Set affiliate patterns."""
        if patterns != self.affiliate_patterns:
            self.add_change("affiliate_patterns", self.affiliate_patterns, patterns)
            self.affiliate_patterns = patterns
        return self

    def set_block_patterns(self, patterns) -> Self:
        """Set block patterns."""
        if patterns != self.block_patterns:
            self.add_change("block_patterns", self.block_patterns, patterns)
            self.block_patterns = patterns
        return self

    def set_urls(self, urls) -> Self:
        """Set URLs collection."""
        if urls != self.urls:
            self.add_change("urls", self.urls, urls)
            self.urls = urls
        return self

    def update_from_service(self, service_name) -> None:
        """Update URL data from external service."""
        stone = self.get_stone(service_name)
        data = stone.get_urls(cfg)

    # def verify(self, url):
    #     """Verify if URL is safe and not blocked."""
    #     if url not in self.block_patterns:
    #         if TwoFDNS(self.url):
    #             return True
    #     return False


# ====================================================================================================================||

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@||
