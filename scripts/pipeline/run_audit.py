"""
Pipeline script to check for consistent view among the multiple DBs
"""
from db.utils_pipeline import audit_only, reconcile

if __name__ == '__main__':
    print("Audit between primary and derived stores")
    report = audit_only()
    #report = reconcile()
    print(report)
    
