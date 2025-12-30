from __future__ import annotations

import os
import csv
import re
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


_BACKEND_ENV_PATH = (Path(__file__).resolve().parents[1] / ".env").resolve()
load_dotenv(dotenv_path=_BACKEND_ENV_PATH)


DATA_DIR = (Path(__file__).resolve().parents[2] / "data" / "voltway_data").resolve()
SAMPLES_DIR = (Path(__file__).resolve().parents[2] / "hugo_data_samples").resolve()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class FinancialImpact:
    revenue_at_risk: float = 0.0
    penalty_risk: float = 0.0

    @property
    def total(self) -> float:
        return float(self.revenue_at_risk) + float(self.penalty_risk)


@dataclass
class OperationalImpact:
    affected_orders_count: int = 0
    days_until_stockout: int | None = None


@dataclass
class Alert:
    id: str
    alert_type: str
    severity: str
    title: str
    description: str
    created_at: str
    dismissed: bool = False
    impact_summary: str | None = None
    recommended_actions: str | None = None
    financial_impact: FinancialImpact = field(default_factory=FinancialImpact)
    operational_impact: OperationalImpact = field(default_factory=OperationalImpact)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["financial_impact"]["total"] = self.financial_impact.total
        return d


_ALERTS: list[Alert] = []


_FIREBASE_INIT_DONE = False
_FIREBASE_LAST_ERROR: str | None = None
_FIREBASE_ALERTS_PATH = "hugo/alerts"
_FIREBASE_SAMPLES_PATH = "hugo/datasets/hugo_data_samples"


def _set_firebase_error(msg: str | None) -> None:
    global _FIREBASE_LAST_ERROR
    _FIREBASE_LAST_ERROR = msg


