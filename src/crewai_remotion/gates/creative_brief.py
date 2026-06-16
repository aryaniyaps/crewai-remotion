from crewai_remotion.models.development import CreativeBrief


def gate_creative_brief(brief: CreativeBrief | None) -> tuple[bool, str]:
    if not brief:
        return False, "Missing creative brief"
    if not brief.objective or not brief.audience or not brief.key_message:
        return False, "Creative brief incomplete"
    return True, "Creative brief approved"
