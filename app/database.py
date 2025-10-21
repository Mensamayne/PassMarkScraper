"""SQLite database operations."""

import sqlite3
from pathlib import Path
from typing import Optional, List
from app.config_loader import config


class Database:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = config.get_db_path()
        self.db_path = db_path
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    def init_database(self):
        """Initialize database with schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create main table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS component_benchmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                normalized_name TEXT NOT NULL,
                component_type TEXT NOT NULL,
                category TEXT,
                passmark_score INTEGER NOT NULL,
                normalized_score INTEGER NOT NULL,
                tier TEXT,

                -- CPU specific
                single_thread_rating INTEGER,
                thread_rating INTEGER,
                cores INTEGER,
                threads INTEGER,
                base_clock REAL,
                boost_clock REAL,
                socket TEXT,
                cache REAL,
                l3_cache REAL,

                -- GPU specific
                g3d_mark INTEGER,
                g2d_mark INTEGER,
                memory_size INTEGER,
                memory_type TEXT,
                memory_bus INTEGER,
                memory_bandwidth REAL,
                cuda_cores INTEGER,

                -- Common
                tdp INTEGER,
                process INTEGER,
                architecture TEXT,
                price REAL,

                -- Metadata
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(normalized_name, component_type)
            )
        """
        )

        # Create indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_name ON component_benchmarks(normalized_name)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_type ON component_benchmarks(component_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_score ON component_benchmarks(passmark_score DESC)"
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON component_benchmarks(category)")

        conn.commit()
        conn.close()

    def insert_component(self, data: dict):
        """Insert or update component in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Extract all possible fields
        fields = [
            "name",
            "normalized_name",
            "component_type",
            "category",
            "passmark_score",
            "normalized_score",
            "tier",
            "single_thread_rating",
            "thread_rating",
            "cores",
            "threads",
            "base_clock",
            "boost_clock",
            "socket",
            "cache",
            "l3_cache",
            "g3d_mark",
            "g2d_mark",
            "memory_size",
            "memory_type",
            "memory_bus",
            "memory_bandwidth",
            "cuda_cores",
            "tdp",
            "process",
            "architecture",
            "price",
        ]

        values = {field: data.get(field) for field in fields}

        # Build INSERT OR REPLACE query
        columns = ", ".join(fields)
        placeholders = ", ".join(["?" for _ in fields])

        query = f"""
            INSERT OR REPLACE INTO component_benchmarks ({columns})
            VALUES ({placeholders})
        """

        cursor.execute(query, [values[field] for field in fields])
        conn.commit()
        conn.close()

    def search_component(self, name: str, component_type: Optional[str] = None) -> Optional[dict]:
        """Search for component by name with flexible matching."""
        from app.normalizer import normalize_name
        import re

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Normalize search term (remove spaces, special chars)
        normalized_search = normalize_name(name)

        # Try exact normalized match first
        query = """
            SELECT * FROM component_benchmarks
            WHERE normalized_name LIKE ?
        """
        params = [f"%{normalized_search}%"]

        if component_type:
            query += " AND component_type = ?"
            params.append(component_type.upper())

        # Sort by name length (shorter = more exact match), not by performance
        query += " ORDER BY LENGTH(name) ASC, passmark_score DESC LIMIT 1"

        cursor.execute(query, params)
        row = cursor.fetchone()

        # If not found, try removing ALL spaces from normalized_name for more flexible matching
        if not row:
            # Create search pattern with removed spaces
            search_no_spaces = normalized_search.replace(" ", "")

            query = """
                SELECT * FROM component_benchmarks
                WHERE REPLACE(normalized_name, ' ', '') LIKE ?
            """
            params = [f"%{search_no_spaces}%"]

            if component_type:
                query += " AND component_type = ?"
                params.append(component_type.upper())

            # Sort by name length (shorter = more exact match), not by performance
            query += " ORDER BY LENGTH(name) ASC, passmark_score DESC LIMIT 1"

            cursor.execute(query, params)
            row = cursor.fetchone()

        # If still not found, try token-based search (all tokens must be present)
        if not row:
            # Extract meaningful tokens (numbers, letters)
            tokens = re.findall(r"\w+", normalized_search.lower())

            if tokens:
                # Build query: all tokens must be in normalized_name
                query = "SELECT * FROM component_benchmarks WHERE "
                conditions = []
                params = []

                for token in tokens:
                    conditions.append("REPLACE(normalized_name, ' ', '') LIKE ?")
                    params.append(f"%{token}%")

                query += " AND ".join(conditions)

                if component_type:
                    query += " AND component_type = ?"
                    params.append(component_type.upper())

                # Sort by name length (shorter = more exact match), not by performance
                query += " ORDER BY LENGTH(name) ASC, passmark_score DESC LIMIT 1"

                cursor.execute(query, params)
                row = cursor.fetchone()

        conn.close()

        if row:
            return dict(row)
        return None

    def get_top_components(
        self, component_type: str, limit: int = 10, category: Optional[str] = None
    ) -> List[dict]:
        """Get top components by type."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT * FROM component_benchmarks
            WHERE component_type = ?
        """
        params = [component_type.upper()]

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY passmark_score DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_count(self, component_type: Optional[str] = None) -> int:
        """Get count of components."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if component_type:
            cursor.execute(
                "SELECT COUNT(*) FROM component_benchmarks WHERE component_type = ?",
                (component_type.upper(),),
            )
        else:
            cursor.execute("SELECT COUNT(*) FROM component_benchmarks")

        count = cursor.fetchone()[0]
        conn.close()
        return count

    def search_enhanced(self, query: str, component_type: Optional[str] = None) -> List[dict]:
        """
        Enhanced search with fuzzy matching, chipset extraction, and confidence scoring.

        Returns list of matches with confidence scores, ordered by confidence DESC.
        """
        import re
        from app.normalizer import normalize_name

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        matches = []

        # 1. Extract chipset/model number from query
        chipset_patterns = {
            'gpu': [
                r'rtx\s*(\d{4})',  # RTX 5080, RTX5080
                r'gtx\s*(\d{4})',  # GTX 1080
                r'rx\s*(\d{4})',   # RX 7800
                r'radeon\s*rx\s*(\d{4})',  # Radeon RX 7800
                r'geforce\s*rtx\s*(\d{4})',  # GeForce RTX 5080
            ],
            'cpu': [
                r'ryzen\s*(\d)\s*(\d{4})',  # Ryzen 9 7900X
                r'core\s*i(\d)\s*(\d{4})',  # Core i9 13900K
                r'(\d{4})\s*x',  # 7900X
            ]
        }

        extracted_chipsets = []
        if component_type and component_type.lower() in chipset_patterns:
            for pattern in chipset_patterns[component_type.lower()]:
                matches_found = re.findall(pattern, query.lower())
                for match in matches_found:
                    if isinstance(match, tuple):
                        extracted_chipsets.extend([str(m) for m in match if m])
                    else:
                        extracted_chipsets.append(str(match))

        # 2. Try exact normalized match first (highest confidence)
        # BUT: Skip for RAM/STORAGE - they need token-based search
        if component_type and component_type.upper() not in ['RAM', 'STORAGE']:
            normalized_search = normalize_name(query)
            base_query = ("SELECT * FROM component_benchmarks "
                          "WHERE normalized_name LIKE ?")
            params = [f"%{normalized_search}%"]

            if component_type:
                base_query += " AND component_type = ?"
                params.append(component_type.upper())

            cursor.execute(base_query, params)
            exact_rows = cursor.fetchall()

            for row in exact_rows:
                matches.append({
                    "name": row["name"],
                    "passmark_score": row["passmark_score"],
                    "normalized_score": row["normalized_score"],
                    "confidence": 1.0,
                    "match_type": "exact_normalized"
                })
        else:
            normalized_search = normalize_name(query)

        # 3. Try chipset-based matching (high confidence)
        if extracted_chipsets and not matches:
            for chipset in extracted_chipsets:
                chipset_query = ("SELECT * FROM component_benchmarks "
                                 "WHERE name LIKE ?")
                chipset_params = [f"%{chipset}%"]

                if component_type:
                    chipset_query += " AND component_type = ?"
                    chipset_params.append(component_type.upper())

                chipset_query += " ORDER BY passmark_score DESC LIMIT 3"

                cursor.execute(chipset_query, chipset_params)
                chipset_rows = cursor.fetchall()

                for row in chipset_rows:
                    # Calculate confidence based on how well chipset matches
                    chipset_in_name = chipset.lower() in row["name"].lower()
                    confidence = 0.9 if chipset_in_name else 0.7

                    matches.append({
                        "name": row["name"],
                        "passmark_score": row["passmark_score"],
                        "normalized_score": row["normalized_score"],
                        "confidence": confidence,
                        "match_type": "chipset_extracted",
                        "extracted_chipset": chipset
                    })

        # 4. Try partial matching (medium confidence) - SKIP for RAM/STORAGE
        if (not matches and component_type
                and component_type.upper() not in ['RAM', 'STORAGE']):
            # Remove spaces and try matching
            search_no_spaces = normalized_search.replace(" ", "")

            partial_query = """
                SELECT * FROM component_benchmarks
                WHERE REPLACE(normalized_name, ' ', '') LIKE ?
            """
            partial_params = [f"%{search_no_spaces}%"]

            if component_type:
                partial_query += " AND component_type = ?"
                partial_params.append(component_type.upper())

            partial_query += " ORDER BY passmark_score DESC LIMIT 5"

            cursor.execute(partial_query, partial_params)
            partial_rows = cursor.fetchall()

            for row in partial_rows:
                matches.append({
                    "name": row["name"],
                    "passmark_score": row["passmark_score"],
                    "normalized_score": row["normalized_score"],
                    "confidence": 0.6,
                    "match_type": "partial_match"
                })

        # 5. Try token-based matching (PRIMARY for RAM/STORAGE, fallback for others)
        # For RAM/STORAGE: always try, for others: only if no matches yet
        should_try_tokens = ((component_type
                              and component_type.upper() in ['RAM', 'STORAGE'])
                             or not matches)
        if should_try_tokens:
            # Extract meaningful tokens (skip Polish words, focus on specs)
            skip_words = ['pamięć', 'pamiec', 'dysk', 'ssd', 'hdd',
                          'nvme', 'gb', 'tb']
            all_tokens = re.findall(r'\b\w+\b', query.lower())

            # Clean tokens: remove 'mhz' suffix, skip words
            tokens = []
            for t in all_tokens:
                if t in skip_words or len(t) <= 2:
                    continue
                # Remove common suffixes
                cleaned = re.sub(r'(mhz|ghz)$', '', t)
                if cleaned and cleaned not in skip_words:
                    tokens.append(cleaned)

            if len(tokens) >= 2:  # Need at least 2 tokens
                token_conditions = []
                token_params = []

                # For RAM/STORAGE, prioritize key specs
                important_tokens = []
                for token in tokens:
                    # RAM keywords
                    ram_keywords = ['ddr4', 'ddr5', '3200', '6000', '5600',
                                    'cl']
                    # STORAGE keywords (product codes, brands, types)
                    storage_keywords = ['ssdpr', 'cx400', 'nvme', 'samsung',
                                        'crucial', 'wd', 'seagate', 'm.2']

                    kw = ram_keywords + storage_keywords
                    if any(keyword in token for keyword in kw):
                        important_tokens.append(token)

                # Use important tokens first, then others (remove duplicates)
                search_tokens_raw = important_tokens + tokens
                # Remove duplicates, max 4 tokens
                search_tokens = list(dict.fromkeys(search_tokens_raw))[:4]

                # Try with decreasing number of tokens (3 -> 2)
                for min_tokens in [3, 2]:  # Start with 3 tokens, then try 2
                    if matches:
                        break  # Found something, stop

                    n = min(min_tokens, len(search_tokens))
                    tokens_to_use = search_tokens[:n]

                    token_conditions = []
                    token_params = []

                    for token in tokens_to_use:
                        token_conditions.append("LOWER(name) LIKE ?")
                        token_params.append(f"%{token}%")

                    token_query = f"""
                        SELECT * FROM component_benchmarks
                        WHERE {' AND '.join(token_conditions)}
                    """

                    if component_type:
                        token_query += " AND component_type = ?"
                        token_params.append(component_type.upper())

                    token_query += " ORDER BY passmark_score DESC LIMIT 10"

                    cursor.execute(token_query, token_params)
                    token_rows = cursor.fetchall()

                    if token_rows:
                        # Higher confidence for RAM/STORAGE token matching,
                        # adjusted by token count
                        base_conf = (0.85 if component_type
                                     and component_type.upper() in ['RAM', 'STORAGE']
                                     else 0.5)
                        ratio = len(tokens_to_use) / len(search_tokens)
                        token_confidence = base_conf * ratio

                        for row in token_rows:
                            matches.append({
                                "name": row["name"],
                                "passmark_score": row["passmark_score"],
                                "normalized_score": row["normalized_score"],
                                # At least 0.75 for RAM/STORAGE
                                "confidence": max(0.75, token_confidence),
                                "match_type": "token_based",
                                "tokens_used": tokens_to_use,
                                "token_count": len(tokens_to_use)
                            })

        # Remove duplicates and sort by confidence
        seen_names = set()
        unique_matches = []

        for match in matches:
            if match["name"] not in seen_names:
                seen_names.add(match["name"])
                unique_matches.append(match)

        # Sort by confidence descending, then by passmark_score descending
        unique_matches.sort(key=lambda x: (-x["confidence"],
                                           -x["passmark_score"]))

        conn.close()
        return unique_matches[:5]  # Return top 5 matches
