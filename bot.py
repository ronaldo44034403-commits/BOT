import asyncio
import html
import os
import signal
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (CallbackQuery, FSInputFile, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)
from aiohttp import web

TOKEN = os.environ["8815285092:AAGSF8SFvu-xyDfBcmXHuCJ9LQEL5Z7HT3s"]
OWNER = int(os.environ["8869664157"])

DIR = Path("workdir")
DIR.mkdir(exist_ok=True)
LOG = Path("run.log")
FLAG = Path("autostart")

bot = Bot(TOKEN)
dp = Dispatcher()
proc = None
manual_stop = False


def running() -> bool:
    return proc is not None and proc.returncode is None


def kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardButton
    return InlineKeyboardMarkup(inline_keyboard=[
        [b(text="▶️ Запустить", callback_data="run"),
         b(text="⏹ Стоп", callback_data="stop"),
         b(text="🔄 Рестарт", callback_data="restart")],
        [b(text="📜 Логи", callback_data="logs"),
         b(text="📥 Скачать лог", callback_data="dl"),
         b(text="🧹 Очистить", callback_data="clear")],
        [b(text="📁 Файлы", callback_data="files"),
         b(text="📦 pip install", callback_data="pip"),
         b(text="🔃 Статус", callback_data="status")],
    ])


def panel() -> str:
    has = (DIR / "main.py").exists()
    if running():
        st = f"🟢 Работает (PID {proc.pid})"
    elif proc is not None:
        st = f"🔴 Остановлен (код {proc.returncode})"
    else:
        st = "⚪️ Не запущен"
    return (f"<b>Хостинг кода</b>\nСтатус: {st}\n"
            f"main.py: {'есть ✅' if has else 'нет ❌ — пришли файл'}")


async def watch(p):
    code = await p.wait()
    if p is proc and not manual_stop:
        try:
            await bot.send_message(OWNER, f"⚠️ Процесс завершился с кодом {code}",
                                   reply_markup=kb())
        except Exception:
            pass


async def start_proc():
    global proc, manual_stop
    if running():
        return "уже запущен"
    if not (DIR / "main.py").exists():
        return "нет main.py"
    manual_stop = False
    env = {k: v for k, v in os.environ.items() if k not in ("BOT_TOKEN", "OWNER_ID")}
    with open(LOG, "ab") as lf:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-u", "main.py", cwd=DIR, env=env,
            stdout=lf, stderr=lf, start_new_session=True)
    FLAG.touch()
    asyncio.create_task(watch(proc))
    return "запущен"


async def stop_proc():
    global manual_stop
    FLAG.unlink(missing_ok=True)
    if not running():
        return "не был запущен"
    manual_stop = True
    try:
        os.killpg(proc.pid, signal.SIGTERM)
        await asyncio.wait_for(proc.wait(), 5)
    except asyncio.TimeoutError:
        os.killpg(proc.pid, signal.SIGKILL)
        await proc.wait()
    except ProcessLookupError:
        pass
    return "остановлен"


def tail(n=3500) -> str:
    if not LOG.exists() or LOG.stat().st_size == 0:
        return "(лог пуст)"
    data = LOG.read_bytes()[-n:]
    return data.decode("utf-8", "replace")


async def refresh(msg: Message, note: str = ""):
    text = panel() + (f"\n\n{note}" if note else "")
    try:
        await msg.edit_text(text, reply_markup=kb(), parse_mode="HTML")
    except Exception:
        pass


def owner_only(obj) -> bool:
    return obj.from_user and obj.from_user.id == OWNER


@dp.message(CommandStart())
@dp.message(Command("panel"))
async def cmd_start(m: Message):
    if not owner_only(m):
        return await m.answer("Бот приватный.")
    await m.answer(panel(), reply_markup=kb(), parse_mode="HTML")


@dp.message(Command("del"))
async def cmd_del(m: Message):
    if not owner_only(m):
        return
    name = Path((m.text or "").partition(" ")[2].strip()).name
    f = DIR / name
    if name and f.is_file():
        f.unlink()
        await m.answer(f"Удалён: {name}")
    else:
        await m.answer("Использование: /del имя_файла")


@dp.message(F.document)
async def on_file(m: Message):
    if not owner_only(m):
        return
    name = Path(m.document.file_name or "file").name
    await bot.download(m.document, destination=DIR / name)
    extra = "\nЭто main.py — жми «Рестарт»." if name == "main.py" else ""
    await m.answer(f"💾 Сохранён: {name}{extra}", reply_markup=kb())


@dp.callback_query()
async def on_cb(c: CallbackQuery):
    if not owner_only(c):
        return await c.answer("Нет доступа", show_alert=True)
    a, msg = c.data, c.message
    await c.answer()

    if a == "run":
        await refresh(msg, f"▶️ {await start_proc()}")
    elif a == "stop":
        await refresh(msg, f"⏹ {await stop_proc()}")
    elif a == "restart":
        await stop_proc()
        await refresh(msg, f"🔄 {await start_proc()}")
    elif a == "status":
        await refresh(msg)
    elif a == "logs":
        await msg.answer(f"<pre>{html.escape(tail())}</pre>", parse_mode="HTML")
    elif a == "dl":
        if LOG.exists() and LOG.stat().st_size:
            await msg.answer_document(FSInputFile(LOG))
        else:
            await msg.answer("Лог пуст")
    elif a == "clear":
        LOG.write_bytes(b"")
        await refresh(msg, "🧹 Логи очищены")
    elif a == "files":
        files = sorted(p for p in DIR.iterdir() if p.is_file())
        txt = "\n".join(f"• {p.name} ({p.stat().st_size} Б)" for p in files) or "(пусто)"
        await msg.answer(f"<b>Файлы:</b>\n{html.escape(txt)}\n\nУдалить: /del имя",
                         parse_mode="HTML")
    elif a == "pip":
        req = DIR / "requirements.txt"
        if not req.exists():
            return await msg.answer("Пришли requirements.txt")
        await msg.answer("📦 Устанавливаю...")
        p = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "pip", "install", "-r", str(req),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        out, _ = await p.communicate()
        out = out.decode("utf-8", "replace")[-3000:]
        await msg.answer(f"{'✅' if p.returncode == 0 else '❌'}\n"
                         f"<pre>{html.escape(out)}</pre>", parse_mode="HTML")


async def web_server():
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="ok"))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000))).start()


async def main():
    await web_server()
    if FLAG.exists():
        await start_proc()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
