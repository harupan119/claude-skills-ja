#!/usr/bin/env python3
"""日付・曜日・空き時間の計算を、モデルの暗算ではなくコードでやるための補助。

    python3 calendar_calc.py weekday 2026-07-28 2026-07-29
    python3 calendar_calc.py year 7/28 火 --from 2024 --to 2030
    python3 calendar_calc.py free busy.json

free の入力（JSON）:
    {
      "timezone": "+09:00",                          # 出力に使うUTCオフセット
      "range": {"start": "2026-10-01", "end": "2026-10-07"},  # 両端を含む
      "day_hours": ["09:00", "22:00"],               # 1日のうち候補にしてよい時間帯
      "buffer_before_minutes": 60,                   # 各予定の開始前に空ける時間
      "min_slot_minutes": 60,                        # これより短い空きは出さない
      "all_day": "ignore",                           # 終日予定: "ignore"(注記のみ) / "block"
      "events": [ ...list_events の items をそのまま並べてよい... ]
    }

events の各要素は Google Calendar の Event 形式
（start.dateTime / start.date、終日予定の end.date は翌日＝排他的）か、
{"start": "2026-10-01T16:00:00+09:00", "end": "...", "summary": "..."} の簡易形式。
"""
import argparse
import datetime as dt
import json
import re
import sys

WEEKDAYS = "月火水木金土日"


def fmt_date(d):
    return f"{d.isoformat()}（{WEEKDAYS[d.weekday()]}）"


def parse_offset(text):
    m = re.fullmatch(r"([+-])(\d{2}):?(\d{2})", text or "+09:00")
    if not m:
        raise ValueError(f"timezone は +09:00 の形式で指定する: {text!r}")
    sign = 1 if m.group(1) == "+" else -1
    return dt.timezone(sign * dt.timedelta(hours=int(m.group(2)), minutes=int(m.group(3))))


def parse_hhmm(text):
    h, m = text.split(":")
    return dt.time(int(h), int(m))


def _point(value):
    """(kind, value) を返す。kind は 'datetime' か 'date'。"""
    if isinstance(value, dict):
        if "dateTime" in value:
            value = value["dateTime"]
        elif "date" in value:
            return "date", dt.date.fromisoformat(value["date"])
        else:
            raise ValueError(f"start/end に dateTime も date も無い: {value!r}")
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return "date", dt.date.fromisoformat(value)
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"UTCオフセットの無い日時は曖昧なので受け付けない: {value!r}")
    return "datetime", parsed


def load_events(events, tz):
    timed, all_day = [], []
    for ev in events:
        if ev.get("status") == "cancelled":
            continue
        sk, sv = _point(ev["start"])
        ek, ev_end = _point(ev["end"])
        title = ev.get("summary", "(無題)")
        if sk == "date":
            # Google Calendar の終日予定は end.date が排他的（翌日）
            all_day.append((sv, ev_end, title))
        else:
            if ek != "datetime":
                raise ValueError(f"開始と終了の形式が混在している: {title}")
            timed.append((sv.astimezone(tz), ev_end.astimezone(tz), title))
    return timed, all_day


def free_slots(cfg):
    tz = parse_offset(cfg.get("timezone", "+09:00"))
    first = dt.date.fromisoformat(cfg["range"]["start"])
    last = dt.date.fromisoformat(cfg["range"]["end"])
    if last < first:
        raise ValueError("range.end が range.start より前")
    day_start, day_end = (parse_hhmm(x) for x in cfg.get("day_hours", ["09:00", "22:00"]))
    buffer = dt.timedelta(minutes=cfg.get("buffer_before_minutes", 60))
    min_slot = dt.timedelta(minutes=cfg.get("min_slot_minutes", 60))
    all_day_mode = cfg.get("all_day", "ignore")
    if all_day_mode not in {"ignore", "block"}:
        raise ValueError("all_day は ignore か block")

    timed, all_day = load_events(cfg.get("events", []), tz)
    busy = [(s - buffer, e, t) for s, e, t in timed]

    out = []
    day = first
    while day <= last:
        lo = dt.datetime.combine(day, day_start, tz)
        hi = dt.datetime.combine(day, day_end, tz)
        notes = [t for s, e, t in all_day if s <= day < e]
        if notes and all_day_mode == "block":
            out.append((day, [], notes))
            day += dt.timedelta(days=1)
            continue
        cuts = sorted((max(s, lo), min(e, hi)) for s, e, _ in busy if s < hi and e > lo)
        slots, cursor = [], lo
        for s, e in cuts:
            if s - cursor >= min_slot:
                slots.append((cursor, s))
            cursor = max(cursor, e)
        if hi - cursor >= min_slot:
            slots.append((cursor, hi))
        out.append((day, slots, notes))
        day += dt.timedelta(days=1)
    return out


def cmd_weekday(args):
    for text in args.dates:
        print(fmt_date(dt.date.fromisoformat(text)))


def cmd_year(args):
    m = re.fullmatch(r"(\d{1,2})[/-](\d{1,2})", args.month_day)
    if not m or args.weekday not in WEEKDAYS:
        sys.exit("usage: year 7/28 火 [--from Y] [--to Y]")
    month, day = int(m.group(1)), int(m.group(2))
    hits = []
    for year in range(args.year_from, args.year_to + 1):
        try:
            d = dt.date(year, month, day)
        except ValueError:
            continue
        if WEEKDAYS[d.weekday()] == args.weekday:
            hits.append(d)
    for d in hits:
        print(fmt_date(d))
    if not hits:
        print("該当なし", file=sys.stderr)
        sys.exit(1)


def cmd_free(args):
    with open(args.json, encoding="utf-8") as f:
        cfg = json.load(f)
    for day, slots, notes in free_slots(cfg):
        head = f"{day.month}/{day.day}（{WEEKDAYS[day.weekday()]}）"
        note = f"  ※終日: {', '.join(notes)}" if notes else ""
        if not slots:
            print(f"{head} 空きなし{note}")
            continue
        spans = []
        for s, e in slots:
            mins = int((e - s).total_seconds() // 60)
            spans.append(f"{s:%H:%M}〜{e:%H:%M}（{mins // 60}h{mins % 60:02d}m）")
        print(f"{head} " + " / ".join(spans) + note)


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("weekday", help="日付の曜日を出す")
    w.add_argument("dates", nargs="+")
    w.set_defaults(func=cmd_weekday)
    y = sub.add_parser("year", help="月日と曜日が一致する年を出す")
    y.add_argument("month_day")
    y.add_argument("weekday")
    this_year = dt.date.today().year
    y.add_argument("--from", dest="year_from", type=int, default=this_year - 2)
    y.add_argument("--to", dest="year_to", type=int, default=this_year + 2)
    y.set_defaults(func=cmd_year)
    f = sub.add_parser("free", help="空き時間を出す")
    f.add_argument("json")
    f.set_defaults(func=cmd_free)
    args = p.parse_args()
    try:
        args.func(args)
    except (ValueError, KeyError) as e:
        sys.exit(f"入力エラー: {e}")


if __name__ == "__main__":
    main()
