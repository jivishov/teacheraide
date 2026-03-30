from enum import Enum
from dataclasses import dataclass
from typing import Optional
import yaml
from pathlib import Path


class ContentType(Enum):
    READING_MATERIAL = "rm_q"
    SIMILAR_QUESTIONS = "siml_q"
    DIFFERENT_CONTENT = "diffr_q"
    IMAGE_QUESTION = "img_q"


@dataclass
class PromptConfig:
    prefix: str
    maintain: Optional[list] = None
    modify: Optional[list] = None


class PromptPrefixGenerator:
    """Manages prompt prefixes for different content types and scenarios"""

    def __init__(self):
        self._prefix_templates = {
            ContentType.READING_MATERIAL: PromptConfig(
                prefix="As user I uploaded a reading material and I want to generate questions based on the whole content"
            ),
            ContentType.SIMILAR_QUESTIONS: {
                True: PromptConfig(
                    prefix="As user I uploaded a collection of questions and I want to generate same count of the questions",
                    maintain=[
                        "learning objective",
                        "addressed topic/skill",
                        "difficulty",
                    ],
                    modify=[
                        "numbers, quantities, values",
                        "names",
                        "case scenarios",
                        "visual contexts",
                        "data points",
                    ],
                ),
                False: PromptConfig(
                    prefix="As user I uploaded a collection of questions and I want to generate questions",
                    maintain=[
                        "distribution of the learning objectives",
                        "assessed topics/skills",
                        "difficulty",
                    ],
                    modify=[
                        "question type (mcq, fib, essay, etc) using best judgement",
                        "numbers, quantities, values",
                        "names",
                        "case scenarios",
                        "visual contexts",
                        "data points",
                    ],
                ),
            },
            ContentType.DIFFERENT_CONTENT: {
                True: PromptConfig(
                    prefix="Generate equivalent assessment questions with same structure but different content",
                    maintain=[
                        "Question types and their count",
                        "Core concepts and learning objectives",
                        "Difficulty level for each question",
                        "Assessment style and patterns",
                        "Conceptual relationships",
                        "Problem-solving steps",
                        "Critical thinking requirements",
                        "Knowledge assessment level",
                    ],
                    modify=[
                        "Content and context while preserving difficulty",
                        "Numbers and quantities",
                        "Names and examples",
                        "Data points and values",
                        "Case scenarios",
                        "Problem contexts",
                        "Visual elements",
                    ],
                ),
                False: PromptConfig(
                    prefix="Generate equivalent assessment questions with flexible structure",
                    maintain=[
                        "Core concepts and learning objectives",
                        "Overall difficulty distribution",
                        "Conceptual relationships",
                        "Problem-solving complexity",
                        "Critical thinking requirements",
                        "Knowledge assessment level",
                    ],
                    modify=[
                        "Question types based on best judgment",
                        "Content and context",
                        "Numbers and quantities",
                        "Names and examples",
                        "Data points and values",
                        "Case scenarios",
                        "Problem contexts",
                        "Visual elements",
                        "Assessment patterns while maintaining quality",
                    ],
                ),
            },
        }

    def get_prefix(self, content_type: str, gen_similar_questions: bool = False) -> str:
        """Generate appropriate prompt prefix based on content type and generation mode"""
        content_type_enum = ContentType(content_type)
        config = self._prefix_templates[content_type_enum]
        if isinstance(config, dict):
            config = config[gen_similar_questions]
        return self._format_prompt_prefix(config)

    def _format_prompt_prefix(self, config: PromptConfig) -> str:
        """Format prompt prefix with maintained and modified elements"""
        prefix_parts = [config.prefix]
        if config.maintain:
            prefix_parts.append("""
Analyze the provided content and maintain/preserve:""")
            prefix_parts.extend((f"* {item}" for item in config.maintain))
        if config.modify:
            prefix_parts.append("""
Create new questions by modifying:""")
            prefix_parts.extend((f"* {item}" for item in config.modify))
        return """
""".join(prefix_parts)

    @staticmethod
    def get_system_prompt() -> str:
        """Generate system prompt for the given content type and generation mode"""

        def load_yaml_file(filename: str) -> dict:
            """Load and parse YAML file"""
            with open(Path("templates") / filename, "r") as f:
                return yaml.safe_load(f)

        formats = load_yaml_file("question_formats.yaml")["question_formats"]
        format_examples = yaml.dump(formats, default_flow_style=False, sort_keys=False)
        system_text = f'You are A HIGH QUALITY HIGH SCHOOL TEACHER IN VARIOUS SUBJECTS who is ALSO HIGHLY SKILLED IN \nCRAFTING ORIGINAL QUESTIONS FOR KNOWLEDGE ASSESSMENT OF STUDENTS.\nGenerate questions in YAML format using PROVIDED CONTENT AS THE SOLE SOURCE OF INFORMATION.\nIMPORTANT: AIM TO HAVE 30% OF THE QUESTIONS AS HIGH LEVEL THINKING, \n50% OF THE QUESTIONS INTERMEDIATE LEVEL OF THINKING, 20% OF THE QUESTIONS BASIC RECALL OF TERMINOLOGY OR CONCEPTS.\nKEY RULES:\n1. STRICTLY FOLLOW YAML FORMAT PROVIDED BY THE USER. Proper indentation is critical - use 2 spaces for each level.\n2. When MCQ: MUST have exactly 4 choices with ONE correct.\n3. When FIB: Use single underscore (_) for each blank.\nMINIMUM 2 blanks per question. MUST INCLUDE ANSWER KEY FOR EACH BLANK. PER BLANK: MAXIMUM 1 BEST ANSWER. \nMUST SET expectedLength=20 ALWAYS.ENFORCE CORRECT FORMAT TO AVOID ERRORS.\nDO NOT PUT ANY LaTex FORMATTING IN THE QUESTIONS OR ANSWERS. USE INLINE EQUATION FORMAT FOR MATH RELATED INFORMATION AND\nEASY TO MOVE TO RICH TEXT EDITOR OVERALL.\n4. When ORDER: MUST have MINIMUM 5 ITEMS TO ORDER. THE ITEMS IN QUESTION SHOULD BE SHUFFLED AND THE ANSWER KEY SEQUENCE \nSHOULD BE PROVIDED.\n5. When MATCH: Generate minimum 4 and maximum 8 pairs to match in the question.\n6. Each answer must be in string format: ["answer"].\n7. Include all required fields: identifier, title, adaptive, timeDependent, prompt.\n8. Questions directly and only related to the provided source material.\n9. Create unique identifiers like MCQ_1, FIB_1, etc.\n10. Do not include any markdown formatting or explanations.\n11. All answers must be convertible to strings. DO NOT USE &, -, + OR SIMILAR CHARACTERS IN QUESTIONS AND ANSWERS BECAUSE \nTHEY CAUSE ERRORS TO XML CONVERSION.\n12. FORMAT USER REQUESTED QUESTIONS BY STRICTLY FOLLOWING THE REFERENCE YAML FORMATs BELOW, MAINTAN PROPER INDENTATION.\n\nREFERENCE FORMATS:\n{format_examples}\n'
        return system_text


