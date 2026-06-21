import sys
import csv
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app.db.database import SessionLocal, engine, Base
from app.db.models import Search
from app.services.prefix_utils import get_prefixes
from app.cache.cache_manager import update_suggestions
from sqlalchemy.dialects.mysql import insert as mysql_insert

def load_data(filepath):
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        print(f"Reading data from {filepath}...")
        total_lines = sum(1 for _ in open(filepath, 'r', encoding='utf-8')) - 1
        
        with open(filepath, 'r', encoding='utf-8') as f:
            next(f)  # skip header
            reader = csv.reader(f)
            records_dict = {}
            batch_size = 5000
            
            print(f"Step 1/2: Inserting {total_lines} records into MySQL...")
            for i, row in enumerate(reader, 1):
                try:
                    count_val = int(float(row[1]))
                    query_val = row[0].strip().lower()[:255]
                    if query_val not in records_dict:
                        records_dict[query_val] = count_val
                    else:
                        # Ignore duplicates or sum them; we will sum them to be safe.
                        records_dict[query_val] += count_val
                except:
                    continue
                
                if len(records_dict) >= batch_size or i == total_lines:
                    if records_dict:
                        batch = [{"query": k, "count": v} for k, v in records_dict.items()]
                        try:
                            stmt = mysql_insert(Search).values(batch)
                            stmt = stmt.on_duplicate_key_update(count=stmt.inserted.count)
                            db.execute(stmt)
                            db.commit()
                        except Exception as e:
                            db.rollback()
                            print(f"\nMySQL Error during batch insert: {e}")
                        finally:
                            records_dict = {}
                    if i % 10000 == 0 or i == total_lines:
                        print(f"\r  DB Progress: {i}/{total_lines} ({(i/total_lines)*100:.1f}%)", end="", flush=True)
            
            print("\nStep 2/2: Building distributed cache for top trending 50 queries...")
            top_queries = db.query(Search).order_by(Search.count.desc()).limit(50).all()
            prefix_set = set()
            for r in top_queries:
                prefix_set.update(get_prefixes(r.query))
                
            prefix_list = list(prefix_set)
            total_prefixes = len(prefix_list)
            for i, prefix in enumerate(prefix_list, 1):
                top_10 = db.query(Search).filter(Search.query.like(f"{prefix}%")).order_by(Search.count.desc()).limit(10).all()
                suggestions = [{"query": s.query, "count": s.count} for s in top_10]
                update_suggestions(prefix, suggestions)
                
                if i % 100 == 0 or i == total_prefixes:
                    print(f"\r  Cache Progress: {i}/{total_prefixes} ({(i/total_prefixes)*100:.1f}%)", end="", flush=True)
                
        print("\nDataset loaded successfully.")
    except Exception as e:
        print(f"Error loading dataset: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python load_dataset.py <dataset_csv_path>")
        sys.exit(1)
    
    load_data(sys.argv[1])
