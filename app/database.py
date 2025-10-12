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
        cursor.execute("""
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
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_name ON component_benchmarks(normalized_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_type ON component_benchmarks(component_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_score ON component_benchmarks(passmark_score DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON component_benchmarks(category)")
        
        conn.commit()
        conn.close()
    
    def insert_component(self, data: dict):
        """Insert or update component in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Extract all possible fields
        fields = [
            'name', 'normalized_name', 'component_type', 'category',
            'passmark_score', 'normalized_score', 'tier',
            'single_thread_rating', 'thread_rating', 'cores', 'threads',
            'base_clock', 'boost_clock', 'socket', 'cache', 'l3_cache',
            'g3d_mark', 'g2d_mark', 'memory_size', 'memory_type',
            'memory_bus', 'memory_bandwidth', 'cuda_cores',
            'tdp', 'process', 'architecture', 'price'
        ]
        
        values = {field: data.get(field) for field in fields}
        
        # Build INSERT OR REPLACE query
        columns = ', '.join(fields)
        placeholders = ', '.join(['?' for _ in fields])
        
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
        
        query += " ORDER BY passmark_score DESC LIMIT 1"
        
        cursor.execute(query, params)
        row = cursor.fetchone()
        
        # If not found, try removing ALL spaces from normalized_name for more flexible matching
        if not row:
            # Create search pattern with removed spaces
            search_no_spaces = normalized_search.replace(' ', '')
            
            query = """
                SELECT * FROM component_benchmarks 
                WHERE REPLACE(normalized_name, ' ', '') LIKE ?
            """
            params = [f"%{search_no_spaces}%"]
            
            if component_type:
                query += " AND component_type = ?"
                params.append(component_type.upper())
            
            query += " ORDER BY passmark_score DESC LIMIT 1"
            
            cursor.execute(query, params)
            row = cursor.fetchone()
        
        # If still not found, try token-based search (all tokens must be present)
        if not row:
            # Extract meaningful tokens (numbers, letters)
            tokens = re.findall(r'\w+', normalized_search.lower())
            
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
                
                query += " ORDER BY passmark_score DESC LIMIT 1"
                
                cursor.execute(query, params)
                row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_top_components(self, component_type: str, limit: int = 10, category: Optional[str] = None) -> List[dict]:
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
            cursor.execute("SELECT COUNT(*) FROM component_benchmarks WHERE component_type = ?", 
                         (component_type.upper(),))
        else:
            cursor.execute("SELECT COUNT(*) FROM component_benchmarks")
        
        count = cursor.fetchone()[0]
        conn.close()
        return count