def create_complete_prompt(
    special_instructions,
    content_type: str,
    assessment_type,
    num_questions_dict: Optional[dict[str, int]] = None,
    gen_similar_questions: bool = False,
) -> str:
    """Creates complete prompt combining prefix and YAML format instructions"""
    prefix_generator = PromptPrefixGenerator()
    prompt_prefix = prefix_generator.get_prefix(content_type, gen_similar_questions)
    question_cnt_instr = ""
    if gen_similar_questions == True:
        question_cnt_instr = "same as in the user-provided content."
    else:
        question_cnt_instr = ", ".join(
            [
                f"{count} QUESTIONS of {qtype} QUESTION TYPE."
                for qtype, count in num_questions_dict.items()
                if count > 0
            ]
        )
    return f"{prompt_prefix}\n\n{create_yaml_prompt(special_instructions, assessment_type, question_cnt_instr, num_questions_dict)}"


def create_yaml_prompt(
    special_instructions,
    assessment_type,
    question_cnt_instr: str,
    num_questions_dict: Optional[dict[str, int]] = None,
) -> str:
    """Create prompt for LLM to generate questions in YAML format"""
    from pathlib import Path

    def load_yaml_file(filename: str) -> dict:
        """Load and parse YAML file"""
        with open(Path("templates") / filename, "r") as f:
            return yaml.safe_load(f)

    formats = load_yaml_file("question_formats.yaml")["question_formats"]
    prompt_parts = [
        "Generate questions in YAML format using provided content as the sole source.",
        "FOLLOW THE KEY RULES IN THE SYSTEM PROMPT WHEN CRAFTING QUESTIONS. THE USER REQUESTED QUESTION TYPES AND COUNTS ARE MENTIONED BELOW.",
        f"ASSESSMENT TYPE: {assessment_type}",
        f"FOR EACH QUESTION CONSIDER USER-SPECIAL INSTRUCTIONS: {special_instructions}",
        "STRICTLY FOLLOW THE BELOW LIST OF QUESTION TYPES AND COUNT TO CRAFT YOUR QUESTIONS:",
        question_cnt_instr,
    ]
    prompt_parts.extend(
        [
            """
IMPORTANT:""",
            '- Start IMMEDIATELY with "- type:"',
            "- No explanation text, no markdown",
            "- NO YAML DOCUMENT MARKERS LIKE (---), (yaml), ()",
            "- Maintain consistent 2-space indentation",
            """
Begin YAML list now:""",
        ]
    )
    return """
""".join(prompt_parts)


def create_extension_prompt(base_prompt: str, media_info: dict) -> str:
    """Add media-specific instructions to the base prompt"""
    if not media_info:
        return base_prompt
    with open("templates/metadata.yaml", "r") as f:
        metadata = yaml.safe_load(f)
        media_settings = metadata["common_settings"]["media_settings"]
    media_prompt = f"""\n\nImage requirements:\n- Available images: {", ".join(media_info.keys())}\n- Reference: <img src="media/{{filename}}"/>\n- Max dimensions: {media_settings["max_dimensions"]}\n- Allowed formats: {", ".join(media_settings["allowed_formats"])}\n- For hotspots/matching: Use exact coordinates\n- Include clear image interaction instructions"""
    return base_prompt + media_prompt