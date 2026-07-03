"""Core analytics functions converted from the GroupDNA notebooks."""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from statistics import mean, median


STOP_WORDS = {
    "a", "an", "the", "is", "are", "am", "was", "were", "be", "been", "being",
    "to", "of", "in", "on", "at", "by", "for", "from", "with", "about", "into",
    "after", "before", "and", "or", "but", "this", "that", "these", "those",
    "it", "its", "it's", "i", "me", "my", "mine", "you", "your", "yours", "he",
    "him", "his", "she", "her", "hers", "they", "them", "their", "we", "our",
    "ours", "as", "if", "then", "than", "not", "no", "yes", "can", "could",
    "will", "would", "shall", "should", "do", "does", "did", "have", "has", "had",
    "media", "omitted", "message", "deleted", "file", "attached", "image", "video",
    "document", "sticker", "edited",
}

CARING_KEYWORDS = {"take", "care", "eat", "food", "sleep", "safe", "medicine", "help", "please"}
DRAMA_KEYWORDS = {"omg", "seriously", "really", "never", "always", "hate", "love", "drama", "why"}
COMEDIAN_KEYWORDS = {"lol", "lmao", "haha", "hehe", "meme", "joke", "funny", "rofl"}
QUESTION_KEYWORDS = {"who", "what", "when", "where", "why", "how", "which", "ki", "kobe", "keno"}
COMEDIAN_EMOJIS = {"😂", "🤣", "😆", "😹", "😄", "😁"}
EMOJI_PATTERN = re.compile(
    "[\U0001F1E0-\U0001FAFF\U00002700-\U000027BF\U00002600-\U000026FF]",
    flags=re.UNICODE,
)


def clean_word(word: str, remove_stopwords: bool = True) -> str:
    word = word.lower()
    if "http" in word or "www" in word or "@" in word:
        return ""
    cleaned = "".join(character for character in word if character.isalpha() or character.isdigit())
    if not cleaned or len(cleaned) < 3 or cleaned.isdigit():
        return ""
    if remove_stopwords and cleaned in STOP_WORDS:
        return ""
    return cleaned


def message_words(text: str, remove_stopwords: bool = True) -> list[str]:
    return [word for word in (clean_word(part, remove_stopwords) for part in text.split()) if word]


def calculate_report(chat_data: list[dict], validation: dict | None = None) -> dict:
    if not chat_data:
        return empty_report(validation)

    chat_data = sorted(chat_data, key=lambda item: item["timestamp"])
    summary = calculate_summary(chat_data, validation or {})
    members = calculate_member_stats(chat_data)
    activity = calculate_activity(chat_data)
    words = calculate_word_statistics(chat_data)
    response = calculate_response_analysis(chat_data)
    personality = calculate_personality(chat_data, response)

    return {
        "chat_data": chat_data,
        "group_overview": {
            "summary": summary,
            "participant_count": {name: data["messages"] for name, data in members.items()},
            "most_active": max(members.items(), key=lambda item: item[1]["messages"]),
            "least_active": min(members.items(), key=lambda item: item[1]["messages"]),
            "leaderboard": sorted(
                [(name, data["messages"]) for name, data in members.items()],
                key=lambda item: item[1],
                reverse=True,
            ),
        },
        "members": members,
        "activity_summary": activity,
        "word_statistics": words,
        "response_analysis": response,
        "personality_archetypes": personality["assignments"],
        "normalized_archetype_scores": personality["normalized_scores"],
        "validation": validation or {},
    }


def empty_report(validation: dict | None = None) -> dict:
    return {
        "chat_data": [],
        "group_overview": {"summary": {}, "participant_count": {}, "leaderboard": []},
        "members": {},
        "activity_summary": {},
        "word_statistics": {"total_valid_words": 0, "unique_words": 0, "word_frequency": {}, "top_words": []},
        "response_analysis": {"average_response_time": {}, "silent_streaks": {}},
        "personality_archetypes": {},
        "normalized_archetype_scores": {},
        "validation": validation or {},
    }


