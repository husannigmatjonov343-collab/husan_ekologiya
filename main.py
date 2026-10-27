import os
import sqlite3
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from data import (
    MASLAHATLAR,
    MUAMMOLAR,
    OZBEKISTON,
    STATISTIKA,
    TEST,
    YANGILIKLAR,
)

BASE = Path(__file__).parent

# Vercel serverida /tmp papkasidan foydalanamiz (read-only xatosi chiqmasligi uchun)
if os.environ.get("VERCEL"):
  DB = Path("/tmp/ekologiya.db")
else:
  DB = BASE / "ekologiya.db"

app = FastAPI(
    title="EkoDunyo API",
    description="Ekologiya mavzusidagi sayt",
    version="1.0",
)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
tpl = Jinja2Templates(directory=BASE / "templates")


def db():
  con = sqlite3.connect(DB)
  con.execute("""CREATE TABLE IF NOT EXISTS xabarlar(
        id INTEGER PRIMARY KEY AUTOINCREMENT, ism TEXT, email TEXT, mavzu TEXT, xabar TEXT, sana TEXT)""")
  con.execute(
      """CREATE TABLE IF NOT EXISTS obunachilar(email TEXT UNIQUE, sana TEXT)"""
  )
  con.execute(
      """CREATE TABLE IF NOT EXISTS natijalar(ism TEXT, ball INTEGER, sana"
      " TEXT)"""
  )
  return con


def render(request, name, **ctx):
  return tpl.TemplateResponse(request, name, {"sahifa": name, **ctx})


@app.get("/", response_class=HTMLResponse)
def bosh(request: Request):
  return render(
      request,
      "index.html",
      muammolar=MUAMMOLAR[:6],
      stat=STATISTIKA,
      yangiliklar=YANGILIKLAR[:3],
  )


@app.get("/muammolar", response_class=HTMLResponse)
def muammolar(request: Request):
  return render(request, "muammolar.html", muammolar=MUAMMOLAR)


@app.get("/muammo/{slug}", response_class=HTMLResponse)
def muammo(request: Request, slug: str):
  m = next((x for x in MUAMMOLAR if x["slug"] == slug), None)
  if not m:
    return render(request, "404.html")
  boshqa = [x for x in MUAMMOLAR if x["slug"] != slug][:3]
  return render(request, "muammo.html", m=m, boshqa=boshqa)


@app.get("/ozbekiston", response_class=HTMLResponse)
def ozbekiston(request: Request):
  return render(request, "ozbekiston.html", bolimlar=OZBEKISTON)


@app.get("/yangiliklar", response_class=HTMLResponse)
def yangiliklar(request: Request, kategoriya: str = ""):
  kats = sorted({y["kategoriya"] for y in YANGILIKLAR})
  items = [
      y for y in YANGILIKLAR if not kategoriya or y["kategoriya"] == kategoriya
  ]
  return render(
      request, "yangiliklar.html", items=items, kats=kats, tanlangan=kategoriya
  )


@app.get("/kalkulyator", response_class=HTMLResponse)
def kalk(request: Request):
  return render(request, "kalkulyator.html", natija=None)


@app.post("/kalkulyator", response_class=HTMLResponse)
def kalk_post(
    request: Request,
    km: float = Form(0),
    elektr: float = Form(0),
    gaz: float = Form(0),
    parvoz: float = Form(0),
    gosht: int = Form(0),
):
  q = {
      "Avtomobil": km * 52 * 0.19,
      "Elektr": elektr * 12 * 0.45,
      "Gaz": gaz * 12 * 2.0,
      "Parvozlar": parvoz * 250,
      "Go'sht": gosht * 52 * 3.3,
  }
  jami = sum(q.values())
  daraxt = round(jami / 22)
  return render(
      request,
      "kalkulyator.html",
      natija={
          "qismlar": q,
          "jami": jami,
          "daraxt": daraxt,
          "daraja": (
              "Past" if jami < 2000 else "O'rtacha" if jami < 5000 else "Yuqori"
          ),
      },
  )


@app.get("/test", response_class=HTMLResponse)
def test(request: Request):
  con = db()
  top = con.execute(
      "SELECT ism, ball, sana FROM natijalar ORDER BY ball DESC LIMIT 10"
  ).fetchall()
  return render(request, "test.html", test=TEST, natija=None, top=top)


