from __future__ import annotations

from dataclasses import dataclass
import xml.etree.ElementTree as ET


QTI_NS = {"qti": "http://www.imsglobal.org/xsd/imsqti_v2p2"}
SUPPORTED_STUDENT_ITEM_TYPES = {
    "MCQ",
    "MRQ",
    "TF",
    "FIB",
    "Match",
    "Order",
    "Numeric",
    "Essay",
}


@dataclass
class ParsedQTIItem:
    source_qti_identifier: str
    item_type: str
    prompt: str
    interaction_payload: dict
    media_refs: list[dict]
    student_response_schema: dict
    scoring_mode: str
    answer_key: dict | None
    raw_qti_xml: str


def _text_of(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return "".join(element.itertext()).strip()


def _item_prompt(item_body: ET.Element) -> str:
    prompt_el = item_body.find(".//qti:prompt", QTI_NS)
    prompt = _text_of(prompt_el)
    if prompt:
        return prompt
    prompt = _text_of(item_body)
    return prompt or "No prompt found"


def _extract_media_refs(item_body: ET.Element, media_lookup: dict[str, dict] | None) -> list[dict]:
    refs: list[dict] = []
    for img_el in item_body.findall(".//qti:img", QTI_NS):
        src = img_el.get("src") or ""
        filename = src[len("media/"):] if src.startswith("media/") else src
        resolved = dict(media_lookup.get(filename, {})) if media_lookup else {}
        refs.append(
            {
                "filename": filename,
                "src": src,
                **resolved,
            }
        )
    return refs


def _parse_true_false(root: ET.Element, item_body: ET.Element) -> ParsedQTIItem:
    choices = []
    correct_answers = []
    for val in root.findall(".//qti:correctResponse/qti:value", QTI_NS):
        if val.text:
            correct_answers.append(val.text)
    for choice_el in item_body.findall(".//qti:simpleChoice", QTI_NS):
        choices.append(
            {
                "id": choice_el.get("identifier") or "",
                "text": _text_of(choice_el),
            }
        )
    return ParsedQTIItem(
        source_qti_identifier=root.get("identifier", ""),
        item_type="TF",
        prompt=_item_prompt(item_body),
        interaction_payload={"choices": choices},
        media_refs=[],
        student_response_schema={"kind": "single_choice", "choice_ids": [c["id"] for c in choices]},
        scoring_mode="objective",
        answer_key={"correct": correct_answers},
        raw_qti_xml="",
    )


def _parse_choice_item(root: ET.Element, item_body: ET.Element) -> ParsedQTIItem:
    response_decl = root.find("qti:responseDeclaration", QTI_NS)
    item_type = "MRQ" if response_decl is not None and response_decl.get("cardinality") == "multiple" else "MCQ"
    correct_answers = []
    choices = []
    for val in root.findall(".//qti:correctResponse/qti:value", QTI_NS):
        if val.text:
            correct_answers.append(val.text)
    for choice_el in item_body.findall(".//qti:simpleChoice", QTI_NS):
        choices.append(
            {
                "id": choice_el.get("identifier") or "",
                "text": _text_of(choice_el),
            }
        )
    schema_kind = "multi_choice" if item_type == "MRQ" else "single_choice"
    return ParsedQTIItem(
        source_qti_identifier=root.get("identifier", ""),
        item_type=item_type,
        prompt=_item_prompt(item_body),
        interaction_payload={"choices": choices},
        media_refs=[],
        student_response_schema={"kind": schema_kind, "choice_ids": [c["id"] for c in choices]},
        scoring_mode="objective",
        answer_key={"correct": correct_answers},
        raw_qti_xml="",
    )


def _parse_fib_or_numeric(root: ET.Element, item_body: ET.Element) -> ParsedQTIItem:
    response_decls = root.findall(".//qti:responseDeclaration", QTI_NS)
    if len(response_decls) == 1 and response_decls[0].get("baseType") in {"float", "integer", "decimal"}:
        correct_values = [
            value.text
            for value in response_decls[0].findall(".//qti:value", QTI_NS)
            if value.text is not None
        ]
        interaction = root.find(".//qti:textEntryInteraction", QTI_NS)
        expected_length = 20
        if interaction is not None:
            try:
                expected_length = int(interaction.get("expectedLength", "20"))
            except ValueError:
                expected_length = 20
        return ParsedQTIItem(
            source_qti_identifier=root.get("identifier", ""),
            item_type="Numeric",
            prompt=_item_prompt(item_body),
            interaction_payload={"expected_length": expected_length},
            media_refs=[],
            student_response_schema={"kind": "numeric"},
            scoring_mode="objective",
            answer_key={"correct": correct_values[0] if correct_values else ""},
            raw_qti_xml="",
        )

    fib_answers = []
    blank_num = 1
    for decl in response_decls:
        response_id = decl.get("identifier", "")
        if not response_id.startswith("RESPONSE"):
            continue
        values = decl.findall(".//qti:value", QTI_NS)
        answers = [value.text for value in values if value.text]
        if answers:
            fib_answers.append({"blank_num": blank_num, "answers": answers})
            blank_num += 1

    prompt = _item_prompt(item_body)
    prompt_with_blanks = ""
    paragraph = item_body.find(".//qti:p", QTI_NS)
    if paragraph is not None:
        parts: list[str] = []
        if paragraph.text:
            parts.append(paragraph.text)
        blank_counter = 1
        for child in paragraph:
            if child.tag.endswith("textEntryInteraction"):
                parts.append(f"[BLANK {blank_counter}]")
                blank_counter += 1
            if child.tail:
                parts.append(child.tail)
        prompt_with_blanks = "".join(parts).strip()
    if prompt_with_blanks:
        prompt = prompt_with_blanks

    return ParsedQTIItem(
        source_qti_identifier=root.get("identifier", ""),
        item_type="FIB",
        prompt=prompt,
        interaction_payload={
            "prompt_with_blanks": prompt_with_blanks or prompt,
            "blank_count": len(fib_answers),
        },
        media_refs=[],
        student_response_schema={"kind": "fib", "blank_count": len(fib_answers)},
        scoring_mode="objective",
        answer_key={"fib_answers": fib_answers},
        raw_qti_xml="",
    )


def _parse_essay(root: ET.Element, item_body: ET.Element) -> ParsedQTIItem:
    interaction = root.find(".//qti:extendedTextInteraction", QTI_NS)
    expected_lines = 5
    if interaction is not None:
        try:
            expected_lines = int(interaction.get("expectedLines", "5"))
        except ValueError:
            expected_lines = 5
    return ParsedQTIItem(
        source_qti_identifier=root.get("identifier", ""),
        item_type="Essay",
        prompt=_item_prompt(item_body),
        interaction_payload={"expected_lines": expected_lines},
        media_refs=[],
        student_response_schema={"kind": "essay"},
        scoring_mode="manual",
        answer_key=None,
        raw_qti_xml="",
    )


def _parse_match(root: ET.Element, item_body: ET.Element) -> ParsedQTIItem:
    match_sets = root.findall(".//qti:simpleMatchSet", QTI_NS)
    sources: list[dict] = []
    targets: list[dict] = []
    answer_key: list[dict] = []
    if len(match_sets) >= 2:
        for choice in match_sets[0].findall(".//qti:simpleAssociableChoice", QTI_NS):
            sources.append({"id": choice.get("identifier", ""), "text": _text_of(choice)})
        for choice in match_sets[1].findall(".//qti:simpleAssociableChoice", QTI_NS):
            targets.append({"id": choice.get("identifier", ""), "text": _text_of(choice)})
        for value in root.findall(".//qti:correctResponse/qti:value", QTI_NS):
            if not value.text:
                continue
            parts = value.text.strip().split()
            if len(parts) >= 2:
                answer_key.append({"source_id": parts[0], "target_id": parts[1]})
    return ParsedQTIItem(
        source_qti_identifier=root.get("identifier", ""),
        item_type="Match",
        prompt=_item_prompt(item_body),
        interaction_payload={"sources": sources, "targets": targets},
        media_refs=[],
        student_response_schema={
            "kind": "match",
            "source_ids": [source["id"] for source in sources],
            "target_ids": [target["id"] for target in targets],
        },
        scoring_mode="objective",
        answer_key={"pairs": answer_key},
        raw_qti_xml="",
    )


def _parse_order(root: ET.Element, item_body: ET.Element) -> ParsedQTIItem:
    items = []
    correct_order = []
    for choice_el in item_body.findall(".//qti:simpleChoice", QTI_NS):
        items.append(
            {
                "id": choice_el.get("identifier") or "",
                "text": _text_of(choice_el),
            }
        )
    for value in root.findall(".//qti:correctResponse/qti:value", QTI_NS):
        if value.text:
            correct_order.append(value.text)
    return ParsedQTIItem(
        source_qti_identifier=root.get("identifier", ""),
        item_type="Order",
        prompt=_item_prompt(item_body),
        interaction_payload={"items": items},
        media_refs=[],
        student_response_schema={"kind": "order", "item_ids": [item["id"] for item in items]},
        scoring_mode="objective",
        answer_key={"correct_order": correct_order},
        raw_qti_xml="",
    )


def parse_qti_item(
    xml_string: str,
    media_lookup: dict[str, dict] | None = None,
) -> ParsedQTIItem:
    root = ET.fromstring(xml_string)
    item_body = root.find("qti:itemBody", QTI_NS)
    if item_body is None:
        raise ValueError("QTI item has no itemBody.")

    response_decl = root.find("qti:responseDeclaration", QTI_NS)
    if response_decl is not None and response_decl.get("baseType") == "boolean":
        parsed = _parse_true_false(root, item_body)
    elif root.find(".//qti:choiceInteraction", QTI_NS) is not None:
        parsed = _parse_choice_item(root, item_body)
    elif root.find(".//qti:textEntryInteraction", QTI_NS) is not None:
        parsed = _parse_fib_or_numeric(root, item_body)
    elif root.find(".//qti:extendedTextInteraction", QTI_NS) is not None:
        parsed = _parse_essay(root, item_body)
    elif root.find(".//qti:matchInteraction", QTI_NS) is not None:
        parsed = _parse_match(root, item_body)
    elif root.find(".//qti:orderInteraction", QTI_NS) is not None:
        parsed = _parse_order(root, item_body)
    else:
        parsed = ParsedQTIItem(
            source_qti_identifier=root.get("identifier", ""),
            item_type="Unsupported",
            prompt=_item_prompt(item_body),
            interaction_payload={},
            media_refs=[],
            student_response_schema={"kind": "unsupported"},
            scoring_mode="unsupported",
            answer_key=None,
            raw_qti_xml="",
        )

    parsed.media_refs = _extract_media_refs(item_body, media_lookup)
    parsed.raw_qti_xml = xml_string
    return parsed


def is_student_supported_item(item_type: str) -> bool:
    return item_type in SUPPORTED_STUDENT_ITEM_TYPES


def parse_qti_question_for_review(xml_string: str) -> dict | None:
    try:
        parsed = parse_qti_item(xml_string)
    except ET.ParseError:
        return None
    except ValueError:
        return None

    question = {
        "type": parsed.item_type,
        "prompt": parsed.prompt,
        "choices": list(parsed.interaction_payload.get("choices", [])),
        "correct": list((parsed.answer_key or {}).get("correct", [])),
        "img_src": parsed.media_refs[0]["filename"] if parsed.media_refs else None,
        "order_items": list(parsed.interaction_payload.get("items", [])),
        "correct_order": list((parsed.answer_key or {}).get("correct_order", [])),
        "match_pairs": [],
        "fib_answers": list((parsed.answer_key or {}).get("fib_answers", [])),
        "prompt_with_blanks": parsed.interaction_payload.get("prompt_with_blanks", ""),
        "expected_lines": int(parsed.interaction_payload.get("expected_lines", 5) or 5),
        "numeric_answer": (parsed.answer_key or {}).get("correct", ""),
        "numeric_expected_length": int(parsed.interaction_payload.get("expected_length", 20) or 20),
    }

    if parsed.item_type == "Match":
        source_map = {
            source["id"]: source["text"]
            for source in parsed.interaction_payload.get("sources", [])
        }
        target_map = {
            target["id"]: target["text"]
            for target in parsed.interaction_payload.get("targets", [])
        }
        question["match_pairs"] = [
            {
                "source_id": pair["source_id"],
                "source_text": source_map.get(pair["source_id"], ""),
                "target_id": pair["target_id"],
                "target_text": target_map.get(pair["target_id"], ""),
            }
            for pair in (parsed.answer_key or {}).get("pairs", [])
        ]

    if parsed.item_type == "Numeric":
        question["fib_answers"] = []
        question["prompt_with_blanks"] = ""
        question["correct"] = [str(question["numeric_answer"])] if question["numeric_answer"] != "" else []

    return question