def calculate_summary(chat_data: list[dict], validation: dict) -> dict:
    timestamps = [message["timestamp"] for message in chat_data]
    lengths = [len(message["text"]) for message in chat_data]
    first = min(timestamps)
    last = max(timestamps)
    duration_days = max((last.date() - first.date()).days + 1, 1)
    participants = {message["sender"] for message in chat_data}
    by_day = Counter(message["timestamp"].date() for message in chat_data)
    by_hour = Counter(message["timestamp"].hour for message in chat_data)

    return {
        "total_messages": len(chat_data),
        "total_participants": len(participants),
        "start_date": first,
        "end_date": last,
        "duration_days": duration_days,
        "average_messages_per_day": round(len(chat_data) / duration_days, 2),
        "media_messages": sum(1 for message in chat_data if message.get("is_media")),
        "deleted_messages": sum(1 for message in chat_data if message.get("is_deleted")),
        "system_messages": validation.get("system_messages", 0),
        "longest_message": max(lengths),
        "shortest_message": min(lengths),
        "average_message_length": round(mean(lengths), 2),
        "most_active_day": by_day.most_common(1)[0],
        "most_active_hour": by_hour.most_common(1)[0],
        "first_message": chat_data[0],
        "last_message": chat_data[-1],
    }


def calculate_member_stats(chat_data: list[dict]) -> dict:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for message in chat_data:
        grouped[message["sender"]].append(message)

    all_response = calculate_response_analysis(chat_data)
    normalized = calculate_personality(chat_data, all_response)["normalized_scores"]
    assignments = assign_from_normalized(normalized)

    stats = {}
    for member, messages in grouped.items():
        texts = [message["text"] for message in messages]
        words = [word for text in texts for word in message_words(text)]
        timestamps = [message["timestamp"] for message in messages]
        total = len(messages)
        question_count = sum(1 for message in messages if message.get("is_question"))
        caps_count = sum(1 for message in messages if message.get("is_caps"))
        night_count = sum(1 for message in messages if message.get("is_night"))
        weekend_count = sum(1 for message in messages if message.get("is_weekend"))
        silent = all_response["silent_streaks"].get(member, {"days": 0})
        average_response = all_response["average_response_time"].get(member)
        member_scores = {name: scores.get(member, 0) for name, scores in normalized.items()}
        sorted_scores = sorted(member_scores.items(), key=lambda item: item[1], reverse=True)

        stats[member] = {
            "messages": total,
            "words": len(words),
            "media": sum(1 for message in messages if message.get("is_media")),
            "deleted": sum(1 for message in messages if message.get("is_deleted")),
            "average_length": round(mean([len(text) for text in texts]), 2) if texts else 0,
            "activity_hours": dict(Counter(message["timestamp"].hour for message in messages)),
            "activity_days": dict(Counter(message["timestamp"].strftime("%A") for message in messages)),
            "favorite_words": Counter(words).most_common(20),
            "emojis": Counter(emoji for text in texts for emoji in EMOJI_PATTERN.findall(text)).most_common(20),
            "longest_silent_streak": silent,
            "average_response_time": average_response,
            "burst_score": round(calculate_burst_score(timestamps), 3),
            "ghost_score": round(silent.get("days", 0) / max(total, 1), 3),
            "question_ratio": round(question_count / total, 3),
            "caps_ratio": round(caps_count / total, 3),
            "night_activity": round(night_count / total, 3),
            "weekend_activity": round(weekend_count / total, 3),
            "monthly_trend": dict(Counter(message["timestamp"].strftime("%Y-%m") for message in messages)),
            "yearly_trend": dict(Counter(message["timestamp"].year for message in messages)),
            "personality_scores": member_scores,
            "archetype": assignments.get(member, {}).get("Archetype", "Unassigned"),
            "archetype_score": assignments.get(member, {}).get("Score", 0),
            "runner_up_archetype": sorted_scores[1][0] if len(sorted_scores) > 1 else None,
            "runner_up_score": sorted_scores[1][1] if len(sorted_scores) > 1 else None,
            "timeline": messages[-250:],
        }
    return stats


