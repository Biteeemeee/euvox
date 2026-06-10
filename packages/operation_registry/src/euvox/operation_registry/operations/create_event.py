from euvox.operation_registry.base import RenderContext, RenderResult


def _safe_id(event_id: str) -> str:
    return event_id.replace(".", "_").replace(" ", "_")


def _namespace(event_id: str) -> str:
    parts = event_id.split(".")
    return parts[0] if parts else "euvox"


def _render_event_script(spec: dict[str, object]) -> str:
    event_id = str(spec["event_id"])
    ns = _namespace(event_id)
    picture = str(spec.get("picture", "GFX_evt_default"))
    is_triggered_only = bool(spec.get("is_triggered_only", True))
    fire_only_once = bool(spec.get("fire_only_once", True))
    trigger_conditions: list[str] = list(spec.get("trigger_conditions", []))  # type: ignore[arg-type]
    top_effects: list[str] = list(spec.get("effects", []))  # type: ignore[arg-type]
    options: list[dict] = list(spec.get("options", []))  # type: ignore[arg-type]

    if not options:
        options = [{"name": f"{event_id}.a", "tooltip": "Accept.", "effects": top_effects}]
        top_effects = []

    lines: list[str] = [f"namespace = {ns}", ""]
    lines.append(f"# {spec.get('title', event_id)}")
    lines.append("country_event = {")
    lines.append(f"\tid = {event_id}")
    lines.append(f'\ttitle = "{event_id}.t"')
    lines.append(f'\tdesc = "{event_id}.d"')
    lines.append(f"\tpicture = {picture}")

    if is_triggered_only:
        lines.append("\tis_triggered_only = yes")
    if fire_only_once:
        lines.append("\tfire_only_once = yes")

    if trigger_conditions:
        lines.append("")
        lines.append("\ttrigger = {")
        for cond in trigger_conditions:
            lines.append(f"\t\t{cond}")
        lines.append("\t}")

    if top_effects:
        lines.append("")
        lines.append("\timmediate = {")
        for eff in top_effects:
            lines.append(f"\t\t{eff}")
        lines.append("\t}")

    for opt in options:
        lines.append("")
        lines.append("\toption = {")
        lines.append(f'\t\tname = "{opt["name"]}"')
        for eff in opt.get("effects", []):
            lines.append(f"\t\t{eff}")
        lines.append("\t}")

    lines.append("}")
    return "\n".join(lines)


def _render_localization(spec: dict[str, object]) -> str:
    event_id = str(spec["event_id"])
    title = str(spec.get("title", event_id))
    description = str(spec.get("description", ""))
    options: list[dict] = list(spec.get("options", []))  # type: ignore[arg-type]

    if not options:
        options = [{"name": f"{event_id}.a", "tooltip": "Accept."}]

    lines: list[str] = ["l_english:"]
    lines.append(f' {event_id}.t:0 "{title}"')
    lines.append(f' {event_id}.d:0 "{description}"')
    for opt in options:
        tooltip = str(opt.get("tooltip", "Accept."))
        lines.append(f' {opt["name"]}:0 "{tooltip}"')

    return "\n".join(lines)


class CreateEventV1:
    type_name = "create_event"
    schema_version = "v1"

    def validate(self, spec: dict[str, object]) -> list[str]:
        errors: list[str] = []
        if not spec.get("event_id"):
            errors.append("missing required field: event_id")
        if not spec.get("title"):
            errors.append("missing required field: title")
        for fname in ("trigger_conditions", "effects", "options"):
            val = spec.get(fname, [])
            if not isinstance(val, list):
                errors.append(f"{fname} must be a list")
        options = spec.get("options", [])
        if isinstance(options, list):
            for i, opt in enumerate(options):
                if not isinstance(opt, dict) or not opt.get("name"):
                    errors.append(f"option[{i}] missing required field: name")
        return errors

    def render(self, spec: dict[str, object], context: RenderContext) -> RenderResult:
        event_id = str(spec["event_id"])
        safe = _safe_id(event_id)
        return RenderResult(
            files={
                f"events/euvox_{safe}.txt": _render_event_script(spec),
                f"localisation/english/euvox_{safe}_l_english.yml": _render_localization(spec),
            },
            description=f"create_event:{event_id}",
        )

    def complexity(self, spec: dict[str, object]) -> float:
        return 1.0 + 0.2 * len(list(spec.get("options", [])))  # type: ignore[arg-type]

    def describe(self, spec: dict[str, object]) -> str:
        return f"Create event {spec.get('event_id', 'unknown')} ('{spec.get('title', '')}')"
