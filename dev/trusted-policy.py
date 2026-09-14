"""Validate explicit source budgets; proposals never discharge a user ruling."""
import hashlib
import json

PATH = "dev/trusted-policy.json"


def unique_object(pairs):
    result = dict(pairs)
    if len(result) != len(pairs):
        raise ValueError("duplicate trusted-policy key")
    return result


def invalid_number(value):
    raise ValueError(f"invalid trusted-policy number: {value}")


def fields(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(f"{label}: expected exactly {', '.join(keys)}")


def evaluate(report, data):
    policy = json.loads(data, object_pairs_hook=unique_object, parse_constant=invalid_number)
    fields(policy, ("format", "status", "ruling", "groups"), "trusted policy")
    if type(policy["format"]) is not int or policy["format"] != 1:
        raise ValueError("trusted policy: unsupported format")
    if policy["status"] not in ("PROPOSED", "APPROVED"):
        raise ValueError("trusted policy: expected PROPOSED or APPROVED")
    approved = policy["status"] == "APPROVED"
    ruling = policy["ruling"]
    if approved:
        if not isinstance(ruling, str) or not ruling.strip():
            raise ValueError("approved trusted policy requires a user ruling reference")
    elif ruling is not None:
        raise ValueError("proposed trusted policy must leave its ruling null")
    groups = policy["groups"]
    if not isinstance(groups, list):
        raise ValueError("trusted policy groups must be a list")
    indexed = {}
    for group in groups:
        fields(group, ("name", "scope", "limit", "reason", "files"), "policy group")
        name = group["name"]
        if not isinstance(name, str) or name in indexed:
            raise ValueError("invalid or duplicate trusted-policy group")
        if group["scope"] not in ("included", "excluded"):
            raise ValueError(f"{name}: expected included or excluded scope")
        included = group["scope"] == "included"
        limit = group["limit"]
        if included and (type(limit) is not int or limit < 0):
            raise ValueError(f"{name}: included budget must be a nonnegative integer")
        if not included and limit is not None:
            raise ValueError(f"{name}: excluded budget must be null")
        reason = group["reason"]
        if not isinstance(reason, str) or (not included and not reason.strip()):
            raise ValueError(f"{name}: excluded scope requires a reason")
        names = group["files"]
        if (not isinstance(names, list) or any(not isinstance(path, str) for path in names)
                or names != sorted(set(names))):
            raise ValueError(f"{name}: files must be sorted unique path strings")
        # A dropped kernel and a relaxed kernel budget are different faults.
        # The inventory prints this text, so each one names its own cause.
        if name == "kernel" and not included:
            raise ValueError("kernel: the established trusted base cannot be excluded")
        if name == "kernel" and limit > 4000:
            raise ValueError("kernel: the ratified 4000-line limit cannot be relaxed")
        if name in ("erase", "rir", "printer", "signatures") and not included:
            raise ValueError(f"{name}: the established trusted base cannot be excluded")
        indexed[name] = group
    if set(indexed) != {group["name"] for group in report["groups"]}:
        raise ValueError("trusted policy must name every inventory group exactly once")
    checks = []
    for measured in report["groups"]:
        group = indexed[measured["name"]]
        included = group["scope"] == "included"
        paths_match = group["files"] == measured["files"]
        within_limit = not included or measured["lines"] <= group["limit"]
        checks.append({"name": group["name"], "scope": group["scope"],
                       "lines": measured["lines"], "limit": group["limit"],
                       "reason": group["reason"], "paths_match": paths_match,
                       "within_limit": within_limit, "passed": paths_match and within_limit})
    included = [check for check in checks if check["scope"] == "included"]
    return {"path": PATH, "sha256": hashlib.sha256(data).hexdigest(),
            "status": policy["status"], "ruling": ruling,
            "lines": sum(check["lines"] for check in included),
            "limit": sum(check["limit"] for check in included),
            "passed": all(check["passed"] for check in checks), "checks": checks}


def apply(report, data):
    policy = evaluate(report, data)
    report["policy"] = policy
    if policy["status"] == "APPROVED":
        report["status"] = "PASS" if report["kernel"]["passed"] and policy["passed"] else "FAIL"
        limits = {check["name"]: check["limit"] or 0 for check in policy["checks"]}
        base = limits["kernel"] + limits["erase"]
        other = policy["limit"] - base - limits["rir"] - limits["printer"] - limits["signatures"]
        report["ceiling"] = {"base": base, "formula": f"{base} + A_rir + A_emit + A_sig + A_other",
                             "total": policy["limit"], "A_rir": limits["rir"],
                             "A_emit": limits["printer"], "A_sig": limits["signatures"],
                             "A_other": other}
        scopes = {check["name"]: check["scope"] for check in policy["checks"]}
        for group in report["groups"]:
            group["scope"] = scopes[group["name"]]
        report["pending_rulings"] = []
    return report