def calculate_activity(chat_data: list[dict]) -> dict:
    daily = Counter(message["timestamp"].date() for message in chat_data)
    hourly = Counter(message["timestamp"].hour for message in chat_data)
    weekly = Counter(message["timestamp"].strftime("%Y-W%U") for message in chat_data)
    monthly = Counter(message["timestamp"].strftime("%Y-%m") for message in chat_data)
    yearly = Counter(message["timestamp"].year for message in chat_data)
    weekday_hour = {day: {hour: 0 for hour in range(24)} for day in weekday_names()}
    member_hour: dict[str, dict[int, int]] = defaultdict(lambda: {hour: 0 for hour in range(24)})
    member_day: dict[str, dict[str, int]] = defaultdict(lambda: {day: 0 for day in weekday_names()})

    for message in chat_data:
        weekday = message["timestamp"].strftime("%A")
        hour = message["timestamp"].hour
        weekday_hour[weekday][hour] += 1
        member_hour[message["sender"]][hour] += 1
        member_day[message["sender"]][weekday] += 1

    busiest_day = daily.most_common(1)[0]
    busiest_hour = hourly.most_common(1)[0]
    return {
        "daily_activity": dict(sorted(daily.items())),
        "hourly_activity": {hour: hourly.get(hour, 0) for hour in range(24)},
        "weekly_activity": dict(sorted(weekly.items())),
        "monthly_activity": dict(sorted(monthly.items())),
        "yearly_activity": dict(sorted(yearly.items())),
        "activity_heatmap": weekday_hour,
        "member_hour_heatmap": dict(member_hour),
        "member_day_heatmap": dict(member_day),
        "busiest_day": {"date": busiest_day[0], "messages": busiest_day[1]},
        "busiest_hour": {
            "hour": busiest_hour[0],
            "total_messages": busiest_hour[1],
            "average_messages": busiest_hour[1] / max(len(daily), 1),
        },
        "weekend_vs_weekday": {
            "Weekend": sum(1 for message in chat_data if message["timestamp"].weekday() >= 5),
            "Weekday": sum(1 for message in chat_data if message["timestamp"].weekday() < 5),
        },
    }


def calculate_word_statistics(chat_data: list[dict]) -> dict:
    by_member: dict[str, Counter] = defaultdict(Counter)
    phrase_counter: Counter = Counter()
    word_trends: dict[str, Counter] = defaultdict(Counter)
    all_words: list[str] = []

    for message in chat_data:
        words = message_words(message["text"])
        all_words.extend(words)
        by_member[message["sender"]].update(words)
        month = message["timestamp"].strftime("%Y-%m")
        word_trends[month].update(words)
        for index in range(len(words) - 1):
            phrase_counter[" ".join(words[index:index + 2])] += 1
        for index in range(len(words) - 2):
            phrase_counter[" ".join(words[index:index + 3])] += 1

    freq = Counter(all_words)
    return {
        "total_valid_words": len(all_words),
        "unique_words": len(freq),
        "word_frequency": dict(freq),
        "top_words": freq.most_common(100),
        "top_words_per_member": {member: counter.most_common(25) for member, counter in by_member.items()},
        "vocabulary_richness": round(len(freq) / max(len(all_words), 1), 4),
        "common_phrases": phrase_counter.most_common(50),
        "longest_words": sorted(freq, key=lambda word: (len(word), freq[word]), reverse=True)[:25],
        "shortest_words": sorted([word for word in freq if len(word) >= 3], key=lambda word: (len(word), -freq[word]))[:25],
        "message_length_distribution": [len(message["text"]) for message in chat_data],
        "word_trends": {month: counter.most_common(15) for month, counter in word_trends.items()},
        "language_distribution": best_effort_language_distribution(all_words),
    }


