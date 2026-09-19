"""Server-rendered routes for the demo application."""

import csv
import io
from datetime import date, datetime, timezone
from typing import Any

from bson import ObjectId
from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from app.db import claims_collection, users_collection
from app.models import ClaimCategory, ClaimStatus, User, UserRole
from app.services.claims import ClaimTransitionError, transition
from app.services.auth import hash_password, verify_password
from app.services.employees import next_employee_id
from app.services.duplicates import find_duplicate, fingerprint
from app.services.parsing import ReceiptParseError, parse_receipt
from app.services.receipt_files import ReceiptFileError, extract_receipt_text
from app.services.payouts import make_payout_ref, pay_claim
from app.services.reports import monthly_report

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def format_paise(value: int) -> str:
    """Format integer paise using Indian grouping."""

    rupees = int(value) // 100
    digits = str(rupees)
    if len(digits) > 3:
        tail, head = digits[-3:], digits[:-3]
        groups = []
        while head:
            groups.insert(0, head[-2:])
            head = head[:-2]
        digits = ",".join(groups + [tail])
    return f"Rs {digits}"


templates.env.filters["paise"] = format_paise


def _current_user(request: Request) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    document = users_collection().find_one({"_id": user_id, "active": True})
    if not document:
        return None
    document["id"] = str(document.pop("_id"))
    return User.model_validate(document)


def _require_user(request: Request) -> User:
    user = _current_user(request)
    if not user:
        raise PermissionError("sign in required")
    return user


def _require_admin(request: Request) -> User:
    user = _require_user(request)
    if user.role != UserRole.ADMIN:
        raise PermissionError("admin access required")
    return user


def _csrf(request: Request) -> str:
    token = request.session.get("csrf_token")
    if not token:
        token = ObjectId().__str__()
        request.session["csrf_token"] = token
    return token


def _check_csrf(request: Request, token: str) -> None:
    if not token or token != request.session.get("csrf_token"):
        raise PermissionError("invalid form token")


def _render(request: Request, name: str, **context: Any) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name=name, context={"user": _current_user(request), "csrf": _csrf(request), **context})


@router.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return RedirectResponse("/dashboard" if _current_user(request) else "/sign-in", status_code=303)


@router.get("/sign-in", response_class=HTMLResponse)
def sign_in(request: Request) -> HTMLResponse:
    return _render(request, "sign_in.html")


@router.post("/sign-in")
def sign_in_submit(request: Request, user_id: str = Form(...), password: str = Form(...), csrf_token: str = Form(...)) -> RedirectResponse:
    _check_csrf(request, csrf_token)
    person = users_collection().find_one(
        {"$or": [{"_id": user_id}, {"employee_id": user_id}], "active": True}
    )
    if not person or not verify_password(password, person.get("password_hash")):
        return RedirectResponse("/sign-in?error=invalid", status_code=303)
    request.session["user_id"] = str(person["_id"])
    return RedirectResponse("/dashboard", status_code=303)


@router.post("/sign-out")
def sign_out(request: Request, csrf_token: str = Form(...)) -> RedirectResponse:
    _check_csrf(request, csrf_token)
    request.session.clear()
    return RedirectResponse("/sign-in", status_code=303)


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    user = _require_user(request)
    if user.role == UserRole.STAFF:
        query = {"claimant_id": user.id}
    elif user.role == UserRole.MANAGER:
        query = {"$or": [{"claimant_id": user.id}, {"approver_id": user.id}]}
    elif user.role == UserRole.FINANCE:
        query = {"status": {"$in": ["approved", "paid"]}}
    else:
        query = {}
    claims = list(claims_collection().find(query).sort("expense_date", -1).limit(100))
    return _render(request, "dashboard.html", claims=claims, role=user.role.value)


@router.get("/claims/new", response_class=HTMLResponse)
def new_claim(request: Request) -> HTMLResponse:
    _require_user(request)
    return _render(request, "claim_intake.html")


