import hmac
import json
import time
from pathlib import Path

from django.conf import settings
from django.core import signing
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import Item

WEB = Path(settings.BASE_DIR) / "web"
KINDS = {"att", "cond", "fin"}


def now_ms():
    return int(time.time() * 1000)


def _code_ok(request):
    if not settings.ACCESS_CODE:
        return True
    return hmac.compare_digest(request.headers.get("X-Code", ""), settings.ACCESS_CODE)


def _is_admin(request):
    tok = request.headers.get("X-Admin", "")
    if not tok:
        return False
    try:
        signing.loads(tok, salt="tafaqqud-admin", max_age=3 * 24 * 3600)
        return True
    except signing.BadSignature:
        return False


def _denied():
    return JsonResponse({"error": "code"}, status=401)


def _file(name, ctype):
    resp = HttpResponse((WEB / name).read_bytes(), content_type=ctype)
    resp["Cache-Control"] = "no-cache"
    return resp


def index(request):
    return _file("index.html", "text/html; charset=utf-8")


def service_worker(request):
    resp = _file("sw.js", "application/javascript; charset=utf-8")
    resp["Service-Worker-Allowed"] = "/"
    return resp


@require_GET
def ping(request):
    return JsonResponse({"ok": True, "now": now_ms(), "exam": settings.EXAM_ID})


@require_GET
def state(request):
    if not (_code_ok(request) or _is_admin(request)):
        return _denied()
    try:
        since = int(request.GET.get("since", "0"))
    except ValueError:
        since = 0
    now = now_ms()
    qs = Item.objects.filter(exam=settings.EXAM_ID, kind__in=KINDS, updated__gte=since).values("kind", "key", "data")
    items = [{"k": r["kind"], "id": r["key"], "d": r["data"]} for r in qs]
    return JsonResponse({"now": now, "items": items, "epoch": _epoch(), "exam": settings.EXAM_ID})


def _epoch():
    """وقت آخر مسح للبيانات؛ تغيّره يجعل كل الأجهزة تبدأ من جديد."""
    return Item.objects.filter(exam=settings.EXAM_ID, kind="sys", key="epoch").values_list("t", flat=True).first() or 0


def _better(kind, old, new):
    """هل السجل الجديد أحق من القديم؟"""
    if kind == "att":
        if old.get("auto") and not new.get("auto") and new.get("st"):
            return True      # التسجيل اليدوي يتقدّم على الغياب التلقائي
        if new.get("auto") and not old.get("auto") and old.get("st"):
            return False
    return int(new.get("t") or 0) >= int(old.get("t") or 0)


@csrf_exempt
@require_POST
def push(request):
    if not (_code_ok(request) or _is_admin(request)):
        return _denied()
    try:
        ops = json.loads(request.body or b"{}").get("ops", [])
    except (ValueError, AttributeError):
        return JsonResponse({"error": "bad json"}, status=400)
    if not isinstance(ops, list) or len(ops) > 1000:
        return JsonResponse({"error": "bad ops"}, status=400)
    done = 0
    with transaction.atomic():
        for op in ops:
            k, key, d = op.get("k"), str(op.get("id", ""))[:64], op.get("d")
            if k not in KINDS or not key or not isinstance(d, dict) or len(json.dumps(d)) > 4000:
                continue
            obj = Item.objects.select_for_update().filter(exam=settings.EXAM_ID, kind=k, key=key).first()
            if obj and not _better(k, obj.data, d):
                continue
            t = int(d.get("t") or 0)
            if obj:
                obj.data, obj.t, obj.updated = d, t, now_ms()
                obj.save(update_fields=["data", "t", "updated"])
            else:
                Item.objects.create(exam=settings.EXAM_ID, kind=k, key=key, data=d, t=t, updated=now_ms())
            done += 1
    return JsonResponse({"ok": True, "saved": done, "now": now_ms()})


@csrf_exempt
@require_POST
def login(request):
    try:
        pw = json.loads(request.body or b"{}").get("password", "")
    except ValueError:
        pw = ""
    if settings.ADMIN_PASSWORD and hmac.compare_digest(str(pw), settings.ADMIN_PASSWORD):
        return JsonResponse({"token": signing.dumps({"a": 1}, salt="tafaqqud-admin")})
    time.sleep(1)
    return JsonResponse({"error": "wrong"}, status=403)


@require_GET
def me(request):
    return JsonResponse({"admin": _is_admin(request), "code": _code_ok(request)})


@csrf_exempt
@require_POST
def reset(request):
    if not _is_admin(request):
        return JsonResponse({"error": "admin"}, status=403)
    with transaction.atomic():
        n, _ = Item.objects.filter(exam=settings.EXAM_ID).delete()
        t = now_ms()
        Item.objects.create(exam=settings.EXAM_ID, kind="sys", key="epoch", data={"t": t}, t=t, updated=t)
    return JsonResponse({"ok": True, "deleted": n})