def calculate_response_analysis(chat_data: list[dict]) -> dict:
    response_times: dict[str, list[float]] = defaultdict(list)
    starters: Counter = Counter()
    enders: Counter = Counter()
    bursts: list[dict] = []
    previous = None
    current_burst = []

    for message in sorted(chat_data, key=lambda item: item["timestamp"]):
        if previous is None:
            starters[message["sender"]] += 1
            current_burst = [message]
            previous = message
            continue

        delta = (message["timestamp"] - previous["timestamp"]).total_seconds() / 60
        if message["sender"] != previous["sender"] and 0 <= delta <= 24 * 60:
            response_times[message["sender"]].append(delta)

        if delta <= 30:
            current_burst.append(message)
        else:
            if len(current_burst) >= 3:
                bursts.append(describe_burst(current_burst))
            enders[previous["sender"]] += 1
            starters[message["sender"]] += 1
            current_burst = [message]
        previous = message

    if previous is not None:
        enders[previous["sender"]] += 1
    if len(current_burst) >= 3:
        bursts.append(describe_burst(current_burst))

    silent_streaks = calculate_silent_streaks(chat_data)
    averages = {member: mean(values) for member, values in response_times.items() if values}
    return {
        "average_response_time": averages,
        "median_response_time": {member: median(values) for member, values in response_times.items() if values},
        "fastest_responder": min(averages.items(), key=lambda item: item[1]) if averages else None,
        "slowest_responder": max(averages.items(), key=lambda item: item[1]) if averages else None,
        "reply_chains": bursts[:100],
        "conversation_bursts": sorted(bursts, key=lambda item: item["messages"], reverse=True)[:100],
        "silent_streaks": silent_streaks,
        "ghost_score": {member: details["days"] for member, details in silent_streaks.items()},
        "conversation_starters": starters.most_common(),
        "conversation_enders": enders.most_common(),
    }


def calculate_personality(chat_data: list[dict], response_analysis: dict) -> dict:
    members = sorted({message["sender"] for message in chat_data})
    grouped: dict[str, list[dict]] = defaultdict(list)
    for message in chat_data:
        grouped[message["sender"]].append(message)

    raw = {name: {} for name in archetype_names()}
    total_messages = len(chat_data)
    global_average = total_messages / max(len(members), 1)

    for member in members:
        messages = grouped[member]
        count = len(messages)
        texts = [message["text"] for message in messages]
        words = [word for text in texts for word in message_words(text)]
        raw["THE SPAMMER"][member] = count / max(global_average, 1)
        raw["THE GROUP MOM"][member] = keyword_ratio(words, CARING_KEYWORDS)
        raw["THE NIGHT OWL"][member] = sum(1 for message in messages if message["timestamp"].hour <= 4) / max(count, 1)
        raw["THE STORYTELLER"][member] = len(words) / max(count, 1)
        raw["THE DRAMA QUEEN"][member] = (
            sum(text.count("!") + text.count("?") for text in texts) / max(count, 1)
            + keyword_ratio(words, DRAMA_KEYWORDS)
        )
        silent = response_analysis.get("silent_streaks", {}).get(member, {}).get("days", 0)
        raw["THE GHOST"][member] = silent / max(count, 1)
        raw["THE COMEDIAN"][member] = (
            keyword_ratio(words, COMEDIAN_KEYWORDS)
            + sum(1 for text in texts if any(emoji in text for emoji in COMEDIAN_EMOJIS)) / max(count, 1)
        )
        raw["THE QUESTION MASTER"][member] = sum(1 for message in messages if message.get("is_question")) / max(count, 1)

    normalized = normalize_score_map(raw)
    assignments = assign_from_normalized(normalized)
    return {"normalized_scores": normalized, "assignments": assignments}