@router.post("/claims/parse-batch", response_class=HTMLResponse)
async def parse_batch(request: Request, files: list[UploadFile] = File(...), csrf_token: str = Form(...)) -> HTMLResponse:
    user = _require_user(request)
    _check_csrf(request, csrf_token)
    rows = []
    for upload in files:
        filename = upload.filename or "receipt"
        try:
            text = extract_receipt_text(filename, await upload.read())
            draft = parse_receipt(text)
            rows.append({"filename": filename, "raw_text": text, "draft": draft, "error": None})
        except (ReceiptFileError, ReceiptParseError) as exc:
            rows.append({"filename": filename, "raw_text": "", "draft": None, "error": str(exc)})
    return _render(request, "claim_batch_review.html", rows=rows, categories=list(ClaimCategory))


@router.get("/admin/employees", response_class=HTMLResponse)
def admin_employees(request: Request) -> HTMLResponse:
    _require_admin(request)
    employees = list(users_collection().find({"role": {"$ne": UserRole.ADMIN.value}}).sort("name", 1))
    return _render(request, "admin_employees.html", employees=employees)


@router.post("/admin/employees")
def enroll_employee(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    designation: str = Form(...),
    role: UserRole = Form(...),
    manager_id: str = Form(""),
    monthly_limit_paise: int = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...),
) -> RedirectResponse:
    _require_admin(request)
    _check_csrf(request, csrf_token)
    if role == UserRole.ADMIN:
        raise PermissionError("new administrators must be provisioned separately")
    employee_id = next_employee_id(name, users_collection())
    employee = User(
        id=employee_id.strip(),
        name=name.strip(),
        email=email.strip(),
        designation=designation.strip(),
        role=role,
        manager_id=manager_id.strip() or None,
        monthly_limit_paise=monthly_limit_paise,
        password_hash=hash_password(password),
    )
    users_collection().insert_one({"_id": employee.id, **employee.model_dump(exclude={"id"})})
    return RedirectResponse("/admin/employees", status_code=303)


@router.get("/admin/employees/{employee_id}", response_class=HTMLResponse)
def employee_detail(request: Request, employee_id: str) -> HTMLResponse:
    _require_admin(request)
    employee = users_collection().find_one({"_id": employee_id})
    if not employee:
        raise PermissionError("employee not found")
    employee["id"] = employee.pop("_id")
    return _render(request, "employee_detail.html", employee=employee)


@router.get("/admin/employees/{employee_id}/edit", response_class=HTMLResponse)
def edit_employee_form(request: Request, employee_id: str) -> HTMLResponse:
    _require_admin(request)
    employee = users_collection().find_one({"_id": employee_id, "role": {"$ne": UserRole.ADMIN.value}})
    if not employee:
        raise PermissionError("employee not found")
    employee["id"] = employee.pop("_id")
    managers = list(users_collection().find({"role": UserRole.MANAGER.value, "active": True}).sort("name", 1))
    return _render(request, "employee_edit.html", employee=employee, managers=managers)


@router.post("/admin/employees/{employee_id}/edit")
def edit_employee(
    request: Request,
    employee_id: str,
    name: str = Form(...),
    email: str = Form(...),
    designation: str = Form(...),
    role: UserRole = Form(...),
    manager_id: str = Form(""),
    monthly_limit_paise: int = Form(...),
    password: str = Form(""),
    active: bool = Form(False),
    csrf_token: str = Form(...),
) -> RedirectResponse:
    _require_admin(request)
    _check_csrf(request, csrf_token)
    if role == UserRole.ADMIN:
        raise PermissionError("employee role cannot be changed to admin")
    existing = users_collection().find_one({"_id": employee_id, "role": {"$ne": UserRole.ADMIN.value}})
    if not existing:
        raise PermissionError("employee not found")
    employee = User(
        id=employee_id,
        name=name.strip(),
        email=email.strip(),
        designation=designation.strip(),
        role=role,
        manager_id=manager_id.strip() or None,
        monthly_limit_paise=monthly_limit_paise,
        active=active,
    )
    update = {"$set": employee.model_dump(exclude={"id", "password_hash"})}
    if password.strip():
        update["$set"]["password_hash"] = hash_password(password)
    result = users_collection().update_one(
        {"_id": employee_id, "role": {"$ne": UserRole.ADMIN.value}},
        update,
    )
    if not result.matched_count:
        raise PermissionError("employee not found")
    return RedirectResponse(f"/admin/employees/{employee_id}", status_code=303)


