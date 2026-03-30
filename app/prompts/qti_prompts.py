from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional
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
        self.prefix_templates = {
            ContentType.READING_MATERIAL: PromptConfig(
                prefix="As user I uploaded a reading material and I want to generate questions based on the whole content"
            ),
            ContentType.SIMILAR_QUESTIONS: {
                True: PromptConfig(  # gen_similar_questions=True
                    prefix="As user I uploaded a collection of questions and I want to generate same count of the questions",
                    maintain=[
                        "question type (mcq, fib, essay, etc)",
                        "learning objective",
                        "addressed topic/skill",
                        "difficulty"
                    ],
                    modify=[
                        "numbers, quantities, values",
                        "names",
                        "case scenarios",
                        "visual contexts",
                        "data points"
                    ]
                ),
                False: PromptConfig(  # gen_similar_questions=False
                    prefix="As user I uploaded a collection of questions and I want to generate questions",
                    maintain=[
                        "distribution of the learning objectives",
                        "assessed topics/skills",
                        "difficulty"
                    ],
                    modify=[
                        "question type (mcq, fib, essay, etc) using best judgement",
                        "numbers, quantities, values",
                        "names",
                        "case scenarios",
                        "visual contexts",
                        "data points"
                    ]
                )
            },
            ContentType.DIFFERENT_CONTENT: {
                True: PromptConfig(  # gen_similar_questions=True
                    prefix="Generate equivalent assessment questions with same structure but different content",
                    maintain=[
                        "Question types and their count",
                        "Core concepts and learning objectives",
                        "Difficulty level for each question",
                        "Assessment style and patterns",
                        "Conceptual relationships",
                        "Problem-solving steps",
                        "Critical thinking requirements",
                        "Knowledge assessment level"
                    ],
                    modify=[
                        "Content and context while preserving difficulty",
                        "Numbers and quantities",
                        "Names and examples",
                        "Data points and values",
                        "Case scenarios",
                        "Problem contexts",
                        "Visual elements"
                    ]
                ),
                False: PromptConfig(  # gen_similar_questions=False
                    prefix="Generate equivalent assessment questions with flexible structure",
                    maintain=[
                        "Core concepts and learning objectives",
                        "Overall difficulty distribution",
                        "Conceptual relationships",
                        "Problem-solving complexity",
                        "Critical thinking requirements",
                        "Knowledge assessment level"
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
                        "Assessment patterns while maintaining quality"
                    ]
                )
            }
        }

    def get_prefix(self, content_type: str, gen_similar_questions: bool = False) -> str:
        """Generate appropriate prompt prefix based on content type and generation mode"""
        content_type = ContentType(content_type)
        config = self.prefix_templates[content_type]

        if isinstance(config, dict):  # Handle both SIMILAR_QUESTIONS and DIFFERENT_CONTENT
            config = config[gen_similar_questions]

        return self._format_prompt_prefix(config)

    def _format_prompt_prefix(self, config: PromptConfig) -> str:
        """Format prompt prefix with maintained and modified elements"""
        prefix_parts = [config.prefix]

        if config.maintain:
            prefix_parts.append("\nAnalyze the provided content and maintain/preserve:")
            prefix_parts.extend(f"* {item}" for item in config.maintain)

        if config.modify:
            prefix_parts.append("\nCreate new questions by modifying:")
            prefix_parts.extend(f"* {item}" for item in config.modify)

        return "\n".join(prefix_parts)

    @staticmethod
    def get_system_prompt() -> str:
        """Generate system prompt for the given content type and generation mode"""

        def load_yaml_file(filename: str) -> dict:
            """Load and parse YAML file"""
            with open(Path('app/templates') / filename, 'r') as f:
                return yaml.safe_load(f)

        # Load formats for examples
        formats = load_yaml_file('question_formats.yaml')['question_formats']

        # Format the yaml examples as a string
        format_examples = yaml.dump(formats, default_flow_style=False, sort_keys=False)

        system_text = f"""You are A HIGH QUALITY HIGH SCHOOL TEACHER IN VARIOUS SUBJECTS who is ALSO HIGHLY SKILLED IN
        CRAFTING ORIGINAL QUESTIONS FOR KNOWLEDGE ASSESSMENT OF STUDENTS.
        Generate questions in YAML format using PROVIDED CONTENT AS THE SOLE SOURCE OF INFORMATION.
        IMPORTANT: FOLLOW THE USER-PROVIDED COGNITIVE MIX TARGETS IF PROVIDED.
        IF NOT PROVIDED, DEFAULT TO 30% HIGH-LEVEL THINKING, 50% INTERMEDIATE THINKING, 20% BASIC RECALL.
        KEY RULES:
        1. STRICTLY FOLLOW YAML FORMAT PROVIDED BY THE USER. Proper indentation is critical - use 2 spaces for each level.
        2. When MCQ: MUST have exactly 4 choices with ONE correct.
        3. When FIB: Use single underscore (_) for each blank.
        MINIMUM 2 blanks per question. MUST INCLUDE ANSWER KEY FOR EACH BLANK. PER BLANK: MAXIMUM 1 BEST ANSWER.
        MUST SET expectedLength=20 ALWAYS.ENFORCE CORRECT FORMAT TO AVOID ERRORS.
        DO NOT PUT ANY LaTex FORMATTING IN THE QUESTIONS OR ANSWERS. USE INLINE EQUATION FORMAT FOR MATH RELATED INFORMATION AND
        EASY TO MOVE TO RICH TEXT EDITOR OVERALL.
        4. When ORDER: MUST have MINIMUM 5 ITEMS TO ORDER. THE ITEMS IN QUESTION SHOULD BE SHUFFLED AND THE ANSWER KEY SEQUENCE
        SHOULD BE PROVIDED.
        5. When MATCH: Generate minimum 4 and maximum 8 pairs to match in the question.
        6. Each answer must be in string format: ["answer"].
        7. Include all required fields: identifier, title, adaptive, timeDependent, prompt.
        8. Questions directly and only related to the provided source material.
        9. Do not include any markdown formatting or explanations.
        10. All answers must be convertible to strings. DO NOT USE &, -, + OR SIMILAR CHARACTERS IN QUESTIONS AND ANSWERS BECAUSE
        THEY CAUSE ERRORS TO XML CONVERSION.
        11. FORMAT USER REQUESTED QUESTIONS BY STRICTLY FOLLOWING THE REFERENCE YAML FORMATs BELOW, MAINTAN PROPER INDENTATION.

        REFERENCE FORMATS:
        {format_examples}
        """

        return system_text


