import json
import os


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

GROUPS_FILE = os.path.join(
    BASE_DIR,
    "data",
    "groups.json"
)


# ============================================================
# DATA FILE
# ============================================================

def ensure_data_file():
    os.makedirs(
        os.path.dirname(GROUPS_FILE),
        exist_ok=True
    )

    if not os.path.exists(GROUPS_FILE):
        with open(
            GROUPS_FILE,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                [],
                file,
                ensure_ascii=False,
                indent=2
            )


# ============================================================
# LOAD / SAVE
# ============================================================

def load_groups():
    ensure_data_file()

    try:
        with open(
            GROUPS_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

            if not isinstance(data, list):
                return []

            return data

    except (
        json.JSONDecodeError,
        OSError
    ):
        return []


def save_groups(groups):
    ensure_data_file()

    with open(
        GROUPS_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            groups,
            file,
            ensure_ascii=False,
            indent=2
        )


# ============================================================
# ADD GROUP
# ============================================================

def add_group(chat_id, title):
    groups = load_groups()

    for group in groups:
        if group.get("chat_id") == chat_id:

            # اگر گروه قبلاً وجود داشته باشد
            # فقط نام آن را بروزرسانی می‌کنیم.
            group["title"] = title

            save_groups(groups)

            return False

    groups.append({
        "chat_id": chat_id,
        "title": title,
        "enabled": True
    })

    save_groups(groups)

    return True


# ============================================================
# REMOVE GROUP
# ============================================================

def remove_group(chat_id):
    groups = load_groups()

    new_groups = [
        group
        for group in groups
        if group.get("chat_id") != chat_id
    ]

    if len(new_groups) == len(groups):
        return False

    save_groups(new_groups)

    return True


# ============================================================
# GET GROUP
# ============================================================

def get_group(chat_id):
    groups = load_groups()

    for group in groups:
        if group.get("chat_id") == chat_id:
            return group

    return None


# ============================================================
# UPDATE GROUP TITLE
# ============================================================

def update_group_title(chat_id, title):
    groups = load_groups()

    for group in groups:
        if group.get("chat_id") == chat_id:

            group["title"] = title

            save_groups(groups)

            return True

    return False


# ============================================================
# ENABLE GROUP
# ============================================================

def enable_group(chat_id):
    groups = load_groups()

    for group in groups:
        if group.get("chat_id") == chat_id:

            group["enabled"] = True

            save_groups(groups)

            return True

    return False


# ============================================================
# DISABLE GROUP
# ============================================================

def disable_group(chat_id):
    groups = load_groups()

    for group in groups:
        if group.get("chat_id") == chat_id:

            group["enabled"] = False

            save_groups(groups)

            return True

    return False


# ============================================================
# TOGGLE GROUP
# ============================================================

def toggle_group(chat_id):
    groups = load_groups()

    for group in groups:
        if group.get("chat_id") == chat_id:

            current_status = group.get(
                "enabled",
                True
            )

            group["enabled"] = not current_status

            save_groups(groups)

            return group["enabled"]

    return None


# ============================================================
# ACTIVE GROUPS
# ============================================================

def get_active_groups():
    groups = load_groups()

    return [
        group
        for group in groups
        if group.get("enabled", True)
    ]


# ============================================================
# DISABLED GROUPS
# ============================================================

def get_disabled_groups():
    groups = load_groups()

    return [
        group
        for group in groups
        if not group.get("enabled", True)
    ]


# ============================================================
# GROUP COUNT
# ============================================================

def get_group_count():
    groups = load_groups()

    return len(groups)


def get_active_group_count():
    groups = get_active_groups()

    return len(groups)


def get_disabled_group_count():
    groups = get_disabled_groups()

    return len(groups)


# ============================================================
# GROUP STATUS
# ============================================================

def is_group_enabled(chat_id):
    group = get_group(chat_id)

    if group is None:
        return False

    return group.get(
        "enabled",
        True
    )


# ============================================================
# SET GROUP STATUS
# ============================================================

def set_group_status(chat_id, enabled):
    groups = load_groups()

    for group in groups:
        if group.get("chat_id") == chat_id:

            group["enabled"] = bool(enabled)

            save_groups(groups)

            return True

    return False
