"""
MetaboliteClassifier - Classification Engine
=============================================
Accepts raw metabolite names (string, list, or pandas Series/DataFrame column),
sanitizes them, resolves them via a multi-stage pipeline, and returns structured
classification results.

Usage example:
    from metabolite_classifier.engine import MetaboliteClassifier
    clf = MetaboliteClassifier(db_path="metabolites.db")
    results = clf.classify(["L-Glutamine", "beta-alanine", "Glucose"])
    print(results)
    clf.summary()
    clf.export("results.csv")
"""

import re
import time
import logging
import sqlite3
import unicodedata
import html
import json
import asyncio
from pathlib import Path

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
from datetime import datetime
from typing import Union, List, Optional, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

try:
    from rapidfuzz import fuzz, process as rfprocess
    FUZZY_BACKEND = "rapidfuzz"
except ImportError:
    try:
        from thefuzz import fuzz
        FUZZY_BACKEND = "thefuzz"
    except ImportError:
        FUZZY_BACKEND = None

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GREEK_TO_ASCII = {
    "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta",
    "ε": "epsilon", "ζ": "zeta", "η": "eta", "θ": "theta",
    "κ": "kappa", "λ": "lambda", "μ": "mu", "ν": "nu",
    "ξ": "xi", "π": "pi", "ρ": "rho", "σ": "sigma",
    "τ": "tau", "υ": "upsilon", "φ": "phi", "χ": "chi",
    "ψ": "psi", "ω": "omega",
    "Α": "alpha", "Β": "beta", "Γ": "gamma", "Δ": "delta",
}

ASCII_TO_GREEK = {v: k for k, v in GREEK_TO_ASCII.items()}

STEREO_PREFIXES = re.compile(
    r"\b(L|D|R|S|dl|rac|meso|cis|trans|[Ee][Rr]|[Ss][Ss]|[Rr][Ss])\s*[-–]\s*",
    re.IGNORECASE,
)

HTML_ENTITY_RE = re.compile(r"&[a-zA-Z]+;|&#\d+;|&#x[0-9a-fA-F]+;")
ARTIFACT_RE = re.compile(r"[;\[\]{}]$")
MULTI_WHITESPACE = re.compile(r"\s{2,}")

CONFIDENCE_MAP = {
    "exact": "high",
    "normalized": "medium",
    "api": "medium",
    "fuzzy": "low",
    "unresolved": "unresolved",
}

RESULT_COLUMNS = [
    "input_name",
    "resolved_name",
    "category",
    "secondary_categories",
    "confidence",
    "resolution_method",
    "source",
    "matched_synonym",
    "notes",
]

# ---------------------------------------------------------------------------
# Sanitizer
# ---------------------------------------------------------------------------