def calculate_silent_streaks(chat_data: list[dict]) -> dict:
    grouped: dict[str, list[date]] = defaultdict(list)
    for message in chat_data:
        grouped[message["sender"]].append(message["timestamp"].date())

    result = {}
    for member, dates in grouped.items():
        unique_dates = sorted(set(dates))
        if len(unique_dates) < 2:
            result[member] = {"days": 0, "start_date": unique_dates[0] if unique_dates else None, "end_date": unique_dates[0] if unique_dates else None}
            continue
        best_gap = 0
        best_start = unique_dates[0]
        best_end = unique_dates[0]
        for previous, current in zip(unique_dates, unique_dates[1:]):
            gap = (current - previous).days - 1
            if gap > best_gap:
                best_gap = gap
                best_start = previous + timedelta(days=1)
                best_end = current - timedelta(days=1)
        result[member] = {"days": best_gap, "start_date": best_start, "end_date": best_end}
    return result


def describe_burst(messages: list[dict]) -> dict:
    return {
        "start": messages[0]["timestamp"],
        "end": messages[-1]["timestamp"],
        "messages": len(messages),
        "participants": len({message["sender"] for message in messages}),
        "lead": messages[0]["sender"],
    }


def calculate_burst_score(timestamps: list[datetime]) -> float:
    if len(timestamps) < 2:
        return 0.0
    timestamps = sorted(timestamps)
    quick = 0
    for previous, current in zip(timestamps, timestamps[1:]):
        if (current - previous).total_seconds() <= 10 * 60:
            quick += 1
    return quick / (len(timestamps) - 1)


def keyword_ratio(words: list[str], keywords: set[str]) -> float:
    if not words:
        return 0.0
    return sum(1 for word in words if word in keywords) / len(words)


def normalize_score_map(score_map: dict[str, dict[str, float]]) -> dict[str, dict[str, float]]:
    normalized = {}
    for archetype, scores in score_map.items():
        values = list(scores.values())
        low = min(values) if values else 0
        high = max(values) if values else 0
        normalized[archetype] = {}
        for member, score in scores.items():
            normalized[archetype][member] = 0 if high == low else (score - low) / (high - low)
    return normalized


def assign_from_normalized(normalized: dict[str, dict[str, float]]) -> dict[str, dict]:
    members = set()
    for scores in normalized.values():
        members.update(scores)
    assignments = {}
    for member in members:
        ranked = sorted(((name, scores.get(member, 0)) for name, scores in normalized.items()), key=lambda item: item[1], reverse=True)
        assignments[member] = {
            "Archetype": ranked[0][0] if ranked else "Unassigned",
            "Score": ranked[0][1] if ranked else 0,
            "RunnerUp": ranked[1][0] if len(ranked) > 1 else None,
            "RunnerUpScore": ranked[1][1] if len(ranked) > 1 else None,
            "Confidence": ranked[0][1] - ranked[1][1] if len(ranked) > 1 else ranked[0][1] if ranked else 0,
        }
    return assignments


def best_effort_language_distribution(words: list[str]) -> dict[str, int]:
    distribution = Counter()
    for word in words:
        if any("\u0980" <= char <= "\u09ff" for char in word):
            distribution["Bengali script"] += 1
        elif word.isascii():
            distribution["Latin script"] += 1
        else:
            distribution["Mixed/Other"] += 1
    return dict(distribution)


def weekday_names() -> list[str]:
    return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def archetype_names() -> list[str]:
    return [
        "THE SPAMMER",
        "THE GROUP MOM",
        "THE NIGHT OWL",
        "THE STORYTELLER",
        "THE DRAMA QUEEN",
        "THE GHOST",
        "THE COMEDIAN",
        "THE QUESTION MASTER",
    ]