@router.post("/admin/employees/{employee_id}/delete")
def delete_employee(request: Request, employee_id: str, csrf_token: str = Form(...)) -> RedirectResponse:
    _require_admin(request)
    _check_csrf(request, csrf_token)
    result = users_collection().update_one(
        {"_id": employee_id, "role": {"$ne": UserRole.ADMIN.value}},
        {"$set": {"active": False}},
    )
    if not result.matched_count:
        raise PermissionError("employee not found")
    return RedirectResponse("/admin/employees", status_code=303)


@router.post("/claims/parse", response_class=HTMLResponse)
def parse_claim(request: Request, receipt_text: str = Form(...), csrf_token: str = Form(...)) -> HTMLResponse:
    user = _require_user(request)
    _check_csrf(request, csrf_token)
    try:
        draft = parse_receipt(receipt_text)
    except ReceiptParseError as exc:
        return _render(request, "claim_intake.html", error=str(exc), receipt_text=receipt_text)
    return _render(request, "claim_review.html", draft=draft, receipt_text=receipt_text, categories=list(ClaimCategory))


@router.post("/claims/submit-batch", response_class=HTMLResponse, response_model=None)
def submit_batch(
    request: Request,
    merchant: list[str] = Form(...),
    amount_paise: list[str] = Form(...),
    expense_date: list[str] = Form(...),
    category: list[str] = Form(...),
    receipt_no: list[str] = Form(...),
    receipt_text: list[str] = Form(...),
    filename: list[str] = Form(...),
    duplicate_ack_note: list[str] = Form(...),
    csrf_token: str = Form(...),
) -> HTMLResponse | RedirectResponse:
    user = _require_user(request)
    _check_csrf(request, csrf_token)
    rows = []
    errors = []
    documents = []
    for index, name in enumerate(filename):
        try:
            amount = int(amount_paise[index])
            parsed_date = date.fromisoformat(expense_date[index])
            parsed_category = ClaimCategory(category[index])
            text = receipt_text[index]
            claim_data = {
                "merchant": merchant[index].strip(),
                "amount_paise": amount,
                "expense_date": parsed_date,
                "claimant_id": user.id,
                "receipt_no": receipt_no[index].strip() or None,
            }
            match = find_duplicate(claim_data, claims_collection())
            note = duplicate_ack_note[index].strip()
            if match and match.strength != "weak" and not note:
                raise ValueError(f"possible duplicate: {match.reason}; add an exception note if genuine")
            rows.append({"filename": name, "raw_text": text, "draft": {"merchant": merchant[index], "amount_paise": amount, "expense_date": parsed_date, "category": parsed_category, "receipt_no": receipt_no[index], "confidence": {}}, "error": None})
            documents.append({
                "claimant_id": user.id,
                "approver_id": user.manager_id or "head-operations",
                "merchant": claim_data["merchant"],
                "category": parsed_category.value,
                "amount_paise": amount,
                "currency": "INR",
                "expense_date": datetime.combine(parsed_date, datetime.min.time(), tzinfo=timezone.utc),
                "receipt_no": claim_data["receipt_no"],
                "raw_text": text[:20_000],
                "source": "image" if name.lower().endswith((".jpg", ".jpeg", ".png", ".pdf")) else "text",
                "fingerprint": fingerprint(claim_data["merchant"], amount, parsed_date),
                "duplicate_of": match.claim_id if match else None,
                "duplicate_reason": match.reason if match else None,
                "duplicate_ack_note": note or None,
                "status": "draft",
                "status_history": [],
                "created_at": datetime.now(timezone.utc),
            })
        except (IndexError, TypeError, ValueError) as exc:
            errors.append(f"{name}: {exc}")
            rows.append({"filename": name, "raw_text": receipt_text[index] if index < len(receipt_text) else "", "draft": {"merchant": merchant[index] if index < len(merchant) else "", "amount_paise": amount_paise[index] if index < len(amount_paise) else "", "expense_date": expense_date[index] if index < len(expense_date) else "", "category": category[index] if index < len(category) else ClaimCategory.OTHER.value, "receipt_no": receipt_no[index] if index < len(receipt_no) else "", "confidence": {}}, "error": str(exc)})
    if errors:
        return _render(request, "claim_batch_review.html", rows=rows, categories=list(ClaimCategory), errors=errors)
    for document in documents:
        result = claims_collection().insert_one(document)
        transition(str(result.inserted_id), user, ClaimStatus.SUBMITTED, claims_collection())
    return RedirectResponse("/dashboard", status_code=303)


