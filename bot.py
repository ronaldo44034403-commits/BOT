import asyncio
import html
import json
import os
import re
import shutil
import signal
import sys
import zipfile
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (CallbackQuery, FSInputFile, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)
from aiohttp import web

from config import BOT_TOKEN as TOKEN, OWNER_ID as OWNER

ROOT = Path("projects")
LOGS = Path("logs")
STATE = Path("state.json")
ROOT.mkdir(exist_ok=True)
LOGS.mkdir(exist_ok=True)

bot = Bot(TOKEN)
dp = Dispatcher()

procs: dict = {}
manual: set = set()
awaiting_name = False
NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,30}$")


def load_state():
    try:
        return json.loads(STATE.read_text())
    except Exception:
        return {"current": None, "auto": []}


state = load_state()


def save():
    STATE.write_text(json.dumps(state))


def projects():
    return sorted(p.name for p in ROOT.iterdir() if p.is_dir())


def cur():
    n = state.get("current")
    return n if n in projects() else None


def plog(n):
    return LOGS / f"{n}.log"


def running(n):
    p = procs.get(n)
    return p is not None and p.returncode is None


def btn(t, d):
    return InlineKeyboardButton(text=t, callback_data=d)


def kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn("▶️ Запустить", "run"), btn("⏹ Стоп", "stop"), btn("🔄 Рестарт", "restart")],
        [btn("📜 Логи", "logs"), btn("📥 Скачать лог", "dl"), btn("🧹 Очистить", "clear")],
        [btn("📁 Файлы", "files"), btn("📦 pip install", "pip"), btn("🔃 Статус", "status")],
        [btn("📂 Проекты", "list"), btn("➕ Новый", "new"), btn("🗑 Удалить", "delp")],
    ])