@app.post("/test", response_class=HTMLResponse)
async def test_post(request: Request):
  form = await request.form()
  ism = (form.get("ism") or "Mehmon").strip()[:40]
  javoblar = []
  ball = 0
  for i, s in enumerate(TEST):
    j = form.get(f"s{i}")
    j = int(j) if j is not None else -1
    ok = j == s["togri"]
    ball += ok
    javoblar.append(
        {"savol": s["savol"], "ok": ok, "togri": s["variantlar"][s["togri"]]}
    )
  con = db()
  con.execute(
      "INSERT INTO natijalar VALUES (?,?,?)",
      (ism, ball, datetime.now().strftime("%Y-%m-%d")),
  )
  con.commit()
  top = con.execute(
      "SELECT ism, ball, sana FROM natijalar ORDER BY ball DESC LIMIT 10"
  ).fetchall()
  return render(
      request,
      "test.html",
      test=TEST,
      natija={"ball": ball, "jami": len(TEST), "javoblar": javoblar},
      top=top,
  )


@app.get("/maslahatlar", response_class=HTMLResponse)
def maslahatlar(request: Request):
  return render(request, "maslahatlar.html", maslahatlar=MASLAHATLAR)


@app.get("/qidiruv", response_class=HTMLResponse)
def qidiruv(request: Request, q: str = ""):
  s = q.lower().strip()
  nat = []
  if s:
    for m in MUAMMOLAR:
      if s in (m["nomi"] + m["matn"]).lower():
        nat.append({
            "tur": "Muammo",
            "nomi": m["nomi"],
            "url": f"/muammo/{m['slug']}",
            "qisqa": m["qisqa"],
        })
    for y in YANGILIKLAR:
      if s in (y["sarlavha"] + y["matn"]).lower():
        nat.append({
            "tur": "Yangilik",
            "nomi": y["sarlavha"],
            "url": "/yangiliklar",
            "qisqa": y["matn"][:120],
        })
    for o in OZBEKISTON:
      if s in (o["nomi"] + o["matn"]).lower():
        nat.append({
            "tur": "O'zbekiston",
            "nomi": o["nomi"],
            "url": "/ozbekiston",
            "qisqa": o["matn"][:120],
        })
  return render(request, "qidiruv.html", q=q, nat=nat)


@app.get("/aloqa", response_class=HTMLResponse)
def aloqa(request: Request, ok: int = 0):
  return render(request, "aloqa.html", ok=ok)


@app.post("/aloqa")
def aloqa_post(
    ism: str = Form(...),
    email: str = Form(...),
    mavzu: str = Form(""),
    xabar: str = Form(...),
):
  con = db()
  con.execute(
      "INSERT INTO xabarlar(ism,email,mavzu,xabar,sana) VALUES (?,?,?,?,?)",
      (
          ism[:100],
          email[:100],
          mavzu[:150],
          xabar[:2000],
          datetime.now().strftime("%Y-%m-%d %H:%M"),
      ),
  )
  con.commit()
  return RedirectResponse("/aloqa?ok=1", status_code=303)


@app.get("/xabarlar", response_class=HTMLResponse)
def xabarlar(request: Request):
  rows = db().execute(
      "SELECT ism,email,mavzu,xabar,sana FROM xabarlar ORDER BY id DESC"
  ).fetchall()
  return render(request, "xabarlar.html", rows=rows)


@app.post("/obuna")
def obuna(request: Request, email: str = Form(...)):
  con = db()
  con.execute(
      "INSERT OR IGNORE INTO obunachilar VALUES (?,?)",
      (email[:100], datetime.now().isoformat()),
  )
  con.commit()
  return RedirectResponse(
      (request.headers.get("referer") or "/"), status_code=303
  )


# ---------- JSON API ----------
@app.get("/api/muammolar")
def api_muammolar():
  return MUAMMOLAR


@app.get("/api/yangiliklar")
def api_yangiliklar():
  return YANGILIKLAR


@app.get("/api/maslahatlar")
def api_maslahatlar():
  return MASLAHATLAR


@app.get("/api/statistika")
def api_stat():
  con = db()
  return {
      "statistika": STATISTIKA,
      "xabarlar": con.execute("SELECT COUNT(*) FROM xabarlar").fetchone()[0],
      "obunachilar": con.execute("SELECT COUNT(*) FROM obunachilar").fetchone()[0],
      "test_ishtirokchilari": con.execute(
          "SELECT COUNT(*) FROM natijalar"
      ).fetchone()[0],
  }