def _firebase_config() -> tuple[str | None, Any]:
    # 1. Database URL is always required
    db_url = os.getenv("FIREBASE_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not db_url:
        _set_firebase_error("Missing FIREBASE_DATABASE_URL")
        return None, None

    # 2. Check for Base64 Creds (Cloud/CI)
    base64_creds = os.getenv("FIREBASE_SERVICE_ACCOUNT_BASE64")
    if base64_creds:
        return db_url, "BASE64"

    # 3. Check for Local JSON File (Local Dev)
    sa_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if not sa_path:
        _set_firebase_error("Missing FIREBASE_SERVICE_ACCOUNT_JSON or FIREBASE_SERVICE_ACCOUNT_BASE64")
        return None, None
        
    p = Path(sa_path)
    if not p.is_absolute():
        p = (Path(__file__).resolve().parents[1] / p).resolve()
    if not p.exists():
        _set_firebase_error(f"Service account JSON not found at: {p}")
        return None, None
    
    _set_firebase_error(None)
    return db_url, p


def _firebase_enabled() -> bool:
    db_url, config = _firebase_config()
    return bool(db_url and config)


def _init_firebase() -> bool:
    global _FIREBASE_INIT_DONE
    if _FIREBASE_INIT_DONE:
        return True

    db_url, config = _firebase_config()
    if not db_url or not config:
        return False

    try:
        import firebase_admin
        from firebase_admin import credentials
        import base64
        import json
    except Exception as e:
        _set_firebase_error(f"Failed to import firebase-admin: {e}")
        return False

    try:
        if not firebase_admin._apps:
            if config == "BASE64":
                # Decode from Env Var
                encoded = os.getenv("FIREBASE_SERVICE_ACCOUNT_BASE64")
                decoded_json = base64.b64decode(encoded).decode('utf-8')
                cred_dict = json.loads(decoded_json)
                cred = credentials.Certificate(cred_dict)
                print("Authenticated via FIREBASE_SERVICE_ACCOUNT_BASE64")
            else:
                # Load from File
                cred = credentials.Certificate(str(config))
                print(f"Authenticated via file: {config}")

            firebase_admin.initialize_app(cred, {"databaseURL": db_url})
        
        _FIREBASE_INIT_DONE = True
        _set_firebase_error(None)
        return True
    except Exception as e:
        _set_firebase_error(f"Firebase initialize_app failed: {e}")
        return False


def _require_firebase() -> None:
    if not _firebase_enabled():
        raise HTTPException(
            status_code=500,
            detail=(
                "Firebase is not configured. Set FIREBASE_DATABASE_URL and FIREBASE_SERVICE_ACCOUNT_JSON in backend/.env and restart the server."
            ),
        )
    if not _init_firebase():
        raise HTTPException(
            status_code=500,
            detail="Firebase initialization failed. Check service account JSON path and database URL.",
        )


def _samples_payload_from_disk() -> dict[str, Any]:
    if not SAMPLES_DIR.exists():
        raise HTTPException(status_code=404, detail=f"hugo_data_samples folder not found at: {SAMPLES_DIR}")

    csv_files = [
        "dispatch_parameters.csv",
        "material_master.csv",
        "material_orders.csv",
        "sales_orders.csv",
        "stock_levels.csv",
        "stock_movements.csv",
        "suppliers.csv",
    ]

    csv_data: dict[str, Any] = {}
    for name in csv_files:
        p = SAMPLES_DIR / name
        # Replace periods with underscores for Firebase key compliance
        safe_key = name.replace('.', '_')
        csv_data[safe_key] = _read_csv(p) if p.exists() else []

    emails_dir = SAMPLES_DIR / "emails"
    emails: dict[str, str] = {}
    if emails_dir.exists() and emails_dir.is_dir():
        for p in sorted(emails_dir.glob("*.eml")):
            # Replace periods with underscores for Firebase key compliance
            safe_key = p.name.replace('.', '_')
            emails[safe_key] = _read_text_lossy(p)

    specs_dir = SAMPLES_DIR / "specs"
    specs_manifest: list[dict[str, Any]] = []
    if specs_dir.exists() and specs_dir.is_dir():
        for p in sorted(specs_dir.glob("*.pdf")):
            try:
                size = p.stat().st_size
            except Exception:
                size = None
            specs_manifest.append({"filename": p.name, "size_bytes": size})

    return {
        "source": "hugo_data_samples",
        "uploaded_at": _now_iso(),
        "csv": csv_data,
        "emails": emails,
        "specs_manifest": specs_manifest,
    }


def _save_samples_to_rtdb(payload: dict[str, Any]) -> bool:
    if not _init_firebase():
        return False
    try:
        from firebase_admin import db
    except Exception as e:
        _set_firebase_error(f"Failed to import firebase_admin.db: {e}")
        return False

    try:
        db.reference(_FIREBASE_SAMPLES_PATH).set(payload)
        _set_firebase_error(None)
        return True
    except Exception as e:
        _set_firebase_error(f"Failed to write samples to RTDB: {e}")
        return False


def _samples_summary(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return {"exists": False}

    csv = payload.get("csv") or {}
    emails = payload.get("emails") or {}
    specs_manifest = payload.get("specs_manifest") or []

    csv_counts = {
        name: (len(rows) if isinstance(rows, list) else 0)
        for name, rows in csv.items()
        if isinstance(csv, dict)
    }

    return {
        "exists": True,
        "source": payload.get("source"),
        "uploaded_at": payload.get("uploaded_at"),
        "csv_row_counts": csv_counts,
        "emails_count": len(emails) if isinstance(emails, dict) else 0,
        "specs_count": len(specs_manifest) if isinstance(specs_manifest, list) else 0,
    }


def _load_samples_from_rtdb() -> dict[str, Any] | None:
    if not _init_firebase():
        return None
    try:
        from firebase_admin import db
    except Exception as e:
        _set_firebase_error(f"Failed to import firebase_admin.db: {e}")
        return None

    try:
        raw = db.reference(_FIREBASE_SAMPLES_PATH).get()
        _set_firebase_error(None)
        return raw if isinstance(raw, dict) else None
    except Exception as e:
        _set_firebase_error(f"Failed to read samples from RTDB: {e}")
        return None


def _alert_from_dict(d: dict[str, Any]) -> Alert:
    fi = d.get("financial_impact") or {}
    oi = d.get("operational_impact") or {}

    financial_impact = FinancialImpact(
        revenue_at_risk=_safe_float(fi.get("revenue_at_risk"), 0.0),
        penalty_risk=_safe_float(fi.get("penalty_risk"), 0.0),
    )
    operational_impact = OperationalImpact(
        affected_orders_count=int(float(oi.get("affected_orders_count") or 0)),
        days_until_stockout=(int(float(oi.get("days_until_stockout"))) if oi.get("days_until_stockout") is not None else None),
    )

    return Alert(
        id=str(d.get("id") or uuid.uuid4()),
        alert_type=str(d.get("alert_type") or "info"),
        severity=str(d.get("severity") or "info"),
        title=str(d.get("title") or ""),
        description=str(d.get("description") or ""),
        created_at=str(d.get("created_at") or _now_iso()),
        dismissed=bool(d.get("dismissed") or False),
        impact_summary=(d.get("impact_summary") if d.get("impact_summary") is not None else None),
        recommended_actions=(d.get("recommended_actions") if d.get("recommended_actions") is not None else None),
        financial_impact=financial_impact,
        operational_impact=operational_impact,
    )


def _load_alerts_from_rtdb() -> list[Alert] | None:
    if not _init_firebase():
        return None

    try:
        from firebase_admin import db
    except Exception as e:
        _set_firebase_error(f"Failed to import firebase_admin.db: {e}")
        return None

    try:
        raw = db.reference(_FIREBASE_ALERTS_PATH).get()
        _set_firebase_error(None)
    except Exception as e:
        _set_firebase_error(f"Failed to read alerts from RTDB: {e}")
        return None

    if not raw:
        return []

    if isinstance(raw, dict):
        items = list(raw.values())
    elif isinstance(raw, list):
        items = raw
    else:
        return []

    alerts: list[Alert] = []
    for item in items:
        if isinstance(item, dict):
            try:
                alerts.append(_alert_from_dict(item))
            except Exception:
                continue
    return alerts


def _save_alerts_to_rtdb(alerts: list[Alert]) -> bool:
    if not _init_firebase():
        return False

    try:
        from firebase_admin import db
    except Exception as e:
        _set_firebase_error(f"Failed to import firebase_admin.db: {e}")
        return False

    payload = {a.id: a.to_dict() for a in alerts}
    try:
        db.reference(_FIREBASE_ALERTS_PATH).set(payload)
        _set_firebase_error(None)
        return True
    except Exception as e:
        _set_firebase_error(f"Failed to write alerts to RTDB: {e}")
        return False


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [dict(r) for r in reader]


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _read_text_lossy(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


def _build_context_summary() -> str:
    try:
        # 1. Try Cloud Data First
        samples = _load_samples_from_rtdb()
        if samples and samples.get("csv"):
            # Cloud Mode: Dump all tables into context for the LLM
            csv_data = samples.get("csv", {})
            emails_data = samples.get("emails", {})
            
            context_parts = ["Hugo Knowledge Base (Live Cloud Data):"]
            
            # Priority tables for the Hackathon (include full content if small, truncated if large)
            priority_order = [
                "bottleneck_analysis", "production_capacity", "daily_operations_log", 
                "supplier_performance_metrics", "framework_contracts", "reorder_recommendations",
                "material_consumption_history", "demand_forecast",
                "stock_levels", "material_master", "material_orders", "sales_orders"
            ]
            
            # Helper to find key
            def find_key(partial):
                for k in csv_data.keys():
                    if partial in k:
                        return k
                return None

            # Add Tables
            for name in priority_order:
                key = find_key(name)
                if key:
                    rows_raw = csv_data[key]
                    # Handle Firebase List vs Dict structure
                    if isinstance(rows_raw, dict):
                        rows = list(rows_raw.values())
                    elif isinstance(rows_raw, list):
                        rows = rows_raw
                    else:
                        continue # Unknown format

                    if not rows or len(rows) == 0:
                        continue

                    context_parts.append(f"\n--- TABLE: {name.upper()} ---")
                    
                    # Ensure row is dict
                    first_row = rows[0]
                    if isinstance(first_row, dict):
                        # Headers
                        headers = list(first_row.keys())
                        context_parts.append(",".join(headers))
                        # Rows (limit 20 to save tokens, but enough for analysis)
                        for r in rows[:20]:
                            if isinstance(r, dict):
                                context_parts.append(",".join([str(v) for v in r.values()]))
                        if len(rows) > 20:
                            context_parts.append(f"... ({len(rows) - 20} more rows)")
                    else:
                         # Fallback if rows are not dicts (e.g. strings?)
                         context_parts.append(str(rows[:5]))

            # Add Emails (Critical for "qualitative" questions)
            context_parts.append("\n--- SUPPLIER EMAILS ---")
            # Combine all email values
            all_emails = []
            if isinstance(emails_data, dict):
                for v in emails_data.values():
                    if isinstance(v, str):
                        all_emails.append(v)
                    elif isinstance(v, dict):
                        all_emails.append(json.dumps(v))
            elif isinstance(emails_data, list):
                 for v in emails_data:
                    if isinstance(v, str):
                        all_emails.append(v)

            joined_emails = "\n\n".join(all_emails)
            context_parts.append(joined_emails[:3000]) # Generous limit for emails

            # Add Inventory Summary (calculated)
            if "stock_levels_csv" in csv_data:
                 stock_raw = csv_data.get("stock_levels_csv") or []
                 if isinstance(stock_raw, dict): 
                     stock = list(stock_raw.values())
                 else:
                     stock = stock_raw
                 
                 low_stock = []
                 if isinstance(stock, list):
                     for r in stock:
                         if isinstance(r, dict):
                             try:
                                 if int(float(r.get("quantity", 0))) < 60:
                                     low_stock.append(r)
                             except: pass
                 if low_stock:
                     context_parts.append(f"\n--- LOW STOCK SUMMARY ---\nFound {len(low_stock)} items below threshold 60.")

            return "\n".join(context_parts)

    except Exception as e:
        print(f"Error in _build_context_summary (Cloud): {e}")
        import traceback
        traceback.print_exc()
        # Fallthrough to legacy on error

    # 2. Fallback to Local Disk (Legacy)
    try:
        materials = _read_csv(DATA_DIR / "materials.csv")
        stock = _read_csv(DATA_DIR / "stock_levels.csv")
        purchase_orders = _read_csv(DATA_DIR / "material_orders.csv")
        sales_orders = _read_csv(DATA_DIR / "sales_orders.csv")
        emails = _read_text(DATA_DIR / "supplier_emails.txt")

        suppliers = sorted({(m.get("supplier_name") or "").strip() for m in materials if m.get("supplier_name")})
        suppliers = [s for s in suppliers if s]

        delayed_pos = [po for po in purchase_orders if (po.get("status") or "").strip().lower() == "delayed"]
        low_stock = []
        for row in stock:
            code = (row.get("material_code") or "").strip()
            try:
                qty = int(float(row.get("quantity") or 0))
            except Exception:
                qty = 0
            if code and qty < 60:
                low_stock.append((code, qty))
        low_stock_sorted = sorted(low_stock, key=lambda x: x[1])

        top_low_stock = ", ".join([f"{code}({qty})" for code, qty in low_stock_sorted[:5]]) or "none"
        example_delays = ", ".join([po.get("po_number", "") for po in delayed_pos[:5] if po.get("po_number")]) or "none"

        return (
            "Hugo dataset summary (Local Fallback):\n"
            f"- Materials count: {len(materials)}\n"
            f"- Suppliers count: {len(suppliers)} (examples: {', '.join(suppliers[:5]) if suppliers else 'none'})\n"
            f"- Purchase orders: {len(purchase_orders)} (delayed: {len(delayed_pos)}; examples: {example_delays})\n"
            f"- Sales orders: {len(sales_orders)}\n"
            f"- Low stock items (<60): {len(low_stock_sorted)} (top: {top_low_stock})\n"
            "- Supplier emails are available (use them for qualitative signals like delays, price changes, payment term updates, and quality issues).\n"
            "\n"
            "Supplier emails excerpt:\n"
            f"{emails[:1200]}"
        )
    except Exception as e:
        print(f"Error in _build_context_summary (Legacy): {e}")
        return "Error building dataset context."


def _generate_alerts_from_dataset() -> list[Alert]:
    # Try loading from Firebase first
    firebase_data = _load_samples_from_rtdb()
    
    if firebase_data and firebase_data.get("csv"):
        # Use Firebase data
        csv_data = firebase_data.get("csv") or {}
        
        def get_data(key: str) -> list[dict]:
            # Try underscore key (sanitized) or original
            return csv_data.get(key) or csv_data.get(key.replace("_", ".")) or []

        # Map Materials
        raw_materials = get_data("material_master_csv")
        materials = [{
            "material_code": r.get("part_id", ""),
            "unit_price": r.get("cost_per_unit", "0"),
            "supplier_name": r.get("primary_supplier_id", ""),
        } for r in raw_materials]

        # Map Stock
        raw_stock = get_data("stock_levels_csv")
        stock = [{
            "material_code": r.get("part_id", ""),
            "quantity": r.get("quantity", "0"),
        } for r in raw_stock]

        # Map Purchase Orders
        raw_orders = get_data("material_orders_csv")
        material_orders = [{
            "po_number": r.get("order_id", ""),
            "material_code": r.get("part_id", ""),
            "supplier_name": r.get("supplier_id", ""),
            "quantity": r.get("quantity", "0"),
            "expected_delivery": r.get("date_expected", ""),
            "actual_delivery": r.get("actual_delivered_at", ""),
            "status": r.get("status", ""),
        } for r in raw_orders]

        # Sales Orders (just need count for now)
        sales_orders = get_data("sales_orders_csv")

        # Emails (combine all)
        email_dict = firebase_data.get("emails") or {}
        emails = "\n\n".join([str(v) for v in email_dict.values()])
    
    else:
        # Fallback to local disk
        materials = _read_csv(DATA_DIR / "materials.csv")
        stock = _read_csv(DATA_DIR / "stock_levels.csv")
        material_orders = _read_csv(DATA_DIR / "material_orders.csv")
        sales_orders = _read_csv(DATA_DIR / "sales_orders.csv")
        emails = _read_text(DATA_DIR / "supplier_emails.txt")

    baseline_price_by_material: dict[str, float] = {
        m.get("material_code", ""): _safe_float(m.get("unit_price")) for m in materials
    }

    alerts: list[Alert] = []

    # 1) Supplier delays from purchase orders
    for po in material_orders:
        status = (po.get("status") or "").strip().lower()
        if status != "delayed":
            continue

        po_number = (po.get("po_number") or "").strip()
        supplier = (po.get("supplier_name") or "").strip()
        material_code = (po.get("material_code") or "").strip()
        qty = int(float(po.get("quantity") or 0))

        expected = (po.get("expected_delivery") or "").strip()
        actual = (po.get("actual_delivery") or "").strip()

        # try to compute delay days if dates parse
        delay_days: int | None = None
        try:
            if expected and actual:
                exp_dt = datetime.fromisoformat(expected)
                act_dt = datetime.fromisoformat(actual)
                delay_days = max(0, (act_dt - exp_dt).days)
        except Exception:
            delay_days = None

        severity = "critical" if (delay_days is not None and delay_days >= 5) else "warning"

        title = f"PO {po_number} delayed ({material_code})"
        description = (
            f"Supplier {supplier} reported a delivery delay for PO {po_number} ({qty} units of {material_code})."
        )

        impact_summary = (
            f"Delayed inbound material may impact production schedule."
            + (f" Estimated delay: {delay_days} days." if delay_days is not None else "")
        )

        recommended_actions = (
            "Contact supplier for updated ETA, confirm expedited shipping options, and review safety stock coverage."
        )

        alerts.append(
            Alert(
                id=str(uuid.uuid4()),
                alert_type="supplier_delay",
                severity=severity,
                title=title,
                description=description,
                created_at=_now_iso(),
                impact_summary=impact_summary,
                recommended_actions=recommended_actions,
                operational_impact=OperationalImpact(affected_orders_count=len(sales_orders), days_until_stockout=None),
            )
        )

    # 2) Price spike signals from emails
    price_increase_match = re.search(r"(\d+)%\s+price\s+increase", emails, flags=re.IGNORECASE)
    if price_increase_match:
        pct = int(price_increase_match.group(1))
        base = baseline_price_by_material.get("BATT-48V", 0.0)
        new_price_match = re.search(r"BATT-48V:\s*\$(\d+(?:\.\d+)?)", emails, flags=re.IGNORECASE)
        new_price = _safe_float(new_price_match.group(1)) if new_price_match else base * (1 + pct / 100)

        delta = max(0.0, new_price - base)
        annual_units_assumption = 1000
        exposure = delta * annual_units_assumption

        alerts.append(
            Alert(
                id=str(uuid.uuid4()),
                alert_type="price_spike",
                severity="warning" if pct < 15 else "critical",
                title="Battery price increase announced",
                description=f"Supplier communication indicates a {pct}% price increase for BATT-48V.",
                created_at=_now_iso(),
                impact_summary=(
                    f"Baseline price ${base:.2f} -> new price ${new_price:.2f}. "
                    f"Estimated annual exposure (assumption {annual_units_assumption} units): ${exposure:,.0f}."
                ),
                recommended_actions=(
                    "Negotiate volume pricing, evaluate alternate suppliers, and consider pulling forward orders before the effective date."
                ),
                financial_impact=FinancialImpact(revenue_at_risk=0.0, penalty_risk=exposure),
            )
        )

    # 3) Financial distress signals from emails
    if re.search(r"advance payment|cash flow|financial restructuring", emails, flags=re.IGNORECASE):
        alerts.append(
            Alert(
                id=str(uuid.uuid4()),
                alert_type="financial_distress",
                severity="warning",
                title="Supplier requested advance payment",
                description="Supplier communication indicates tighter payment terms (advance payment) due to cash flow constraints.",
                created_at=_now_iso(),
                impact_summary="Tighter terms may indicate supplier financial stress and higher supply continuity risk.",
                recommended_actions="Assess supplier risk, review contracts, secure secondary sources, and consider risk-mitigation clauses.",
            )
        )

    # 4) Quality issue signals from emails
    if re.search(r"quality issue|bearing defects|defective", emails, flags=re.IGNORECASE):
        alerts.append(
            Alert(
                id=str(uuid.uuid4()),
                alert_type="quality_issue",
                severity="warning",
                title="Potential motor quality issue reported",
                description="Supplier reported a potential quality issue in a motor batch (bearing defects).",
                created_at=_now_iso(),
                impact_summary="Risk of returns/rework and production disruptions if affected inventory is used.",
                recommended_actions="Quarantine suspected lots, inspect inventory, and coordinate replacement plan with the supplier.",
            )
        )

    # 5) Simple stockout risk heuristic
    # If any key items fall below threshold, alert.
    low_stock = []
    for row in stock:
        try:
            qty = int(float(row.get("quantity") or 0))
        except Exception:
            qty = 0
        if qty < 60:
            low_stock.append((row.get("material_code") or "", qty))

    if low_stock:
        worst = sorted(low_stock, key=lambda x: x[1])[0]
        alerts.append(
            Alert(
                id=str(uuid.uuid4()),
                alert_type="stockout_risk",
                severity="critical" if worst[1] < 30 else "warning",
                title="Low inventory risk detected",
                description=f"One or more materials have low on-hand quantity. Lowest: {worst[0]} ({worst[1]} units).",
                created_at=_now_iso(),
                impact_summary="Low stock can cause missed delivery commitments if replenishment is delayed.",
                recommended_actions="Review open POs, expedite replenishment, and adjust production plan to prioritize available components.",
                operational_impact=OperationalImpact(affected_orders_count=len(sales_orders), days_until_stockout=7),
            )
        )

    return alerts


def _compute_stats(alerts: list[Alert]) -> dict[str, Any]:
    active = [a for a in alerts if not a.dismissed]
    dismissed = [a for a in alerts if a.dismissed]

    by_severity: dict[str, int] = {}
    by_type: dict[str, int] = {}
    total_risk = 0.0

    for a in active:
        by_severity[a.severity] = by_severity.get(a.severity, 0) + 1
        by_type[a.alert_type] = by_type.get(a.alert_type, 0) + 1
        total_risk += a.financial_impact.total

    return {
        "active_alerts": len(active),
        "dismissed_alerts": len(dismissed),
        "by_severity": by_severity,
        "by_type": by_type,
        "total_financial_risk": total_risk,
    }


app = FastAPI(title="Hugo AI Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set. Add it to backend/.env and restart the server.")

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage, SystemMessage
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(
                "LangChain Gemini dependencies are not installed. "
                "Run: .\\venv\\Scripts\\python.exe -m pip install -r requirements.txt. "
                f"Import error: {e}"
            ),
        )

    context = _build_context_summary()

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key,
        temperature=0.2,
    )

    messages = [
        SystemMessage(
            content=(
                "You are Hugo AI, a procurement operations agent. "
                "Answer directly and concisely. Avoid long paragraphs. "
                "Summarize data trends instead of listing raw rows. "
                "Use bullet points for clarity. Highlight key numbers in **bold**. "
                "If data is missing, state it briefly."
            )
        ),
        HumanMessage(content=f"Dataset context:\n{context}\n\nUser question:\n{req.message}"),
    ]

    try:
        resp = llm.invoke(messages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM call failed: {e}")

    reply = getattr(resp, "content", None) or str(resp)
    return ChatResponse(reply=reply)


@app.get("/health")
def health() -> dict[str, Any]:
    db_url, sa_path = _firebase_config()
    return {
        "status": "ok",
        "data_dir": str(DATA_DIR),
        "alerts": len(_ALERTS),
        "firebase_enabled": _firebase_enabled(),
        "firebase_init_done": _FIREBASE_INIT_DONE,
        "firebase_last_error": _FIREBASE_LAST_ERROR,
        "firebase_database_url": db_url,
        "firebase_service_account_path": (str(sa_path) if sa_path else None),
        "firebase_service_account_exists": (bool(sa_path and sa_path.exists()) if sa_path else False),
        "firebase_samples_path": _FIREBASE_SAMPLES_PATH,
        "firebase_alerts_path": _FIREBASE_ALERTS_PATH,
    }


@app.get("/alerts")
def get_alerts() -> dict[str, Any]:
    return {"alerts": [a.to_dict() for a in _ALERTS if not a.dismissed]}


@app.post("/alerts/refresh")
def refresh_alerts() -> dict[str, Any]:
    global _ALERTS
    existing_ids = {a.id for a in _ALERTS}

    new_alerts = _generate_alerts_from_dataset()
    # avoid duplicating exact titles/types in a single run if called repeatedly
    existing_keys = {(a.alert_type, a.title) for a in _ALERTS}

    added: list[Alert] = []
    for a in new_alerts:
        if a.id in existing_ids:
            continue
        key = (a.alert_type, a.title)
        if key in existing_keys:
            continue
        existing_keys.add(key)
        added.append(a)

    _ALERTS.extend(added)

    _save_alerts_to_rtdb(_ALERTS)

    return {
        "status": "ok",
        "new_alerts_count": len(added),
        "total_active_alerts": len([a for a in _ALERTS if not a.dismissed]),
    }


@app.post("/alerts/{alert_id}/dismiss")
def dismiss_alert(alert_id: str) -> dict[str, Any]:
    for a in _ALERTS:
        if a.id == alert_id:
            a.dismissed = True
            _save_alerts_to_rtdb(_ALERTS)
            return {"status": "ok"}
    raise HTTPException(status_code=404, detail="Alert not found")


@app.get("/stats")
def stats() -> dict[str, Any]:
    return _compute_stats(_ALERTS)


@app.get("/suppliers")
def suppliers() -> dict[str, Any]:
    materials = _read_csv(DATA_DIR / "materials.csv")
    suppliers_set = {m.get("supplier_name", "").strip() for m in materials if m.get("supplier_name")}
    suppliers_list = sorted([s for s in suppliers_set if s])
    return {"suppliers": suppliers_list}


@app.get("/materials")
def materials() -> dict[str, Any]:
    return {"materials": _read_csv(DATA_DIR / "materials.csv")}


@app.get("/purchase-orders")
def purchase_orders() -> dict[str, Any]:
    return {"purchase_orders": _read_csv(DATA_DIR / "material_orders.csv")}


@app.get("/sales-orders")
def sales_orders() -> dict[str, Any]:
    return {"sales_orders": _read_csv(DATA_DIR / "sales_orders.csv")}


@app.post("/data/upload_samples")
def upload_samples_to_firebase() -> dict[str, Any]:
    _require_firebase()

    payload = _samples_payload_from_disk()
    ok = _save_samples_to_rtdb(payload)
    if not ok:
        db_url, sa_path = _firebase_config()
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to save hugo_data_samples dataset to Firebase RTDB",
                "firebase_last_error": _FIREBASE_LAST_ERROR,
                "firebase_database_url": db_url,
                "firebase_service_account_path": (str(sa_path) if sa_path else None),
                "firebase_service_account_exists": (bool(sa_path and sa_path.exists()) if sa_path else False),
                "firebase_path": _FIREBASE_SAMPLES_PATH,
            },
        )

    return {
        "status": "ok",
        "firebase_path": _FIREBASE_SAMPLES_PATH,
        "samples_dir": str(SAMPLES_DIR),
        "summary": _samples_summary(payload),
    }


@app.get("/data/samples_summary")
def samples_summary_from_firebase() -> dict[str, Any]:
    _require_firebase()

    payload = _load_samples_from_rtdb()
    return {
        "status": "ok",
        "firebase_path": _FIREBASE_SAMPLES_PATH,
        "summary": _samples_summary(payload),
    }


@app.post("/data/reload")
def data_reload() -> dict[str, Any]:
    # For this minimal backend, reload just re-runs detection.
    refreshed = refresh_alerts()
    return {"status": "ok", "refresh": refreshed}


# Seed initial alerts on startup (so UI isn't empty)
try:
    loaded = _load_alerts_from_rtdb()
    if loaded is None:
        _ALERTS = _generate_alerts_from_dataset()
    else:
        _ALERTS = loaded

    if _firebase_enabled() and SAMPLES_DIR.exists():
        existing_samples = _load_samples_from_rtdb()
        if not existing_samples:
            try:
                payload = _samples_payload_from_disk()
            except Exception:
                payload = None
            if payload:
                _save_samples_to_rtdb(payload)
except Exception:
    _ALERTS = []
