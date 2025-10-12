"""Script to scrape all components based on config."""
import requests
from app.config_loader import config


def scrape_all():
    """Scrape all component types based on configuration."""
    base_url = "http://localhost:9091"
    
    component_types = ["GPU", "CPU", "RAM", "STORAGE"]
    include_workstation = config.get_include_workstation()
    
    print("=" * 60)
    print("  SCRAPING ALL COMPONENTS")
    print("=" * 60)
    print()
    
    total_saved = 0
    total_skipped = 0
    
    for comp_type in component_types:
        limit = config.get_scraping_limit(comp_type)
        
        if limit == 0:
            print(f">>  {comp_type}: SKIPPED (limit=0 in config)")
            continue
        
        limit_str = "ALL" if limit == -1 else f"TOP {limit}"
        print(f"[*] Scraping {comp_type} ({limit_str})...")
        
        try:
            # Prepare request
            url = f"{base_url}/scrape-and-save"
            params = {
                "type": comp_type,
                "limit": limit if limit > 0 else 10000,  # -1 becomes very high number
                "include_workstation": include_workstation
            }
            
            # Make request
            response = requests.post(url, params=params, timeout=600)
            response.raise_for_status()
            
            result = response.json()
            
            saved = result.get("saved", 0)
            skipped = result.get("skipped", 0)
            
            total_saved += saved
            total_skipped += skipped
            
            print(f"   [OK] Saved: {saved} | Skipped: {skipped}")
            
        except requests.exceptions.Timeout:
            print(f"   [TIMEOUT] for {comp_type} (scraping took too long)")
        except requests.exceptions.RequestException as e:
            print(f"   [ERROR] for {comp_type}: {e}")
        
        print()
    
    # Final stats
    print("=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"Total saved: {total_saved}")
    print(f"Total skipped: {total_skipped}")
    
    # Get final count from database
    try:
        health = requests.get(f"{base_url}/health").json()
        print(f"Components in database: {health.get('db_count', 0)}")
    except Exception:
        pass
    
    print()
    print("[SUCCESS] SCRAPING COMPLETED!")
    print()


if __name__ == "__main__":
    scrape_all()

