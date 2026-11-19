#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StarsShop - Telegram-бот: продажа Stars / Premium / Gift.
Только стандартная библиотека Python 3.8+ (pip ставить не нужно).

Запуск:   python bot.py
Токен:    впишите в TOKEN ниже или задайте переменную окружения BOT_TOKEN.
База:     файл база.xd (тот же формат, что у старого XD-бота - данные подхватятся).
"""
import html
import json
import os
import sys
import threading
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer

# ===================== НАСТРОЙКИ =====================
TOKEN = os.environ.get("BOT_TOKEN", "ВСТАВЬТЕ_ТОКЕН")   # на Render задайте переменную BOT_TOKEN
ADMIN = "8869664157"                      # ваш Telegram ID
SUPPORT = "https://t.me/MR_XD_TON"        # ссылка на поддержку
PHOTO = "img.png"                         # картинка во всех сообщениях ("" = выключить)
DB_FILE = os.environ.get("DB_FILE", "база.xd")   # на Render с диском: /data/база.xd

MIN_TOPUP = 1000
MAX_TOPUP = 1000000
BONUS_FROM = 200000     # бонус за пополнение от этой суммы (сум)
BONUS_PERCENT = 3       # сколько % добавить бонусом (0 = выключить)
REF_BONUS = 2000        # награда за приглашённого друга (после его первого пополнения)

STARS = [(50, 12000), (75, 16000), (100, 22000), (150, 35000), (200, 46000)]
PREMIUM = [(3, 160000), (6, 215000), (12, 400000)]
GIFTS = [("🧸", 3000), ("💝", 3000), ("🌹", 5000), ("🎁", 5000), ("💐", 10000),
         ("🚀", 10000), ("🏆", 20000), ("💍", 20000), ("💎", 20000)]
HITS = {("s", 2), ("p", 1)}               # какие товары помечать 🔥

API = os.environ.get("TG_API", "https://api.telegram.org")

# ===================== ТЕКСТЫ =====================
T = {
 "ru": {
  "welcome": "👋 Здравствуйте, {имя}!\n\n<blockquote>⭐ Telegram Stars — быстро и дёшево\n💎 Telegram Premium — особые возможности\n🎁 Telegram Gift — подарок друзьям</blockquote>\n\n💰 Ваш баланс: {баланс} сум\n\nВыберите нужную услугу:",
  "b_buy": "🛒 Купить",
  "b_bal": "👛 Мой счёт",
  "b_lang": "🌐 Язык",
  "b_sup": "🧑‍💻 Поддержка",
  "b_ord": "📦 Мои заказы",
  "b_ref": "👥 Пригласить друзей",
  "b_buys": "⭐ Купить Stars",
  "b_buyp": "💎 Купить Premium",
  "b_buyg": "🎁 Купить Gift",
  "b_top": "🏆 Топ рейтинг",
  "b_set": "⚙ Настройки",
  "set_title": "⚙ Настройки\n\nЗдесь можно сменить язык, посмотреть свои заказы и пригласить друзей.",
  "top_title": "🏆 Топ покупателей\n\nСамые активные клиенты магазина:",
  "top_none": "Пока никто ничего не купил — станьте первым! 🚀",
  "top_you": "💳 Вы потратили: {сумма} сум",
  "b_back": "⬅ Назад",
  "b_menu": "🏠 Меню",
  "b_stars": "⭐ Звёзды",
  "b_prem": "💎 Премиум",
  "b_gift": "🎁 Гифты",
  "buy_title": "🛒 Что хотите купить?\n\n⭐ Stars — для подарков, донатов и оплаты в Telegram\n💎 Premium — все возможности Telegram\n🎁 Gift — красивые подарки друзьям",
  "pick_s": "⭐ Telegram Stars\nВыберите пакет (цена в сум) 👇",
  "pick_p": "💎 Telegram Premium\nВыберите срок (цена в сум) 👇",
  "pick_g": "🎁 Telegram Gift\nВыберите подарок (цена в сум) 👇",
  "bal": "💰 Ваш баланс: {сумма} сум\n\nПополните баланс и покупайте в пару нажатий 👇",
  "b_pay": "💳 Оплата",
  "b_chk": "🧾 Отправить чек",
  "b_topup": "➕ Пополнить",
  "pay_ask": "💳 Выберите сумму пополнения кнопкой или введите свою — от 1 000 до 1 000 000 сум (только число, например 25000):",
  "promo": "\n\n🎁 Пополните от {от} сум — и получите +{проц}% бонусом на баланс!",
  "pay_bad": "❌ Сумма должна быть числом от 1 000 до 1 000 000. Попробуйте ещё раз:",
  "pay_instr": "💳 Пополнение на {сумма} сум\n\n1⃣ Подойдите к любому ближайшему терминалу Paynet\n2⃣ Найдите «boostify.uz» в поиске или в разделе «Интернет и ТВ»\n3⃣ Введите Telegram ID 8869664157\n4⃣ Проверьте имя и оплатите {сумма} сум наличными или картой\nИмя: XD #XD 広沢和也\n5⃣ После оплаты нажмите «🧾 Отправить чек» и пришлите скриншот чека в бота",
  "chk_ask": "📸 Пришлите скриншот или фото чека одним сообщением.",
  "chk_none": "Сначала нажмите «💳 Оплата» и укажите сумму пополнения.",
  "chk_sent": "✅ Чек отправлен администратору. Ожидайте подтверждения — обычно это быстро ⚡",
  "topup_ok": "✅ Баланс пополнен на {сумма} сум.",
  "bonus_line": "\n🎁 Бонус: +{бонус} сум",
  "topup_bal": "\n💰 Ваш баланс: {баланс} сум\n\nТеперь можно покупать 👇",
  "topup_no": "❌ Чек отклонён администратором. Если это ошибка — напишите в поддержку.",
  "need_more": "❌ Недостаточно средств. Нужно {цена} сум, на балансе {баланс} сум.\n\nПополните баланс 👇",
  "ask_user": "✍ Введите @username получателя\n🛍 Товар: {товар}\n\nЕсли покупаете себе — свой @username:",
  "bad_user": "❌ Введите @username, например @durov",
  "confirm": "🧾 Ваш заказ\n\n🛍 Товар: {товар}\n👤 Получатель: {получатель}\n💵 Цена: {цена} сум\n\nПосле подтверждения сумма спишется с баланса.",
  "b_yes": "✅ Подтвердить",
  "b_cancel": "❌ Отмена",
  "ordered": "✅ Заказ №{id} принят!\n💵 {цена} сум списано с баланса.\n\nМы выполним его и сообщим вам сюда 💙",
  "done": "🎉 Заказ №{id} выполнен! Спасибо за покупку 💙\n\nЖдём вас снова!",
  "rejected": "❌ Заказ №{id} отклонён. {цена} сум возвращены на баланс.",
  "cancelled": "Отменено.",
  "unknown": "Не понял 🤔 Нажмите /start",
  "ord_title": "📦 Ваши последние заказы:",
  "ord_none": "📦 У вас пока нет заказов.\nСамое время купить первый 👇",
  "st_w": "⏳ в обработке",
  "st_d": "✅ выполнен",
  "st_r": "❌ отклонён",
  "ref_text": "👥 Приглашайте друзей!\n\nЗа каждого друга, который пополнит баланс, вы получите {бонус} сум на свой баланс.\n\n🔗 Ваша ссылка:\n{ссылка}\n\n👤 Приглашено друзей: {n}",
  "ref_got": "🎉 Ваш друг пополнил баланс! Вам начислено {сумма} сум за приглашение."
 },
 "uz": {
  "welcome": "👋 Assalomu alaykum, {имя}!\n\n<blockquote>⭐ Telegram Stars — tez va arzon\n💎 Telegram Premium — maxsus imkoniyatlar\n🎁 Telegram Gift — do'stlarga sovg'a</blockquote>\n\n💰 Balansingiz: {баланс} so'm\n\nKerakli xizmatni tanlang:",
  "b_buy": "🛒 Sotib olish",
  "b_bal": "👛 Hisobim",
  "b_lang": "🌐 Til",
  "b_sup": "🧑‍💻 Yordam",
  "b_ord": "📦 Buyurtmalarim",
  "b_ref": "👥 Do'st taklif qilish",
  "b_buys": "⭐ Stars sotib olish",
  "b_buyp": "💎 Premium sotib olish",
  "b_buyg": "🎁 Gift sotib olish",
  "b_top": "🏆 Reyting",
  "b_set": "⚙ Sozlamalar",
  "set_title": "⚙ Sozlamalar\n\nBu yerda tilni almashtirish, buyurtmalarni ko'rish va do'st taklif qilish mumkin.",
  "top_title": "🏆 Eng yaxshi xaridorlar\n\nDo'kondagi eng faol mijozlar:",
  "top_none": "Hozircha hech kim hech narsa sotib olmadi — birinchi bo'ling! 🚀",
  "top_you": "💳 Siz sarfladingiz: {сумма} so'm",
  "b_back": "⬅ Orqaga",
  "b_menu": "🏠 Menyu",
  "b_stars": "⭐ Stars",
  "b_prem": "💎 Premium",
  "b_gift": "🎁 Giftlar",
  "buy_title": "🛒 Nimani sotib olmoqchisiz?\n\n⭐ Stars — sovg'a, donat va Telegram'da to'lov uchun\n💎 Premium — Telegram'ning barcha imkoniyatlari\n🎁 Gift — do'stlarga chiroyli sovg'alar",
  "pick_s": "⭐ Telegram Stars\nPaketni tanlang (narx so'mda) 👇",
  "pick_p": "💎 Telegram Premium\nMuddatni tanlang (narx so'mda) 👇",
  "pick_g": "🎁 Telegram Gift\nSovg'ani tanlang (narx so'mda) 👇",
  "bal": "💰 Balansingiz: {сумма} so'm\n\nBalansni to'ldiring va bir necha bosishda xarid qiling 👇",
  "b_pay": "💳 To'lov",
  "b_chk": "🧾 Chekni yuborish",
  "b_topup": "➕ To'ldirish",
  "pay_ask": "💳 To'ldirish summasini tugma bilan tanlang yoki o'zingiz kiriting — 1 000 dan 1 000 000 so'mgacha (faqat raqam, masalan 25000):",
  "promo": "\n\n🎁 {от} so'mdan ko'p to'ldiring — balansga +{проц}% bonus oling!",
  "pay_bad": "❌ Summa 1 000 dan 1 000 000 gacha bo'lgan raqam bo'lishi kerak. Qayta urinib ko'ring:",
  "pay_instr": "💳 {сумма} so'm to'ldirish\n\n1⃣ Eng yaqin Paynet terminaliga boring\n2⃣ Qidiruvdan «boostify.uz» ni toping yoki «Internet va TV» bo'limiga kiring\n3⃣ Telegram ID kiriting: 8869664157\n4⃣ Ismni tekshiring va {сумма} so'mni naqd yoki karta orqali to'lang\nIsm: XD #XD 広沢和也\n5⃣ To'lovdan so'ng «🧾 Chekni yuborish» tugmasini bosing va chek skrinshotini botga yuboring",
  "chk_ask": "📸 Chek skrinshotini yoki rasmini bitta xabarda yuboring.",
  "chk_none": "Avval «💳 To'lov» tugmasini bosing va to'ldirish summasini kiriting.",
  "chk_sent": "✅ Chek administratorga yuborildi. Tasdiqlashni kuting — odatda tez ⚡",
  "topup_ok": "✅ Balans {сумма} so'mga to'ldirildi.",
  "bonus_line": "\n🎁 Bonus: +{бонус} so'm",
  "topup_bal": "\n💰 Balansingiz: {баланс} so'm\n\nEndi xarid qilishingiz mumkin 👇",
  "topup_no": "❌ Chek administrator tomonidan rad etildi. Xato bo'lsa, yordamga yozing.",
  "need_more": "❌ Mablag' yetarli emas. Kerak: {цена} so'm, balansda: {баланс} so'm.\n\nBalansni to'ldiring 👇",
  "ask_user": "✍ Qabul qiluvchining @username manzilini kiriting\n🛍 Mahsulot: {товар}\n\nO'zingiz uchun bo'lsa — o'z @username'ingizni yozing:",
  "bad_user": "❌ @username kiriting, masalan @durov",
  "confirm": "🧾 Buyurtmangiz\n\n🛍 Mahsulot: {товар}\n👤 Qabul qiluvchi: {получатель}\n💵 Narxi: {цена} so'm\n\nTasdiqlangandan so'ng summa balansdan yechiladi.",
  "b_yes": "✅ Tasdiqlash",
  "b_cancel": "❌ Bekor qilish",
  "ordered": "✅ №{id} buyurtma qabul qilindi!\n💵 Balansdan {цена} so'm yechildi.\n\nBajarib, shu yerda xabar beramiz 💙",
  "done": "🎉 №{id} buyurtma bajarildi! Xaridingiz uchun rahmat 💙\n\nYana kutamiz!",
  "rejected": "❌ №{id} buyurtma rad etildi. {цена} so'm balansga qaytarildi.",
  "cancelled": "Bekor qilindi.",
  "unknown": "Tushunmadim 🤔 /start ni bosing",
  "ord_title": "📦 Oxirgi buyurtmalaringiz:",
  "ord_none": "📦 Hozircha buyurtmalaringiz yo'q.\nBirinchisini olish vaqti keldi 👇",
  "st_w": "⏳ jarayonda",
  "st_d": "✅ bajarildi",
  "st_r": "❌ rad etildi",
  "ref_text": "👥 Do'stlaringizni taklif qiling!\n\nBalansini to'ldirgan har bir do'st uchun balansingizga {бонус} so'm olasiz.\n\n🔗 Sizning havolangiz:\n{ссылка}\n\n👤 Taklif qilingan do'stlar: {n}",
  "ref_got": "🎉 Do'stingiz balansini to'ldirdi! Taklif uchun sizga {сумма} so'm berildi."
 }
}

# ===================== БАЗА ДАННЫХ =====================
DB = {"польз": {}, "заказы": {}, "пополн": {}, "счёт": 0}
state = {}          # режимы диалога: {chat: {...}}
BOT_USERNAME = ""
photo_id = None


def load_db():
    global DB
    try:
        with open(DB_FILE, encoding="utf-8") as f:
            data = json.load(f)
        for k, v in {"польз": {}, "заказы": {}, "пополн": {}, "счёт": 0}.items():
            data.setdefault(k, v)
        DB = data
    except FileNotFoundError:
        pass
    except Exception as e:
        print("Не могу прочитать базу:", e)
        sys.exit(1)      # лучше остановиться, чем затереть базу пустой


def save_db():
    tmp = DB_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(DB, f, ensure_ascii=False)
    os.replace(tmp, DB_FILE)


# ===================== TELEGRAM API =====================
def _multipart(fields, files):
    boundary = uuid.uuid4().hex
    body = b""
    for k, v in fields.items():
        body += ('--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n' % (boundary, k)).encode()
        body += str(v).encode("utf-8") + b"\r\n"
    for k, (fname, data) in files.items():
        body += ('--%s\r\nContent-Disposition: form-data; name="%s"; filename="%s"\r\n'
                 'Content-Type: application/octet-stream\r\n\r\n' % (boundary, k, fname)).encode()
        body += data + b"\r\n"
    body += ("--%s--\r\n" % boundary).encode()
    return body, "multipart/form-data; boundary=" + boundary


def api(method, files=None, **params):
    data = {}
    for k, v in params.items():
        if v is None:
            continue
        data[k] = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
    try:
        if files:
            body, ctype = _multipart(data, files)
        else:
            body, ctype = urllib.parse.urlencode(data).encode(), "application/x-www-form-urlencoded"
        req = urllib.request.Request("%s/bot%s/%s" % (API, TOKEN, method), body, {"Content-Type": ctype})
        with urllib.request.urlopen(req, timeout=70) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            return {"ok": False, "description": str(e)}
    except Exception as e:
        return {"ok": False, "description": str(e)}


def ok(r):
    return bool(r.get("ok"))


def err(r):
    return r.get("description", "")


def markup(kb):
    """kb = [[(текст, данные), ...], ...] - строки кнопок. Данные http... = кнопка-ссылка."""
    if not kb:
        return None
    rows = []
    for row in kb:
        rows.append([({"text": t, "url": d} if d.startswith(("http", "tg:")) else {"text": t, "callback_data": d})
                     for t, d in row])
    return {"inline_keyboard": rows}


def send_photo(chat, text, kb):
    global photo_id
    if not PHOTO or not os.path.exists(PHOTO) or len(text) > 1000:
        return False
    for use_html in (True, False):
        for use_id in ([True, False] if photo_id else [False]):
            p = dict(chat_id=chat, caption=text, reply_markup=markup(kb),
                     parse_mode="HTML" if use_html else None)
            if use_id:
                r = api("sendPhoto", photo=photo_id, **p)
            else:
                with open(PHOTO, "rb") as f:
                    r = api("sendPhoto", files={"photo": (os.path.basename(PHOTO), f.read())}, **p)
            if ok(r):
                if not photo_id:
                    try:
                        photo_id = r["result"]["photo"][-1]["file_id"]
                    except Exception:
                        pass
                return True
            if "parse entities" in err(r):
                break                       # повторить без HTML
            if use_id:
                photo_id = None             # id не подошёл - грузим файл заново
            else:
                print("Telegram (фото):", err(r))
                return False
    return False


def send(chat, text, kb=None, photo=True):
    if photo and send_photo(chat, text, kb):
        return
    r = api("sendMessage", chat_id=chat, text=text, parse_mode="HTML", reply_markup=markup(kb))
    if not ok(r) and "parse entities" in err(r):
        r = api("sendMessage", chat_id=chat, text=text, reply_markup=markup(kb))
    if not ok(r):
        print("Telegram:", err(r))


def send_plain(chat, text, kb=None):
    """Сообщение без картинки (для служебных сообщений админу)."""
    send(chat, text, kb, photo=False)


def edit(chat, mid, text, kb=None):
    methods = []
    if PHOTO:
        methods.append(("editMessageCaption", "caption"))
    methods.append(("editMessageText", "text"))
    for method, field in methods:
        p = {field: text}
        r = api(method, chat_id=chat, message_id=mid, parse_mode="HTML", reply_markup=markup(kb), **p)
        if not ok(r) and "parse entities" in err(r):
            r = api(method, chat_id=chat, message_id=mid, reply_markup=markup(kb), **p)
        if ok(r) or "not modified" in err(r):
            return
    send(chat, text, kb)


def clear_buttons(chat, mid):
    api("editMessageReplyMarkup", chat_id=chat, message_id=mid, reply_markup={"inline_keyboard": []})


# ===================== ВСПОМОГАТЕЛЬНОЕ =====================
def esc(s):
    return html.escape(str(s), quote=False)


def money(n):
    return "{:,}".format(int(n)).replace(",", " ")


def get_user(chat, name=""):
    if chat not in DB["польз"]:
        DB["польз"][chat] = {"яз": "", "баланс": 0, "имя": name, "реф": "", "потрачено": 0}
        save_db()
    return DB["польз"][chat]


def lang(chat):
    u = DB["польз"].get(chat)
    return u["яз"] if u and u.get("яз") else "ru"


def tr(chat, key):
    return T[lang(chat)][key]


def items(kind):
    return {"s": STARS, "p": PREMIUM}.get(kind, GIFTS)


def price(kind, i):
    return items(kind)[i][1]


def item_name(kind, i, lg):
    if kind == "s":
        return "%d ⭐ Stars" % STARS[i][0]
    if kind == "p":
        return ("Premium %d oy" if lg == "uz" else "Premium %d мес.") % PREMIUM[i][0]
    return "Gift " + GIFTS[i][0]


def item_label(kind, i, lg):
    hot = " 🔥" if (kind, i) in HITS else ""
    if kind == "s":
        return "%d ⭐ · %s%s" % (STARS[i][0], money(STARS[i][1]), hot)
    if kind == "p":
        return ("💎 %d oy · %s%s" if lg == "uz" else "💎 %d мес. · %s%s") % (PREMIUM[i][0], money(PREMIUM[i][1]), hot)
    return "%s · %s" % (GIFTS[i][0], money(GIFTS[i][1]))


def status_text(chat, st):
    return tr(chat, {"выполнен": "st_d", "отклонён": "st_r"}.get(st, "st_w"))


def topup_bonus(n):
    if BONUS_PERCENT > 0 and n >= BONUS_FROM:
        return int(n * BONUS_PERCENT / 100)
    return 0


def pending_topup(chat):
    found = ""
    for k, z in DB["пополн"].items():
        if z["чат"] == chat and z["статус"] == "ждёт":
            found = k
    return found


class Ctx:
    """Один входящий апдейт: кто пишет и (если это нажатие кнопки) под каким сообщением."""

    def __init__(self, chat, name, mid=None):
        self.chat, self.name, self.mid = chat, name, mid

    def tr(self, key):
        return tr(self.chat, key)

    def show(self, text, kb=None):
        """Нажатие кнопки -> правим то же сообщение; обычное сообщение -> новое."""
        if self.mid:
            edit(self.chat, self.mid, text, kb)
        else:
            send(self.chat, text, kb)

    def say(self, text, kb=None):
        send(self.chat, text, kb)

    def admin_say(self, text, kb=None):
        send_plain(self.chat, text, kb)


# ===================== ЭКРАНЫ =====================
def kb_menu(c):
    t = c.tr
    return [[(t("b_buys"), "cat:s"), (t("b_buyp"), "cat:p")],
            [(t("b_buyg"), "cat:g")],
            [(t("b_topup"), "pay"), (t("b_bal"), "bal")],
            [(t("b_top"), "top"), (t("b_set"), "set")],
            [(t("b_sup"), SUPPORT)]]


def show_menu(c):
    u = get_user(c.chat, c.name)
    link = '<a href="tg://user?id=%s">%s</a>' % (c.chat, esc(c.name))
    text = c.tr("welcome").replace("{имя}", link).replace("{баланс}", money(u["баланс"]))
    c.show(text, kb_menu(c))


def show_language(c):
    c.show("🌐 Tilni tanlang / Выберите язык:", [[("🇷🇺 Русский", "lang:ru")], [("🇺🇿 O'zbekcha", "lang:uz")]])


def set_language(c, lg):
    if lg not in T:
        return
    get_user(c.chat, c.name)["яз"] = lg
    save_db()
    show_menu(c)


def show_items(c, kind):
    lg = lang(c.chat)
    kb, row = [], []
    for i in range(len(items(kind))):
        b = (item_label(kind, i, lg), "it:%s:%d" % (kind, i))
        if kind == "p":
            kb.append([b])
        else:
            row.append(b)
            if len(row) == 2:
                kb.append(row)
                row = []
    if row:
        kb.append(row)
    kb.append([(c.tr("b_back"), "menu")])
    c.show(c.tr("pick_" + kind), kb)


def not_enough(c, cost, bal):
    text = c.tr("need_more").replace("{цена}", money(cost)).replace("{баланс}", money(bal))
    c.show(text, [[(c.tr("b_topup"), "pay")], [(c.tr("b_back"), "menu")]])


def choose_item(c, kind, i):
    if kind not in ("s", "p", "g") or not (0 <= i < len(items(kind))):
        return
    u = get_user(c.chat, c.name)
    cost = price(kind, i)
    if u["баланс"] < cost:
        not_enough(c, cost, u["баланс"])
        return
    state[c.chat] = {"режим": "получатель", "тип": kind, "i": i}
    c.show(c.tr("ask_user").replace("{товар}", item_name(kind, i, lang(c.chat))), [[(c.tr("b_cancel"), "cancel")]])


def got_recipient(c, text):
    s = state[c.chat]
    u = text.strip()
    if not (u.startswith("@") and len(u) >= 4 and " " not in u):
        c.say(c.tr("bad_user"))
        return
    u = esc(u)
    s["режим"], s["получатель"] = "подтверждение", u
    msg = (c.tr("confirm").replace("{товар}", item_name(s["тип"], s["i"], lang(c.chat)))
           .replace("{получатель}", u).replace("{цена}", money(price(s["тип"], s["i"]))))
    c.say(msg, [[(c.tr("b_yes"), "ok")], [(c.tr("b_cancel"), "cancel")]])


def cancel(c):
    state.pop(c.chat, None)
    c.show(c.tr("cancelled"), [[(c.tr("b_menu"), "menu")]])


def confirm_order(c):
    s = state.get(c.chat)
    if not s or s.get("режим") != "подтверждение":
        show_menu(c)
        return
    cost = price(s["тип"], s["i"])
    u = get_user(c.chat, c.name)
    if u["баланс"] < cost:
        not_enough(c, cost, u["баланс"])
        return
    u["баланс"] -= cost
    DB["счёт"] += 1
    oid = str(DB["счёт"])
    DB["заказы"][oid] = {"чат": c.chat, "имя": c.name, "тип": s["тип"], "i": s["i"],
                         "получатель": s["получатель"], "цена": cost, "статус": "ожидает"}
    save_db()
    state.pop(c.chat, None)
    c.show(c.tr("ordered").replace("{id}", oid).replace("{цена}", money(cost)),
           [[(c.tr("b_ord"), "ord")], [(c.tr("b_menu"), "menu")]])
    send_plain(ADMIN,
               "🛒 Новый заказ №%s\nПокупатель: %s (%s)\nТовар: %s\nПолучатель: %s\nЦена: %s сум"
               % (oid, esc(c.name), c.chat, item_name(s["тип"], s["i"], "ru"), s["получатель"], money(cost)),
               [[("✅ Выполнено", "oo:" + oid), ("❌ Отклонить", "on:" + oid)]])


def show_orders(c):
    lines = []
    for oid, z in DB["заказы"].items():
        if z["чат"] == c.chat:
            lines.append("№%s · %s · %s сум\n%s → %s" % (oid, item_name(z["тип"], z["i"], lang(c.chat)),
                                                         money(z["цена"]), status_text(c.chat, z["статус"]), z["получатель"]))
    text = c.tr("ord_none") if not lines else c.tr("ord_title") + "\n\n" + "\n\n".join(lines[-5:])
    c.show(text, [[(c.tr("b_buy"), "menu")], [(c.tr("b_back"), "set")]])


def show_referral(c):
    if not BOT_USERNAME:
        return
    n = sum(1 for u in DB["польз"].values() if u.get("реф") == c.chat)
    link = "https://t.me/%s?start=ref%s" % (BOT_USERNAME, c.chat)
    text = (c.tr("ref_text").replace("{бонус}", money(REF_BONUS)).replace("{ссылка}", link).replace("{n}", str(n)))
    c.show(text, [[(c.tr("b_back"), "set")]])


def show_settings(c):
    kb = [[(c.tr("b_lang"), "lng"), (c.tr("b_ord"), "ord")]]
    if BOT_USERNAME:
        kb.append([(c.tr("b_ref"), "ref")])
    kb.append([(c.tr("b_back"), "menu")])
    c.show(c.tr("set_title"), kb)


def show_top(c):
    ranked = sorted(((u.get("потрачено", 0), u.get("имя", "")) for u in DB["польз"].values() if u.get("потрачено", 0) > 0),
                    key=lambda x: -x[0])[:10]
    medals = ["🥇", "🥈", "🥉"]
    lines = ["%s %s — %s сум" % (medals[i] if i < 3 else "▫", esc(name), money(spent))
             for i, (spent, name) in enumerate(ranked)]
    text = c.tr("top_title") + "\n\n" + ("\n".join(lines) if lines else c.tr("top_none"))
    mine = get_user(c.chat, c.name).get("потрачено", 0)
    text += "\n\n" + c.tr("top_you").replace("{сумма}", money(mine))
    c.show(text, [[(c.tr("b_back"), "menu")]])


# ===================== БАЛАНС И ПОПОЛНЕНИЕ =====================
def show_balance(c):
    u = get_user(c.chat, c.name)
    c.show(c.tr("bal").replace("{сумма}", money(u["баланс"])),
           [[(c.tr("b_topup"), "pay"), (c.tr("b_chk"), "chk")], [(c.tr("b_ord"), "ord")], [(c.tr("b_back"), "menu")]])


def ask_amount(c):
    state[c.chat] = {"режим": "сумма"}
    text = c.tr("pay_ask")
    if BONUS_PERCENT > 0:
        text += c.tr("promo").replace("{от}", money(BONUS_FROM)).replace("{проц}", str(BONUS_PERCENT))
    c.show(text, [[("25 000", "sum:25000"), ("50 000", "sum:50000")],
                  [("100 000", "sum:100000"), ("200 000", "sum:200000")],
                  [(c.tr("b_back"), "bal")]])


def got_amount(c, text):
    raw = text.replace(" ", "").replace(",", "")
    if not raw.isdigit() or not (MIN_TOPUP <= int(raw) <= MAX_TOPUP):
        c.say(c.tr("pay_bad"))
        return
    n = int(raw)
    state.pop(c.chat, None)
    for z in DB["пополн"].values():
        if z["чат"] == c.chat and z["статус"] == "ждёт":
            z["статус"] = "отменена"
    DB["счёт"] += 1
    tid = str(DB["счёт"])
    DB["пополн"][tid] = {"чат": c.chat, "имя": c.name, "сумма": n, "статус": "ждёт"}
    save_db()
    c.say(c.tr("pay_instr").replace("{сумма}", money(n)),
          [[(c.tr("b_chk"), "chk")], [(c.tr("b_back"), "bal")]])


def chk_button(c):
    if not pending_topup(c.chat):
        c.show(c.tr("chk_none"), [[(c.tr("b_topup"), "pay")], [(c.tr("b_back"), "bal")]])
    else:
        c.show(c.tr("chk_ask"), [[(c.tr("b_back"), "bal")]])


def got_receipt(c, message_id):
    get_user(c.chat, c.name)
    tid = pending_topup(c.chat)
    if not tid:
        c.say(c.tr("chk_none"), [[(c.tr("b_topup"), "pay")]])
        return
    z = DB["пополн"][tid]
    z["статус"] = "на проверке"
    save_db()
    caption = ("💳 Пополнение №%s\nПокупатель: %s (%s)\nСумма: %s сум\n\nПроверьте чек и подтвердите."
               % (tid, esc(c.name), c.chat, money(z["сумма"])))
    r = api("copyMessage", chat_id=ADMIN, from_chat_id=c.chat, message_id=message_id, caption=caption,
            parse_mode="HTML", reply_markup=markup([[("✅ Подтвердить", "to:" + tid), ("❌ Отклонить", "tn:" + tid)]]))
    if not ok(r):
        print("Telegram (чек):", err(r))
    c.say(c.tr("chk_sent"))


# ===================== РЕШЕНИЯ АДМИНА =====================
def topup_result(c, tid, approve):
    z = DB["пополн"].get(tid)
    if not z:
        return
    if z["статус"] != "на проверке":
        c.admin_say("Заявка №%s уже обработана" % tid)
        return
    clear_buttons(c.chat, c.mid)
    buyer = z["чат"]
    if approve:
        z["статус"] = "принята"
        bonus = topup_bonus(z["сумма"])
        u = get_user(buyer, z.get("имя", ""))
        u["баланс"] += z["сумма"] + bonus
        friend = u.get("реф")
        if friend and not u.get("реф_ок"):
            u["реф_ок"] = 1
            if friend in DB["польз"]:
                DB["польз"][friend]["баланс"] += REF_BONUS
                send(friend, tr(friend, "ref_got").replace("{сумма}", money(REF_BONUS)))
        save_db()
        c.admin_say("✅ Пополнение №%s подтверждено: +%s сум (бонус: %s)" % (tid, money(z["сумма"]), money(bonus)))
        t = lambda k: tr(buyer, k)
        msg = t("topup_ok").replace("{сумма}", money(z["сумма"]))
        if bonus > 0:
            msg += t("bonus_line").replace("{бонус}", money(bonus))
        msg += t("topup_bal").replace("{баланс}", money(u["баланс"]))
        send(buyer, msg, [[(t("b_buy"), "menu")], [(t("b_menu"), "menu")]])
    else:
        z["статус"] = "отклонена"
        save_db()
        c.admin_say("❌ Пополнение №%s отклонено" % tid)
        send(buyer, tr(buyer, "topup_no"))


def order_result(c, oid, approve):
    z = DB["заказы"].get(oid)
    if not z:
        return
    if z["статус"] != "ожидает":
        c.admin_say("Заказ №%s уже обработан" % oid)
        return
    clear_buttons(c.chat, c.mid)
    buyer = z["чат"]
    if approve:
        z["статус"] = "выполнен"
        u = get_user(buyer)
        u["потрачено"] = u.get("потрачено", 0) + z["цена"]
        save_db()
        c.admin_say("✅ Заказ №%s отмечен выполненным" % oid)
        t = lambda k: tr(buyer, k)
        send(buyer, t("done").replace("{id}", oid), [[(t("b_buy"), "menu")], [(t("b_menu"), "menu")]])
    else:
        z["статус"] = "отклонён"
        get_user(buyer)["баланс"] += z["цена"]
        save_db()
        c.admin_say("❌ Заказ №%s отклонён, деньги возвращены покупателю" % oid)
        send(buyer, tr(buyer, "rejected").replace("{id}", oid).replace("{цена}", money(z["цена"])))


# ===================== КОМАНДЫ АДМИНА =====================
def stats(c):
    total = sum(u["баланс"] for u in DB["польз"].values())
    waiting = sum(1 for z in DB["заказы"].values() if z["статус"] == "ожидает")
    done = [z for z in DB["заказы"].values() if z["статус"] == "выполнен"]
    checks = sum(1 for z in DB["пополн"].values() if z["статус"] == "на проверке")
    c.admin_say("📊 Статистика\n\n👥 Клиентов: %d\n💰 Сумма на балансах: %s сум\n\n✅ Выполнено заказов: %d\n"
                "💵 Оборот: %s сум\n⏳ Ждут выполнения: %d\n🧾 Чеков на проверке: %d"
                % (len(DB["польз"]), money(total), len(done), money(sum(z["цена"] for z in done)), waiting, checks))


def broadcast(c, text):
    if not text:
        c.admin_say("Напишите: /send текст сообщения — он уйдёт всем клиентам")
        return
    n = 0
    for chat in list(DB["польз"]):
        send(chat, text)
        n += 1
        time.sleep(0.05)
    c.admin_say("✅ Рассылка отправлена: %d чел." % n)


# ===================== ОБРАБОТЧИКИ =====================
def cmd_start(c, args):
    new = c.chat not in DB["польз"]
    u = get_user(c.chat, c.name)
    if new and args.startswith("ref"):
        friend = args[3:]
        if friend != c.chat and friend in DB["польз"]:
            u["реф"] = friend
            save_db()
    state.pop(c.chat, None)
    show_language(c) if not u["яз"] else show_menu(c)


def on_button(c, d):
    get_user(c.chat, c.name)
    if d in ("menu", "buy"):
        show_menu(c)
    elif d == "bal":
        show_balance(c)
    elif d == "pay":
        ask_amount(c)
    elif d == "chk":
        chk_button(c)
    elif d == "lng":
        show_language(c)
    elif d == "ord":
        show_orders(c)
    elif d == "ref":
        show_referral(c)
    elif d == "set":
        show_settings(c)
    elif d == "top":
        show_top(c)
    elif d == "ok":
        confirm_order(c)
    elif d == "cancel":
        cancel(c)
    elif d.startswith("sum:"):
        got_amount(c, d[4:])
    elif d.startswith("lang:"):
        set_language(c, d[5:])
    elif d.startswith("cat:"):
        if d[4:] in ("s", "p", "g"):
            show_items(c, d[4:])
    elif d.startswith("it:"):
        parts = d.split(":")
        if len(parts) == 3 and parts[2].isdigit():
            choose_item(c, parts[1], int(parts[2]))
    elif c.chat == ADMIN and d[:3] in ("oo:", "on:"):
        order_result(c, d[3:], d.startswith("oo:"))
    elif c.chat == ADMIN and d[:3] in ("to:", "tn:"):
        topup_result(c, d[3:], d.startswith("to:"))


def on_text(c, text):
    if text.startswith("/"):
        head, _, rest = text.partition(" ")
        rest = rest.strip()
        cmd = head[1:].split("@")[0].lower()
        if cmd in ("start", "menu"):
            cmd_start(c, rest)
            return
        if cmd == "stat" and c.chat == ADMIN:
            stats(c)
            return
        if cmd == "send" and c.chat == ADMIN:
            broadcast(c, rest)
            return
    u = get_user(c.chat, c.name)
    mode = state.get(c.chat, {}).get("режим")
    if mode == "сумма":
        got_amount(c, text)
    elif mode == "получатель":
        got_recipient(c, text)
    elif not u["яз"]:
        show_language(c)
    else:
        c.say(c.tr("unknown"), kb_menu(c))


def handle_update(upd):
    if "callback_query" in upd:
        q = upd["callback_query"]
        api("answerCallbackQuery", callback_query_id=q["id"])
        msg = q.get("message")
        if not msg:
            return
        c = Ctx(str(msg["chat"]["id"]), q["from"].get("first_name", ""), msg["message_id"])
        print("<- [кнопка]", q.get("data", ""))
        on_button(c, q.get("data", ""))
    elif "message" in upd:
        m = upd["message"]
        c = Ctx(str(m["chat"]["id"]), m.get("from", {}).get("first_name", ""))
        if "photo" in m or "document" in m:
            print("<- [фото]")
            got_receipt(c, m["message_id"])
        elif "text" in m:
            print("<-", m["text"][:80])
            on_text(c, m["text"])


# ===================== HTTP-СЕРВЕР ДЛЯ RENDER =====================
class _Health(BaseHTTPRequestHandler):
    def _ok(self, body=True):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        if body:
            self.wfile.write(b"ok")

    def do_GET(self):
        self._ok()

    def do_HEAD(self):          # UptimeRobot шлёт HEAD
        self._ok(False)

    def log_message(self, *a):  # не засорять логи
        pass


def start_health_server():
    """Render (Web Service) требует открытый порт из переменной PORT."""
    port = int(os.environ.get("PORT", "10000"))
    srv = HTTPServer(("0.0.0.0", port), _Health)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print("HTTP-сервер для Render слушает порт %d" % port)


def main():
    global BOT_USERNAME
    if TOKEN.startswith("ВСТАВЬТЕ"):
        print("Впишите токен бота в TOKEN (или переменную BOT_TOKEN).")
        sys.exit(1)
    start_health_server()
    load_db()
    me = api("getMe")
    if ok(me):
        BOT_USERNAME = me["result"].get("username", "")
    else:
        print("Не удалось связаться с Telegram:", err(me))
    api("setMyCommands", commands=[{"command": "start", "description": "Меню / Menyu"},
                                   {"command": "menu", "description": "Меню / Menyu"}])
    if PHOTO and not os.path.exists(PHOTO):
        print("Внимание: файл %s не найден - бот будет присылать обычный текст" % PHOTO)
    print("Бот @%s запущен. Остановить: Ctrl+C" % BOT_USERNAME)
    offset = 0
    while True:
        r = api("getUpdates", timeout=40, offset=offset, **{"allowed_updates": ["message", "callback_query"]})
        if not ok(r):
            print("Нет связи с Telegram:", err(r))
            time.sleep(3)
            continue
        for upd in r["result"]:
            offset = upd["update_id"] + 1
            try:
                handle_update(upd)
            except Exception:
                traceback.print_exc()      # одна ошибка не останавливает бота


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nОстановлено")