def _format_cognitive_mix(cognitive_distribution: Optional[Dict[str, int]] = None) -> str:
    if not cognitive_distribution:
        return "Basic recall 20%, Intermediate application 50%, High-level reasoning 30%."

    basic = int(cognitive_distribution.get("basic", 20))
    intermediate = int(cognitive_distribution.get("intermediate", 50))
    high = int(cognitive_distribution.get("high", 30))

    total = basic + intermediate + high
    if total <= 0:
        return "Basic recall 20%, Intermediate application 50%, High-level reasoning 30%."

    if total != 100:
        basic = round(basic * 100 / total)
        intermediate = round(intermediate * 100 / total)
        high = max(0, 100 - basic - intermediate)

    return (
        f"Basic recall {basic}%, "
        f"Intermediate application {intermediate}%, "
        f"High-level reasoning {high}%."
    )


def create_complete_prompt(
    special_instructions,
    content_type: str,
    assessment_type,
    num_questions_dict: Optional[Dict[str, int]] = None,
    gen_similar_questions: bool = False,
    cognitive_distribution: Optional[Dict[str, int]] = None,
) -> str:
    """Creates complete prompt combining prefix and YAML format instructions"""
    prefix_generator = PromptPrefixGenerator()
    prompt_prefix = prefix_generator.get_prefix(content_type, gen_similar_questions)
    question_cnt_instr=''
    if gen_similar_questions==True:
        question_cnt_instr="same as in the user-provided content."
    else:
        question_cnt_instr=', '.join([f"{count} QUESTIONS of {qtype} QUESTION TYPE." for qtype, count in num_questions_dict.items() if count > 0])
    return f"{prompt_prefix}\n\n{create_yaml_prompt(special_instructions,assessment_type,question_cnt_instr,num_questions_dict,cognitive_distribution)}"