class Sanitizer:
    """
    Stateless sanitization pipeline for metabolite name strings.
    """

    # Common artifacts from OCR / copy-paste
    _TRAILING_ARTIFACTS = re.compile(r"[;,.\[\]{}]+$")
    _NBSP = re.compile(r"\xa0|\u00a0")
    _EM_DASH = re.compile(r"[\u2013\u2014]")
    _FANCY_QUOTES = re.compile(r"[\u2018\u2019\u201a\u201b]")
    _FANCY_DQUOTES = re.compile(r"[\u201c\u201d\u201e\u201f]")
    _INTERNAL_WS = re.compile(r"\s{2,}")

    @classmethod
    def sanitize(cls, name: str) -> str:
        """
        Full sanitization pipeline. Returns a cleaned string.

        Steps:
            1. Decode HTML entities
            2. Normalize Unicode (NFKC)
            3. Replace fancy punctuation with ASCII equivalents
            4. Strip trailing/leading whitespace and collapse internal whitespace
            5. Strip trailing artifact characters (semicolons, stray brackets, etc.)
        """
        if not isinstance(name, str):
            name = str(name)

        # 1. HTML entities
        name = html.unescape(name)

        # 2. Unicode normalization (NFKC converts ﬁ → fi, ² → 2, etc.)
        name = unicodedata.normalize("NFKC", name)

        # 3. Punctuation replacements
        name = cls._NBSP.sub(" ", name)
        name = cls._EM_DASH.sub("-", name)
        name = cls._FANCY_QUOTES.sub("'", name)
        name = cls._FANCY_DQUOTES.sub('"', name)

        # 4. Whitespace
        name = name.strip()
        name = cls._INTERNAL_WS.sub(" ", name)

        # 5. Trailing artifacts
        name = cls._TRAILING_ARTIFACTS.sub("", name).strip()

        return name

    @classmethod
    def normalize_for_matching(cls, name: str) -> str:
        """
        Create a normalized key for fuzzy/approximate matching.
        Lowercases, removes hyphens, collapses spaces, maps Greek letters to
        ASCII equivalents, strips stereochemistry prefixes.
        """
        name = cls.sanitize(name)
        name = name.lower()

        # Greek to ASCII
        for greek, ascii_eq in GREEK_TO_ASCII.items():
            name = name.replace(greek, ascii_eq)

        # Stereo prefixes
        name = STEREO_PREFIXES.sub("", name)

        # Remove hyphens and spaces
        name = name.replace("-", "").replace(" ", "")

        # Collapse anything left
        name = re.sub(r"\s+", "", name)

        return name

    @classmethod
    def split_concatenated(cls, raw: str) -> List[str]:
        """
        Split a raw string that might contain multiple metabolite names
        (e.g., semicolon- or comma-delimited entries within a single cell).

        Returns a list with one or more names.
        """
        # Try semicolon first (most common in databases), then comma
        for sep in (";", "|"):
            if sep in raw:
                parts = [cls.sanitize(p) for p in raw.split(sep)]
                return [p for p in parts if p]

        # Comma split only if multiple tokens found (avoid splitting "1,2-propanediol")
        comma_parts = [cls.sanitize(p) for p in raw.split(",")]
        if len(comma_parts) > 1 and all(len(p) > 3 for p in comma_parts):
            return [p for p in comma_parts if p]

        return [cls.sanitize(raw)]

    @classmethod
    def extract_from_freetext(cls, text: str) -> List[str]:
        """
        Heuristic extraction of candidate metabolite names from a longer sentence.
        Returns a list of candidate tokens/phrases (not resolved — just extracted).

        Strategy: Extract noun phrases that look like chemical names
        (CamelCase, contain digits or hyphens, Greek prefixes, etc.)
        """
        # Simple heuristic: words/phrases that contain chemical-style characters
        candidates = re.findall(
            r"\b(?:[A-Z][a-z]*-)?(?:[αβγδεζηθκλμνξπρστυφχψω][-]?)?[A-Za-z0-9][A-Za-z0-9\-']*(?:-[A-Za-z0-9]+)*\b",
            text,
        )
        # Filter out very common English words
        stopwords = {
            "the", "and", "or", "in", "of", "were", "was", "is", "are",
            "a", "an", "to", "for", "with", "at", "by", "from", "that",
            "this", "it", "its", "been", "be", "on", "as", "observed",
            "elevated", "levels", "found",
        }
        return [c for c in candidates if c.lower() not in stopwords and len(c) > 2]


# ---------------------------------------------------------------------------
# Database Layer
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS metabolites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name TEXT NOT NULL UNIQUE,
    primary_category TEXT,
    secondary_categories TEXT,  -- JSON list
    hmdb_id TEXT,
    pubchem_cid TEXT,
    inchi TEXT,
    smiles TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS synonyms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metabolite_id INTEGER NOT NULL REFERENCES metabolites(id),
    synonym TEXT NOT NULL,
    synonym_norm TEXT NOT NULL,  -- normalized version for fast matching
    UNIQUE(synonym_norm)
);