def list_kb():
    rows = [[btn(("🟢 " if running(n) else "⚪️ ") + n + (" ✔" if n == cur() else ""),
                 f"sel:{n}")] for n in projects()]
    rows.append([btn("➕ Новый проект", "new"), btn("⬅️ Назад", "status")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def panel():
    n = cur()
    total = sum(1 for x in projects() if running(x))
    if not n:
        return "<b>Хостинг кода</b>\nПроектов нет. Нажми ➕ Новый."
    if running(n):
        st = f"🟢 Работает (PID {procs[n].pid})"
    elif n in procs:
        st = f"🔴 Остановлен (код {procs[n].returncode})"
    else:
        st = "⚪️ Не запущен"
    has = (ROOT / n / "main.py").exists()
    return (f"<b>Проект: {n}</b>\nСтатус: {st}\n"
            f"main.py: {'есть ✅' if has else 'нет ❌ — пришли файл'}\n"
            f"Запущено проектов: {total}")


async def watch(n, p):
    code = await p.wait()
    if procs.get(n) is p and n not in manual:
        try:
            await bot.send_message(OWNER, f"⚠️ Проект {n} завершился с кодом {code}")
        except Exception:
            pass


async def start_proc(n):
    if running(n):
        return "уже запущен"
    d = ROOT / n
    if not (d / "main.py").exists():
        return "нет main.py"
    manual.discard(n)
    env = {k: v for k, v in os.environ.items() if k not in ("BOT_TOKEN", "OWNER_ID")}
    with open(plog(n), "ab") as lf:
        p = await asyncio.create_subprocess_exec(
            sys.executable, "-u", "main.py", cwd=d, env=env,
            stdout=lf, stderr=lf, start_new_session=True)
    procs[n] = p
    if n not in state["auto"]:
        state["auto"].append(n)
        save()
    asyncio.create_task(watch(n, p))
    return "запущен"


async def stop_proc(n):
    if n in state["auto"]:
        state["auto"].remove(n)
        save()
    if not running(n):
        return "не был запущен"
    manual.add(n)
    p = procs[n]
    try:
        os.killpg(p.pid, signal.SIGTERM)
        await asyncio.wait_for(p.wait(), 5)
    except asyncio.TimeoutError:
        os.killpg(p.pid, signal.SIGKILL)
        await p.wait()
    except ProcessLookupError:
        pass
    return "остановлен"


def tail(n, size=3500):
    f = plog(n)
    if not f.exists() or f.stat().st_size == 0:
        return "(лог пуст)"
    return f.read_bytes()[-size:].decode("utf-8", "replace")


async def refresh(msg, note=""):
    try:
        await msg.edit_text(panel() + (f"\n\n{note}" if note else ""),
                            reply_markup=kb(), parse_mode="HTML")
    except Exception:
        pass


def is_owner(o):
    return o.from_user is not None and o.from_user.id == OWNER


def create_project(name):
    if not NAME_RE.match(name):
        return "Имя: латиница, цифры, _ и -, до 30 символов."
    if name in projects():
        return "Такой проект уже есть."
    (ROOT / name).mkdir()
    state["current"] = name
    save()
    return None


def unzip(zpath, d):
    root = str(d.resolve())
    with zipfile.ZipFile(zpath) as z:
        infos = [i for i in z.infolist() if not i.filename.startswith("__MACOSX")]
        tops = {i.filename.split("/")[0] for i in infos}
        strip = len(tops) == 1 and all("/" in i.filename for i in infos)
        for i in infos:
            rel = i.filename.split("/", 1)[1] if strip else i.filename
            if not rel:
                continue
            t = (d / rel).resolve()
            if not str(t).startswith(root):
                continue
            if i.is_dir():
                t.mkdir(parents=True, exist_ok=True)
            else:
                t.parent.mkdir(parents=True, exist_ok=True)
                t.write_bytes(z.read(i))
    return len(infos)


@dp.message(CommandStart())
@dp.message(Command("panel"))
async def cmd_start(m: Message):
    if not is_owner(m):
        return await m.answer("Бот приватный.")
    await m.answer(panel(), reply_markup=kb(), parse_mode="HTML")


@dp.message(Command("new"))
async def cmd_new(m: Message):
    global awaiting_name
    if not is_owner(m):
        return
    name = (m.text or "").partition(" ")[2].strip()
    if not name:
        awaiting_name = True
        return await m.answer("Напиши имя нового проекта (латиница, цифры, _ -):")
    err = create_project(name)
    await m.answer(err or f"✅ Проект {name} создан. Присылай файлы.\n\n" + panel(),
                   reply_markup=kb(), parse_mode="HTML")


@dp.message(Command("del"))
async def cmd_del(m: Message):
    if not is_owner(m):
        return
    n = cur()
    rel = (m.text or "").partition(" ")[2].strip()
    if not n or not rel:
        return await m.answer("Использование: /del путь/к/файлу (в текущем проекте)")
    d = (ROOT / n).resolve()
    f = (d / rel).resolve()
    if str(f).startswith(str(d) + os.sep) and f.is_file():
        f.unlink()
        await m.answer(f"Удалён: {rel}")
    else:
        await m.answer("Файл не найден.")


@dp.message(F.document)
async def on_file(m: Message):
    if not is_owner(m):
        return
    n = cur()
    if not n:
        return await m.answer("Сначала создай проект: /new имя")
    d = ROOT / n
    name = Path(m.document.file_name or "file").name
    if name.lower().endswith(".zip"):
        tmp = LOGS / "_upload.zip"
        await bot.download(m.document, destination=tmp)
        try:
            k = unzip(tmp, d)
            txt = f"📦 Распаковано в {n}: {k} файлов"
        except zipfile.BadZipFile:
            txt = "❌ Битый zip"
        tmp.unlink(missing_ok=True)
    else:
        await bot.download(m.document, destination=d / name)
        txt = f"💾 Сохранён в {n}: {name}"
    await m.answer(txt + "\nЕсли проект запущен — нажми «Рестарт».", reply_markup=kb())


@dp.message(F.text)
async def on_text(m: Message):
    global awaiting_name
    if not is_owner(m) or not awaiting_name:
        return
    awaiting_name = False
    name = m.text.strip()
    err = create_project(name)
    await m.answer(err or f"✅ Проект {name} создан. Присылай файлы.\n\n" + panel(),
                   reply_markup=kb(), parse_mode="HTML")


@dp.callback_query()
async def on_cb(c: CallbackQuery):
    global awaiting_name
    if not is_owner(c):
        return await c.answer("Нет доступа", show_alert=True)
    a, msg = c.data, c.message
    await c.answer()

    if a == "list":
        return await msg.edit_text("<b>Проекты:</b>", reply_markup=list_kb(),
                                   parse_mode="HTML")
    if a.startswith("sel:"):
        state["current"] = a[4:]
        save()
        return await refresh(msg)
    if a == "new":
        awaiting_name = True
        return await msg.answer("Напиши имя нового проекта (латиница, цифры, _ -):")
    if a == "status":
        return await refresh(msg)

    n = cur()
    if not n:
        return await msg.answer("Сначала создай проект: /new имя")
    d = ROOT / n

    if a == "run":
        await refresh(msg, f"▶️ {await start_proc(n)}")
    elif a == "stop":
        await refresh(msg, f"⏹ {await stop_proc(n)}")
    elif a == "restart":
        await stop_proc(n)
        await refresh(msg, f"🔄 {await start_proc(n)}")
    elif a == "logs":
        await msg.answer(f"<pre>{html.escape(tail(n))}</pre>", parse_mode="HTML")
    elif a == "dl":
        if plog(n).exists() and plog(n).stat().st_size:
            await msg.answer_document(FSInputFile(plog(n)))
        else:
            await msg.answer("Лог пуст")
    elif a == "clear":
        plog(n).write_bytes(b"")
        await refresh(msg, "🧹 Логи очищены")
    elif a == "files":
        files = sorted(p.relative_to(d).as_posix() for p in d.rglob("*")
                       if p.is_file() and "__pycache__" not in p.parts)
        txt = "\n".join(f"• {f}" for f in files[:60]) or "(пусто)"
        if len(files) > 60:
            txt += f"\n… и ещё {len(files) - 60}"
        await msg.answer(f"<b>Файлы {n}:</b>\n{html.escape(txt)}\n\nУдалить: /del путь",
                         parse_mode="HTML")
    elif a == "pip":
        if not (d / "requirements.txt").exists():
            return await msg.answer("Пришли requirements.txt в этот проект")
        await msg.answer("📦 Устанавливаю...")
        p = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt", cwd=d,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        out, _ = await p.communicate()
        out = out.decode("utf-8", "replace")[-3000:]
        await msg.answer(f"{'✅' if p.returncode == 0 else '❌'}\n"
                         f"<pre>{html.escape(out)}</pre>", parse_mode="HTML")
    elif a == "delp":
        await msg.edit_text(
            f"Удалить проект <b>{n}</b> со всеми файлами и логами?",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [btn("✅ Да, удалить", "delyes"), btn("↩️ Нет", "status")]]))
    elif a == "delyes":
        await stop_proc(n)
        procs.pop(n, None)
        shutil.rmtree(d, ignore_errors=True)
        plog(n).unlink(missing_ok=True)
        left = projects()
        state["current"] = left[0] if left else None
        save()
        await refresh(msg, f"🗑 Проект {n} удалён")


async def web_server():
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="ok"))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000))).start()


async def main():
    await web_server()
    for n in list(state["auto"]):
        if n in projects():
            await start_proc(n)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
                                      