def create_yaml_prompt(
    special_instructions,
    assessment_type,
    question_cnt_instr: str,
    num_questions_dict: Optional[Dict[str, int]] = None,
    cognitive_distribution: Optional[Dict[str, int]] = None,
) -> str:
    """Create prompt for LLM to generate questions in YAML format"""
    from pathlib import Path

    def load_yaml_file(filename: str) -> dict:
        """Load and parse YAML file"""
        with open(Path('app/templates') / filename, 'r') as f:
            return yaml.safe_load(f)

    # Load formats for examples
    formats = load_yaml_file('question_formats.yaml')['question_formats']

    prompt_parts = [
        "Generate questions in YAML format using provided content as the sole source.",
        "FOLLOW THE KEY RULES IN THE SYSTEM PROMPT WHEN CRAFTING QUESTIONS. THE USER REQUESTED QUESTION TYPES AND COUNTS ARE MENTIONED BELOW.",
        f"ASSESSMENT TYPE: {assessment_type}",
        f"TARGET COGNITIVE MIX: {_format_cognitive_mix(cognitive_distribution)}",
        "Ensure the complete set of generated questions follows the target cognitive mix across all requested question types.",
        f"FOR EACH QUESTION CONSIDER USER-SPECIAL INSTRUCTIONS: {special_instructions}",
        "STRICTLY FOLLOW THE BELOW LIST OF QUESTION TYPES AND COUNT TO CRAFT YOUR QUESTIONS:",
        question_cnt_instr,
    ]

    # Add final instructions
    prompt_parts.extend([
        "\nIMPORTANT:",
        "- Start IMMEDIATELY with \"- type:\"",
        "- No explanation text, no markdown",
        "- NO YAML DOCUMENT MARKERS LIKE (---), (```yaml), (```)",
        "- Maintain consistent 2-space indentation",
        "\nBegin YAML list now:"
    ])

    return "\n".join(prompt_parts)


def create_pdf_question_conversion_prompt(special_instructions: str) -> str:
    """Create prompt for converting PDF question banks into app YAML format."""

    def load_yaml_file(filename: str) -> dict:
        with open(Path("app/templates") / filename, "r") as f:
            return yaml.safe_load(f)

    formats = load_yaml_file("question_formats.yaml")["question_formats"]
    format_examples = yaml.dump(formats, default_flow_style=False, sort_keys=False)

    prompt_parts = [
        "Extract the existing questions from the uploaded PDF and convert them to YAML.",
        "Treat the PDF as a ready question set, not as reading material for new content generation.",
        "Preserve each question's intent, difficulty, and correct answer validity.",
        "Keep wording close to the source unless a tiny clarity fix is required for YAML validity.",
        "Only emit supported question types: mcq, mrq, tf, fib, essay, match, order.",
        "If an item is ambiguous or unsupported, skip it instead of inventing details.",
        f"FOR EACH QUESTION CONSIDER USER-SPECIAL INSTRUCTIONS: {special_instructions}",
        "STRICTLY FOLLOW THE REFERENCE YAML FORMAT BELOW.",
        "",
        "IMPORTANT:",
        '- Start IMMEDIATELY with "- type:"',
        "- No explanation text, no markdown",
        "- NO YAML DOCUMENT MARKERS LIKE (---), (```yaml), (```)",
        "- Maintain consistent 2-space indentation",
        "",
        "REFERENCE FORMATS:",
        format_examples,
        "Begin YAML list now:",
    ]

    return "\n".join(prompt_parts)

def create_extension_prompt(base_prompt: str, media_info: Dict) -> str:
    """Add media-specific instructions to the base prompt"""
    if not media_info:
        return base_prompt

    # Get media metadata from configuration
    with open('app/templates/metadata.yaml', 'r') as f:
        metadata = yaml.safe_load(f)
        media_settings = metadata['common_settings']['media_settings']

    media_prompt = f"""

Image requirements:
- Available images: {', '.join(media_info.keys())}
- Reference: <img src="media/{{filename}}"/>
- Max dimensions: {media_settings['max_dimensions']}
- Allowed formats: {', '.join(media_settings['allowed_formats'])}
- For hotspots/matching: Use exact coordinates
- Include clear image interaction instructions"""

    return base_prompt + media_prompt