@router.post("/claims/submit")
def submit_claim(request: Request, merchant: str = Form(...), amount_paise: int = Form(...), expense_date: date = Form(...), category: ClaimCategory = Form(...), receipt_no: str = Form(""), receipt_text: str = Form(...), csrf_token: str = Form(...), duplicate_ack_note: str = Form("")) -> RedirectResponse:
    user = _require_user(request)
    _check_csrf(request, csrf_token)
    claim_data = {"merchant": merchant, "amount_paise": amount_paise, "expense_date": expense_date, "claimant_id": user.id, "receipt_no": receipt_no or None}
    match = find_duplicate(claim_data, claims_collection())
    if match and match.strength != "weak" and not duplicate_ack_note.strip():
        return RedirectResponse("/claims/new?duplicate=1", status_code=303)
    approver_id = user.manager_id or "head-operations"
    document = {"claimant_id": user.id, "approver_id": approver_id, "merchant": merchant, "category": category.value, "amount_paise": amount_paise, "currency": "INR", "expense_date": datetime.combine(expense_date, datetime.min.time(), tzinfo=timezone.utc), "receipt_no": receipt_no or None, "raw_text": receipt_text[:20_000], "source": "text", "fingerprint": fingerprint(merchant, amount_paise, expense_date), "duplicate_of": match.claim_id if match else None, "duplicate_reason": match.reason if match else None, "duplicate_ack_note": duplicate_ack_note.strip() or None, "status": "draft", "status_history": [], "created_at": datetime.now(timezone.utc)}
    result = claims_collection().insert_one(document)
    transition(str(result.inserted_id), user, ClaimStatus.SUBMITTED, claims_collection())
    return RedirectResponse("/dashboard", status_code=303)


@router.post("/claims/{claim_id}/approve")
def approve_claim(request: Request, claim_id: str, csrf_token: str = Form(...)) -> RedirectResponse:
    user = _require_user(request)
    _check_csrf(request, csrf_token)
    if user.role != UserRole.MANAGER:
        raise PermissionError("manager access required")
    transition(claim_id, user, ClaimStatus.APPROVED, claims_collection())
    return RedirectResponse("/dashboard", status_code=303)


@router.post("/claims/{claim_id}/reject")
def reject_claim(request: Request, claim_id: str, csrf_token: str = Form(...), note: str = Form("")) -> RedirectResponse:
    user = _require_user(request)
    _check_csrf(request, csrf_token)
    transition(claim_id, user, ClaimStatus.REJECTED, claims_collection(), note=note.strip() or None)
    return RedirectResponse("/dashboard", status_code=303)


@router.post("/claims/{claim_id}/pay")
def pay_one(request: Request, claim_id: str, csrf_token: str = Form(...)) -> RedirectResponse:
    user = _require_user(request)
    _check_csrf(request, csrf_token)
    if user.role != UserRole.FINANCE:
        raise PermissionError("finance access required")
    sequence = claims_collection().count_documents({"status": "paid"}) + 1
    pay_claim(claim_id, user, claims_collection(), payout_ref=make_payout_ref(datetime.now(timezone.utc), sequence))
    return RedirectResponse("/dashboard", status_code=303)


@router.get("/reports", response_class=HTMLResponse)
def reports(request: Request, year: int | None = None, month: int | None = None) -> HTMLResponse:
    user = _require_user(request)
    if user.role != UserRole.FINANCE:
        raise PermissionError("finance access required")
    today = date.today()
    report = monthly_report(claims_collection(), users_collection(), year or today.year, month or today.month)
    return _render(request, "reports.html", report=report)


@router.get("/reports.csv")
def reports_csv(request: Request, year: int | None = None, month: int | None = None) -> StreamingResponse:
    user = _require_user(request)
    if user.role != UserRole.FINANCE:
        raise PermissionError("finance access required")
    today = date.today()
    report = monthly_report(claims_collection(), users_collection(), year or today.year, month or today.month)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Person", "Total (paise)", "Limit (paise)", "Percent", "Status"])
    for person in report["people"]:
        writer.writerow([person["name"], person["total_paise"], person["limit_paise"], f"{person['percent']:.1f}", person["status"]])
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=expense-report.csv"})