CREATE TABLE IF NOT EXISTS api_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_key TEXT NOT NULL UNIQUE,
    api_source TEXT NOT NULL,
    response_json TEXT,
    fetched_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_synonyms_norm ON synonyms(synonym_norm);
CREATE INDEX IF NOT EXISTS idx_synonyms_lower ON synonyms(synonym COLLATE NOCASE);
"""


class DatabaseManager:
    """
    Thin wrapper around SQLite with batch-query helpers.
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self):
        if self._conn is None:
            exists = self.db_path != ":memory:" and Path(self.db_path).exists()
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            if not exists or self.db_path == ":memory:":
                self._conn.executescript(SCHEMA_SQL)
                self._conn.commit()
                logger.info("Database initialised at %s", self.db_path)
        return self._conn

    @property
    def conn(self) -> sqlite3.Connection:
        return self.connect()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    # ------------------------------------------------------------------
    # Batch exact match
    # ------------------------------------------------------------------

    def batch_exact_match(self, names: List[str]) -> Dict[str, sqlite3.Row]:
        """
        Query synonyms table for exact (case-insensitive) matches for all names.
        Processes in chunks of 10,000 to avoid SQLite's variable limit.
        """
        if not names:
            return {}
        result: Dict[str, sqlite3.Row] = {}
        chunk_size = 10000
        for i in range(0, len(names), chunk_size):
            chunk = names[i:i + chunk_size]
            placeholders = ",".join("?" * len(chunk))
            sql = f"""
                SELECT s.synonym, s.metabolite_id, m.canonical_name,
                       m.primary_category, m.secondary_categories,
                       m.hmdb_id, m.pubchem_cid
                FROM synonyms s
                JOIN metabolites m ON s.metabolite_id = m.id
                WHERE lower(s.synonym) IN ({placeholders})
            """
            rows = self.conn.execute(sql, [n.lower() for n in chunk]).fetchall()
            for row in rows:
                result[row["synonym"].lower()] = row
        return result

    # ------------------------------------------------------------------
    # Batch normalized match
    # ------------------------------------------------------------------

    def batch_normalized_match(self, norm_names: List[str]) -> Dict[str, sqlite3.Row]:
        """
        Query synonyms table for normalized-key matches.
        Processes in chunks of 10,000 to avoid SQLite's variable limit.
        """
        if not norm_names:
            return {}
        result: Dict[str, sqlite3.Row] = {}
        chunk_size = 10000
        for i in range(0, len(norm_names), chunk_size):
            chunk = norm_names[i:i + chunk_size]
            placeholders = ",".join("?" * len(chunk))
            sql = f"""
                SELECT s.synonym_norm, s.synonym, s.metabolite_id, m.canonical_name,
                       m.primary_category, m.secondary_categories,
                       m.hmdb_id, m.pubchem_cid
                FROM synonyms s
                JOIN metabolites m ON s.metabolite_id = m.id
                WHERE s.synonym_norm IN ({placeholders})
            """
            rows = self.conn.execute(sql, chunk).fetchall()
            for row in rows:
                result[row["synonym_norm"]] = row
        return result

    # ------------------------------------------------------------------
    # All synonyms for fuzzy matching
    # ------------------------------------------------------------------

    def get_all_synonyms(self) -> List[Dict]:
        sql = """
            SELECT s.synonym, s.synonym_norm, s.metabolite_id,
                   m.canonical_name, m.primary_category, m.secondary_categories
            FROM synonyms s JOIN metabolites m ON s.metabolite_id = m.id
        """
        return [dict(r) for r in self.conn.execute(sql).fetchall()]

    # ------------------------------------------------------------------
    # API cache
    # ------------------------------------------------------------------

    def get_cache(self, key: str) -> Optional[Dict]:
        row = self.conn.execute(
            "SELECT response_json FROM api_cache WHERE query_key=?", (key,)
        ).fetchone()
        if row and row["response_json"]:
            return json.loads(row["response_json"])
        return None

    def set_cache(self, key: str, source: str, data: Dict):
        self.conn.execute(
            "INSERT OR REPLACE INTO api_cache(query_key, api_source, response_json) VALUES(?,?,?)",
            (key, source, json.dumps(data)),
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # Insert helpers (for seeding / API-discovered metabolites)
    # ------------------------------------------------------------------

    def insert_metabolite(
        self,
        canonical_name: str,
        primary_category: str,
        secondary_categories: Optional[List[str]] = None,
        hmdb_id: Optional[str] = None,
        pubchem_cid: Optional[str] = None,
        synonyms: Optional[List[str]] = None,
    ) -> int:
        cur = self.conn.execute(
            """INSERT OR IGNORE INTO metabolites
               (canonical_name, primary_category, secondary_categories, hmdb_id, pubchem_cid)
               VALUES(?,?,?,?,?)""",
            (
                canonical_name,
                primary_category,
                json.dumps(secondary_categories or []),
                hmdb_id,
                pubchem_cid,
            ),
        )
        met_id = cur.lastrowid or self.conn.execute(
            "SELECT id FROM metabolites WHERE canonical_name=?", (canonical_name,)
        ).fetchone()["id"]
        all_syns = list({canonical_name} | set(synonyms or []))
        for syn in all_syns:
            norm = Sanitizer.normalize_for_matching(syn)
            self.conn.execute(
                "INSERT OR IGNORE INTO synonyms(metabolite_id, synonym, synonym_norm) VALUES(?,?,?)",
                (met_id, syn, norm),
            )
        self.conn.commit()
        return met_id


# ---------------------------------------------------------------------------
# External API clients
# ---------------------------------------------------------------------------


class PubChemClient:
    BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

    @staticmethod
    async def search_by_name(session, name: str):
        if not HAS_AIOHTTP:
            return None
        timeout = aiohttp.ClientTimeout(total=15)
        url = f"{PubChemClient.BASE}/compound/name/{name}/JSON"
        try:
            async with session.get(url, timeout=timeout) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    compound = data.get("PC_Compounds", [{}])[0]
                    return {"source": "pubchem", "raw": compound}
                elif resp.status == 404:
                    return None
                else:
                    return None
        except Exception as exc:
            return None


class HMDBClient:
    BASE = "https://hmdb.ca/metabolites"

    @staticmethod
    async def search_by_name(session, name: str):
        if not HAS_AIOHTTP:
            return None
        timeout = aiohttp.ClientTimeout(total=15)
        url = f"https://hmdb.ca/metabolites.json?search_by=metabolite_name&search_by_term={name}"
        try:
            async with session.get(url, timeout=timeout) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data and isinstance(data, list) and len(data) > 0:
                        return {"source": "hmdb", "raw": data[0]}
                return None
        except Exception as exc:
            return None


class ClassyFireClient:
    BASE = "http://classyfire.wishartlab.com"

    @staticmethod
    async def classify_by_name(session, name: str):
        if not HAS_AIOHTTP:
            return None
        timeout = aiohttp.ClientTimeout(total=30)
        url = f"{ClassyFireClient.BASE}/queries.json"
        payload = {"label": name, "query_input": name, "query_type": "get_compound"}
        try:
            async with session.post(url, json=payload, timeout=timeout) as resp:
                if resp.status in (200, 201):
                    data = await resp.json()
                    return {"source": "classyfire", "raw": data}
                return None
        except Exception as exc:
            return None

# ---------------------------------------------------------------------------
# Classification Engine
# ---------------------------------------------------------------------------


class MetaboliteClassifier:
    """
    Classification engine for metabolite names.

    Parameters
    ----------
    db_path : str
        Path to the SQLite database file. Defaults to ':memory:' (in-memory, for testing).
    fuzzy_threshold : float
        Minimum similarity score (0-100) for fuzzy matching. Default 80.
    max_workers : int
        Number of threads for parallel API calls. Default 5.
    api_timeout : float
        Per-request timeout (seconds) for external APIs. Default 15.
    enable_api : bool
        Whether to make external API calls when local DB has no match. Default True.
    rate_limit_delay : float
        Seconds to wait between API request batches. Default 0.5.

    Example
    -------
    >>> clf = MetaboliteClassifier(db_path="metabolites.db")
    >>> df = clf.classify(["Glutamine", "beta-alanine", "Unknown123"])
    >>> clf.summary()
    >>> clf.export("out.csv")
    """

    def __init__(
        self,
        db_path: str = ":memory:",
        fuzzy_threshold: float = 80.0,
        max_workers: int = 5,
        api_timeout: float = 15.0,
        enable_api: bool = True,
        rate_limit_delay: float = 0.5,
    ):
        self.db = DatabaseManager(db_path)
        self.db.connect()
        self.fuzzy_threshold = fuzzy_threshold
        self.max_workers = max_workers
        self.api_timeout = api_timeout
        self.enable_api = enable_api
        self.rate_limit_delay = rate_limit_delay
        self._results: Optional[pd.DataFrame] = None
        self._synonym_cache: Optional[List[Dict]] = None  # lazy loaded

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def classify(
        self,
        input_data: Union[str, List[str], "pd.Series"],
        extract_from_freetext: bool = False,
    ) -> pd.DataFrame:
        """
        Main entry point. Classify one or more metabolite names.

        Parameters
        ----------
        input_data : str | list[str] | pd.Series
            Metabolite name(s) to classify.
        extract_from_freetext : bool
            If True, attempt to extract metabolite names from longer prose strings.

        Returns
        -------
        pd.DataFrame
            One row per resolved entry with columns:
            input_name, resolved_name, category, secondary_categories,
            confidence, resolution_method, source, matched_synonym, notes.

        Raises
        ------
        TypeError
            If input_data is not str, list, or pd.Series.
        """
        names = self._ingest(input_data)

        # Optionally extract from free text
        if extract_from_freetext:
            extracted = []
            for n in names:
                candidates = Sanitizer.extract_from_freetext(n)
                extracted.extend(candidates if candidates else [n])
            names = extracted

        # Split concatenated entries
        flat: List[Tuple[str, str]] = []  # (original, sanitized)
        for raw in names:
            parts = Sanitizer.split_concatenated(raw)
            for p in parts:
                flat.append((raw, p))

        logger.info("Classifying %d entries (from %d raw inputs)", len(flat), len(names))
        records = self._run_pipeline(flat)
        self._results = pd.DataFrame(records, columns=RESULT_COLUMNS)
        return self._results

    def summary(self) -> Dict[str, Any]:
        """
        Return aggregate statistics about the last classify() run.

        Returns
        -------
        dict with keys:
            total, resolved, unresolved, by_category, by_resolution_method

        Raises
        ------
        RuntimeError
            If classify() has not been called yet.
        """
        if self._results is None:
            raise RuntimeError("Call classify() before summary().")
        df = self._results
        total = len(df)
        unresolved = (df["resolution_method"] == "unresolved").sum()
        resolved = total - unresolved

        by_cat = df["category"].value_counts().to_dict()
        by_method = df["resolution_method"].value_counts().to_dict()

        stats = {
            "total": total,
            "resolved": int(resolved),
            "unresolved": int(unresolved),
            "resolution_rate_pct": round(100 * resolved / total, 1) if total else 0,
            "by_category": by_cat,
            "by_resolution_method": by_method,
        }
        # Pretty print
        print("\n=== Classification Summary ===")
        for k, v in stats.items():
            if isinstance(v, dict):
                print(f"  {k}:")
                for kk, vv in v.items():
                    print(f"    {kk}: {vv}")
            else:
                print(f"  {k}: {v}")
        return stats

    def export(self, path: str, fmt: str = "csv") -> None:
        """
        Export results to a file.

        Parameters
        ----------
        path : str
            Output file path.
        fmt : str
            Format: 'csv' (default), 'tsv', 'json', 'excel'.

        Raises
        ------
        RuntimeError
            If classify() has not been called yet.
        ValueError
            If fmt is not supported.
        """
        if self._results is None:
            raise RuntimeError("Call classify() before export().")
        df = self._results
        fmt = fmt.lower()
        if fmt == "csv":
            df.to_csv(path, index=False)
        elif fmt == "tsv":
            df.to_csv(path, sep="\t", index=False)
        elif fmt == "json":
            df.to_json(path, orient="records", indent=2)
        elif fmt in ("excel", "xlsx"):
            df.to_excel(path, index=False)
        else:
            raise ValueError(f"Unsupported export format: {fmt!r}")
        logger.info("Results exported to %s (%s)", path, fmt)

    def flag_ambiguous(self) -> pd.DataFrame:
        """
        Return only rows where the match was uncertain (fuzzy or unresolved).

        Returns
        -------
        pd.DataFrame

        Raises
        ------
        RuntimeError
            If classify() has not been called yet.
        """
        if self._results is None:
            raise RuntimeError("Call classify() before flag_ambiguous().")
        mask = self._results["resolution_method"].isin(["fuzzy", "unresolved"])
        return self._results[mask].copy()

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def _ingest(self, input_data) -> List[str]:
        if isinstance(input_data, str):
            return [input_data]
        elif isinstance(input_data, (list, tuple)):
            return [str(x) for x in input_data]
        elif hasattr(input_data, "tolist"):  # pd.Series / np.ndarray
            return [str(x) for x in input_data.tolist()]
        else:
            raise TypeError(
                f"input_data must be str, list, or pd.Series, got {type(input_data).__name__}"
            )

    # ------------------------------------------------------------------
    # Pipeline orchestration
    # ------------------------------------------------------------------

    def _run_pipeline(self, flat: List[Tuple[str, str]]) -> List[Dict]:
        """
        Run the multi-stage resolution pipeline on the flattened list.
        """
        records = {sanitized: {"original": original, "sanitized": sanitized}
                   for original, sanitized in flat}
        pending = list(records.keys())  # names still unresolved

        # ---- Stage 1: Batch exact match --------------------------------
        pending = self._stage_exact(records, pending)
        if not pending:
            return list(records.values())

        # ---- Stage 2: Batch normalized match ---------------------------
        pending = self._stage_normalized(records, pending)
        if not pending:
            return list(records.values())

        # ---- Stage 3: Fuzzy match --------------------------------------
        pending = self._stage_fuzzy(records, pending)
        if not pending:
            return list(records.values())

        # ---- Stage 4: External API -------------------------------------
        if self.enable_api and pending:
            pending = self._stage_api(records, pending)

        # ---- Stage 5: Mark unresolved ----------------------------------
        for name in pending:
            rec = records[name]
            rec.setdefault("resolution_method", "unresolved")
            rec.setdefault("confidence", "unresolved")
            rec.setdefault("category", "unresolved")

        return [self._to_row(rec) for rec in records.values()]

    def _to_row(self, rec: Dict) -> Dict:
        """Flatten a record dict into the standard output columns."""
        return {
            "input_name": rec.get("original", rec.get("sanitized", "")),
            "resolved_name": rec.get("resolved_name", ""),
            "category": rec.get("category", "unresolved"),
            "secondary_categories": rec.get("secondary_categories", ""),
            "confidence": rec.get("confidence", "unresolved"),
            "resolution_method": rec.get("resolution_method", "unresolved"),
            "source": rec.get("source", ""),
            "matched_synonym": rec.get("matched_synonym", ""),
            "notes": rec.get("notes", ""),
        }

    # ------------------------------------------------------------------
    # Stage 1 — Exact match
    # ------------------------------------------------------------------

    def _stage_exact(self, records: Dict, pending: List[str]) -> List[str]:
        logger.debug("Stage 1 (exact): checking %d names", len(pending))
        matches = self.db.batch_exact_match(pending)
        still_pending = []
        for name in pending:
            row = matches.get(name.lower())
            if row:
                self._apply_db_row(records[name], row, method="exact")
                logger.debug("Exact match: %r → %r", name, row["canonical_name"])
            else:
                still_pending.append(name)
        logger.info("Stage 1 done. Resolved: %d, Pending: %d",
                    len(pending) - len(still_pending), len(still_pending))
        return still_pending

    # ------------------------------------------------------------------
    # Stage 2 — Normalized match
    # ------------------------------------------------------------------

    def _stage_normalized(self, records: Dict, pending: List[str]) -> List[str]:
        logger.debug("Stage 2 (normalized): checking %d names", len(pending))
        norm_map = {name: Sanitizer.normalize_for_matching(name) for name in pending}
        norm_to_orig = {}
        for name, norm in norm_map.items():
            norm_to_orig.setdefault(norm, []).append(name)

        matches = self.db.batch_normalized_match(list(norm_map.values()))
        still_pending = []
        for name in pending:
            norm = norm_map[name]
            row = matches.get(norm)
            if row:
                self._apply_db_row(records[name], row, method="normalized")
                logger.debug("Normalized match: %r → %r", name, row["canonical_name"])
            else:
                still_pending.append(name)
        logger.info("Stage 2 done. Resolved: %d, Pending: %d",
                    len(pending) - len(still_pending), len(still_pending))
        return still_pending

    # ------------------------------------------------------------------
    # Stage 3 — Fuzzy match
    # ------------------------------------------------------------------

    def _stage_fuzzy(self, records: Dict, pending: List[str]) -> List[str]:
        if FUZZY_BACKEND is None:
            logger.warning("No fuzzy backend available (install rapidfuzz or thefuzz). Skipping fuzzy stage.")
            return pending

        logger.debug("Stage 3 (fuzzy): checking %d names", len(pending))
        if self._synonym_cache is None:
            self._synonym_cache = self.db.get_all_synonyms()

        if not self._synonym_cache:
            logger.warning("Synonym cache empty — skipping fuzzy stage")
            return pending

        syn_names = [s["synonym"] for s in self._synonym_cache]
        syn_lookup = {s["synonym"]: s for s in self._synonym_cache}

        still_pending = []
        for name in pending:
            if FUZZY_BACKEND == "rapidfuzz":
                result = rfprocess.extractOne(
                    name, syn_names, scorer=fuzz.token_sort_ratio, score_cutoff=self.fuzzy_threshold
                )
            else:
                # thefuzz fallback
                best_score = 0
                best_match = None
                for syn in syn_names:
                    score = fuzz.token_sort_ratio(name, syn)
                    if score > best_score:
                        best_score = score
                        best_match = syn
                result = (best_match, best_score, None) if best_score >= self.fuzzy_threshold else None

            if result:
                matched_syn, score, *_ = result
                syn_data = syn_lookup[matched_syn]
                records[name].update({
                    "resolved_name": syn_data["canonical_name"],
                    "category": syn_data.get("primary_category", "unknown"),
                    "secondary_categories": syn_data.get("secondary_categories", ""),
                    "confidence": "low",
                    "resolution_method": "fuzzy",
                    "source": "local_db",
                    "matched_synonym": matched_syn,
                    "notes": f"Fuzzy match score: {score:.1f}%",
                })
                logger.debug("Fuzzy match: %r → %r (score %.1f)", name, matched_syn, score)
            else:
                still_pending.append(name)

        logger.info("Stage 3 done. Resolved: %d, Pending: %d",
                    len(pending) - len(still_pending), len(still_pending))
        return still_pending

    # ------------------------------------------------------------------
    # Stage 4 — External API
    # ------------------------------------------------------------------

    def _stage_api(self, records: Dict, pending: List[str]) -> List[str]:
        logger.info("Stage 4 (API): querying external APIs for %d names", len(pending))
        still_pending = []

        # Run async event loop in thread to avoid blocking
        loop = asyncio.new_event_loop()
        try:
            results = loop.run_until_complete(self._async_api_batch(pending))
        finally:
            loop.close()

        for name, api_data in zip(pending, results):
            if api_data:
                self._apply_api_result(records[name], api_data)
                logger.debug("API match: %r → source=%s", name, api_data.get("source"))
            else:
                still_pending.append(name)
                records[name]["notes"] = "No match found in any source"

        logger.info("Stage 4 done. Resolved: %d, Pending: %d",
                    len(pending) - len(still_pending), len(still_pending))
        return still_pending

    async def _async_api_batch(self, names: List[str]) -> List[Optional[Dict]]:
        """Run API calls concurrently with rate limiting."""
        semaphore = asyncio.Semaphore(self.max_workers)
        if not HAS_AIOHTTP:
            return [None] * len(names)
        connector = aiohttp.TCPConnector(limit=self.max_workers)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [self._query_apis_for_name(session, semaphore, name) for name in names]
            return await asyncio.gather(*tasks)

    async def _query_apis_for_name(
        self, session, semaphore: asyncio.Semaphore, name: str
    ) -> Optional[Dict]:
        # Check cache first
        cache_key = f"api:{name.lower()}"
        cached = self.db.get_cache(cache_key)
        if cached:
            logger.debug("Cache hit for %r", name)
            return cached

        async with semaphore:
            await asyncio.sleep(self.rate_limit_delay)

            # Try PubChem first
            result = await PubChemClient.search_by_name(session, name)
            if result:
                self.db.set_cache(cache_key, "pubchem", result)
                return result

            # Try HMDB
            result = await HMDBClient.search_by_name(session, name)
            if result:
                self.db.set_cache(cache_key, "hmdb", result)
                return result

            return None

    def _apply_api_result(self, rec: Dict, api_data: Dict):
        source = api_data.get("source", "api")
        raw = api_data.get("raw", {})

        # Derive category from API data (simplified heuristic)
        category = self._infer_category_from_api(raw, source)

        rec.update({
            "resolved_name": rec.get("sanitized", rec.get("original", "")),
            "category": category,
            "secondary_categories": "",
            "confidence": "medium",
            "resolution_method": "api",
            "source": source,
            "matched_synonym": "",
            "notes": f"Resolved via {source}",
        })

    def _infer_category_from_api(self, raw: Dict, source: str) -> str:
        """Heuristic category inference from API response data."""
        if source == "pubchem":
            # PubChem compound properties can hint at drug status
            iupac = str(raw).lower()
            if any(kw in iupac for kw in ["acid", "amine", "glucose", "fructose", "lactate"]):
                return "endogenous"
        if source == "hmdb":
            bio = str(raw.get("biological_properties", "")).lower()
            if "food" in bio:
                return "food"
            if "drug" in bio:
                return "drug"
        return "unknown"

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def _apply_db_row(self, rec: Dict, row, method: str):
        row_dict = dict(row)
        rec.update({
            "resolved_name": row_dict["canonical_name"],
            "category": row_dict.get("primary_category") or "unknown",
            "secondary_categories": row_dict.get("secondary_categories", "") or "",
            "confidence": CONFIDENCE_MAP.get(method, "medium"),
            "resolution_method": method,
            "source": "local_db",
            "matched_synonym": row_dict.get("synonym", row_dict["canonical_name"]),
            "notes": "",
        })

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.db.close()