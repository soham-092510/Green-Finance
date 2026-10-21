# =====================================================================
# GREEN-FINANCE — BOOTSTRAP_ADMIN.PY (OPERATOR BOOTSTRAP SCRIPT)
# Purpose: One-time operator bootstrap command for initializing the root
#          Boss Admin securely. Fails closed if a Boss Admin already exists.
# =====================================================================

import argparse
import sys
from backend.db.session import SessionLocal
from backend.services.rbac_service import bootstrap_boss_admin
from backend.models.user import User


def main():
    parser = argparse.ArgumentParser(description="One-time Boss Admin bootstrap utility.")
    parser.add_argument("--username", help="Boss Admin username", required=False)
    parser.add_argument("--password", help="Boss Admin password", required=False)
    parser.add_argument("--email", help="Boss Admin email", required=False)
    parser.add_argument("--name", help="Boss Admin full name", default="Root Boss Admin")

    args = parser.parse_args()

    db = SessionLocal()
    try:
        # Check invariant
        existing = db.query(User).filter(
            (User.is_boss_admin == True) | (User.role == "SUPER_ADMIN")
        ).first()

        if existing:
            print(f"[SECURITY ALERT] Boss Admin already initialized as '{existing.username}'. Repeated bootstrap prohibited.")
            sys.exit(1)

        username = args.username or input("Enter Boss Admin username: ").strip()
        email = args.email or input("Enter Boss Admin email: ").strip()
        password = args.password or input("Enter Boss Admin password (min 10 chars): ").strip()

        if len(password) < 8:
            print("[ERROR] Password must be at least 8 characters long.")
            sys.exit(1)

        admin = bootstrap_boss_admin(
            db=db,
            username=username,
            password=password,
            email=email,
            name=args.name,
            ip_address="127.0.0.1 (CLI)"
        )
        print(f"[SUCCESS] Root Boss Admin '{admin.username}' bootstrapped successfully.")

    except Exception as e:
        print(f"[BOOTSTRAP ERROR] {str(e)}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
