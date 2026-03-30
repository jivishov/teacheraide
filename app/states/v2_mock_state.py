"""Mock state classes for V2 UI mockup pages. No real backend logic."""

import reflex as rx
from app.utils.model_catalog import (
    DEFAULT_ANTHROPIC_MODELS,
    DEFAULT_GEMINI_MODELS,
    DEFAULT_OPENAI_MODEL,
    DEFAULT_OPENAI_MODELS,
)

DEFAULT_V2_MODEL_OPTIONS = list(DEFAULT_OPENAI_MODELS[:5]) + list(DEFAULT_ANTHROPIC_MODELS[:2]) + list(DEFAULT_GEMINI_MODELS[:1])


class ReadingMaterialV2State(rx.State):
    """Mock state for the Reading Material V2 page."""

    content_type: str = "reading"
    grade_level: str = "9"
    topic: str = ""
    objectives: str = ""
    user_prompt: str = ""

    # Reference material uploads (mock)
    ref_files: list[dict[str, str]] = [
        {"name": "chapter_10_notes.pdf", "type": "pdf", "size": "2.4 MB"},
        {"name": "cell_diagram.png", "type": "image", "size": "890 KB"},
    ]
    max_ref_files: int = 5
    upload_error: str = ""

    active_model: str = DEFAULT_OPENAI_MODEL
    show_output: bool = False
    generated_content: str = ""

    # Preflight
    preflight_model: bool = True
    preflight_api_key: bool = True
    preflight_topic: bool = False

    # Generation state
    generating: bool = False
    progress: int = 0
    generation_stage: str = "Idle"

    @rx.var
    def ref_file_count(self) -> int:
        return len(self.ref_files)

    @rx.var
    def can_add_ref_file(self) -> bool:
        return len(self.ref_files) < self.max_ref_files

    @rx.var
    def preflight_all_ok(self) -> bool:
        return self.preflight_model and self.preflight_api_key and self.preflight_topic

    @rx.var
    def can_generate(self) -> bool:
        return self.preflight_all_ok and not self.generating

    @rx.var
    def word_count(self) -> int:
        return len(self.generated_content.split()) if self.generated_content else 0

    @rx.var
    def section_count(self) -> int:
        count = 0
        for line in self.generated_content.split("\n"):
            if line.startswith("## "):
                count += 1
        return count

    grade_levels: list[str] = [
        "K", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
        "College",
    ]

    model_options: list[str] = list(DEFAULT_V2_MODEL_OPTIONS)

    def set_content_type_v2(self, val: str):
        self.content_type = val

    def set_grade_level_v2(self, val: str):
        self.grade_level = val

    def set_topic_v2(self, val: str):
        self.topic = val
        self.preflight_topic = len(val.strip()) > 0

    def set_objectives_v2(self, val: str):
        self.objectives = val

    def set_user_prompt_v2(self, val: str):
        self.user_prompt = val

    def set_active_model_v2(self, val: str):
        self.active_model = val

    def mock_add_ref_file(self):
        """Mock adding a reference file."""
        if len(self.ref_files) >= self.max_ref_files:
            self.upload_error = f"Maximum {self.max_ref_files} files allowed."
            return
        mock_files = [
            {"name": "syllabus_spring_2026.docx", "type": "docx", "size": "1.1 MB"},
            {"name": "photosynthesis_diagram.jpg", "type": "image", "size": "1.5 MB"},
            {"name": "lab_manual_excerpt.pdf", "type": "pdf", "size": "4.2 MB"},
        ]
        self.ref_files.append(mock_files[len(self.ref_files) % len(mock_files)])
        self.upload_error = ""

    def remove_ref_file(self, index: int):
        if 0 <= index < len(self.ref_files):
            self.ref_files.pop(index)
            self.upload_error = ""

    def clear_ref_files(self):
        self.ref_files = []
        self.upload_error = ""

    def mock_generate(self):
        self.generated_content = (
            "# Photosynthesis\n\n"
            "## Introduction\n\n"
            "Photosynthesis is the process by which green plants and some other organisms "
            "use sunlight to synthesize foods from carbon dioxide and water.\n\n"
            "## The Light Reactions\n\n"
            "The light-dependent reactions take place in the thylakoid membranes. "
            "They require light energy, which is absorbed by chlorophyll and other pigments.\n\n"
            "## The Calvin Cycle\n\n"
            "The Calvin Cycle uses ATP and NADPH produced by the light reactions "
            "to fix carbon dioxide into organic molecules.\n\n"
            "## Key Vocabulary\n\n"
            "- **Chloroplast** - organelle where photosynthesis occurs\n"
            "- **Stomata** - pores on leaf surfaces for gas exchange\n"
            "- **ATP** - adenosine triphosphate, energy currency of cells"
        )
        self.show_output = True
        self.generating = False
        self.progress = 100
        self.generation_stage = "Complete"

    def clear_output(self):
        self.generated_content = ""
        self.show_output = False


class TextQuestionsV2State(rx.State):
    """Mock state for the Text Questions V2 page."""

    # Quick / Advanced mode toggle
    ui_mode: str = "quick"  # "quick" | "advanced"
    active_preset: str = "Formative"  # tracks which preset chip is selected

    # Form fields
    assessment_type: str = "Formative"
    selected_subject: str = "Biology"
    assessment_title: str = ""
    content_type: str = "rm_q"
    special_instructions: str = ""

    # Question counts
    mcq_count: int = 4
    mrq_count: int = 1
    tf_count: int = 2
    fib_count: int = 2
    essay_count: int = 1
    match_count: int = 0
    order_count: int = 0

    # Cognitive distribution
    cog_basic: int = 40
    cog_mid: int = 40
    cog_high: int = 20

    # Model / preflight
    active_model: str = DEFAULT_OPENAI_MODEL
    preflight_pdf: bool = True
    preflight_model: bool = True
    preflight_api_key: bool = True
    preflight_feature: bool = True

    # Generation state
    generating: bool = False
    progress: int = 0
    generation_stage: str = "Idle"

    model_options: list[str] = list(DEFAULT_V2_MODEL_OPTIONS)

    @rx.var
    def total_questions(self) -> int:
        return (
            self.mcq_count + self.mrq_count + self.tf_count
            + self.fib_count + self.essay_count
            + self.match_count + self.order_count
        )

    @rx.var
    def preflight_all_ok(self) -> bool:
        return (
            self.preflight_pdf
            and self.preflight_model
            and self.preflight_api_key
            and self.preflight_feature
        )

    @rx.var
    def can_generate(self) -> bool:
        return self.preflight_all_ok and self.total_questions > 0 and not self.generating

    @rx.var
    def estimated_output_label(self) -> str:
        n = self.total_questions
        return f"~{n} questions, mixed difficulty"

    @rx.var
    def is_quick_mode(self) -> bool:
        return self.ui_mode == "quick"

    def set_ui_mode(self, mode: str):
        self.ui_mode = mode

    def apply_preset(self, name: str):
        self.active_preset = name
        if name == "Formative":
            self.mcq_count = 4
            self.mrq_count = 1
            self.tf_count = 2
            self.fib_count = 2
            self.essay_count = 1
            self.match_count = 0
            self.order_count = 0
            self.cog_basic = 40
            self.cog_mid = 40
            self.cog_high = 20
            self.assessment_type = "Formative"
        elif name == "Summative":
            self.mcq_count = 8
            self.mrq_count = 2
            self.tf_count = 3
            self.fib_count = 3
            self.essay_count = 2
            self.match_count = 1
            self.order_count = 1
            self.cog_basic = 30
            self.cog_mid = 40
            self.cog_high = 30
            self.assessment_type = "Summative"
        elif name == "Quick Check":
            self.mcq_count = 3
            self.mrq_count = 0
            self.tf_count = 2
            self.fib_count = 0
            self.essay_count = 0
            self.match_count = 0
            self.order_count = 0
            self.cog_basic = 60
            self.cog_mid = 30
            self.cog_high = 10
            self.assessment_type = "Practice"
        elif name == "Homework":
            self.mcq_count = 5
            self.mrq_count = 1
            self.tf_count = 2
            self.fib_count = 3
            self.essay_count = 1
            self.match_count = 1
            self.order_count = 0
            self.cog_basic = 35
            self.cog_mid = 40
            self.cog_high = 25
            self.assessment_type = "Practice"

    def set_mcq(self, val: str):
        self.mcq_count = max(0, min(20, int(val))) if val.isdigit() else self.mcq_count

    def set_mrq(self, val: str):
        self.mrq_count = max(0, min(20, int(val))) if val.isdigit() else self.mrq_count

    def set_tf(self, val: str):
        self.tf_count = max(0, min(20, int(val))) if val.isdigit() else self.tf_count

    def set_fib(self, val: str):
        self.fib_count = max(0, min(20, int(val))) if val.isdigit() else self.fib_count

    def set_essay(self, val: str):
        self.essay_count = max(0, min(20, int(val))) if val.isdigit() else self.essay_count

    def set_match(self, val: str):
        self.match_count = max(0, min(20, int(val))) if val.isdigit() else self.match_count

    def set_order(self, val: str):
        self.order_count = max(0, min(20, int(val))) if val.isdigit() else self.order_count

    def inc_mcq(self):
        self.mcq_count = min(20, self.mcq_count + 1)

    def dec_mcq(self):
        self.mcq_count = max(0, self.mcq_count - 1)

    def inc_mrq(self):
        self.mrq_count = min(20, self.mrq_count + 1)

    def dec_mrq(self):
        self.mrq_count = max(0, self.mrq_count - 1)

    def inc_tf(self):
        self.tf_count = min(20, self.tf_count + 1)

    def dec_tf(self):
        self.tf_count = max(0, self.tf_count - 1)

    def inc_fib(self):
        self.fib_count = min(20, self.fib_count + 1)

    def dec_fib(self):
        self.fib_count = max(0, self.fib_count - 1)

    def inc_essay(self):
        self.essay_count = min(20, self.essay_count + 1)

    def dec_essay(self):
        self.essay_count = max(0, self.essay_count - 1)

    def inc_match(self):
        self.match_count = min(20, self.match_count + 1)

    def dec_match(self):
        self.match_count = max(0, self.match_count - 1)

    def inc_order(self):
        self.order_count = min(20, self.order_count + 1)

    def dec_order(self):
        self.order_count = max(0, self.order_count - 1)

    def set_active_model_v2(self, val: str):
        self.active_model = val

    def set_content_type_v2(self, val: str):
        self.content_type = val

    def set_assessment_type_v2(self, val: str):
        self.assessment_type = val

    def set_subject_v2(self, val: str):
        self.selected_subject = val

    def set_title_v2(self, val: str):
        self.assessment_title = val

    def set_instructions_v2(self, val: str):
        self.special_instructions = val

    def mock_generate(self):
        """Mock generate action — simulates starting generation."""
        self.generating = True
        self.progress = 0
        self.generation_stage = "Generating"


class ImageQuestionsV2State(rx.State):
    """Mock state for the Image Questions V2 page."""

    # Quick / Advanced mode toggle
    ui_mode: str = "quick"  # "quick" | "advanced"

    # Batch defaults
    batch_question_type: str = "Multiple choice"
    batch_subject: str = "Biology"
    batch_assessment_type: str = "Formative"
    batch_title: str = ""
    special_instructions: str = ""

    # Mock uploaded images
    uploaded_images: list[str] = [
        "cell_diagram.png",
        "mitosis.jpg",
        "",
        "",
    ]
    question_types: list[str] = [
        "Multiple choice",
        "True/False",
        "Multiple choice",
        "Multiple choice",
    ]
    image_prompts: list[str] = [
        "Identify the parts of the cell shown in the diagram.",
        "",
        "",
        "",
    ]
    image_statuses: list[str] = [
        "Ready",
        "Ready",
        "Awaiting",
        "Awaiting",
    ]

    expanded_slot: int = -1

    # Model / preflight
    active_model: str = DEFAULT_OPENAI_MODEL
    preflight_model: bool = True
    preflight_api_key: bool = True
    preflight_feature: bool = True

    # Generation state
    generating: bool = False
    progress: int = 0
    generation_stage: str = "Idle"

    model_options: list[str] = list(DEFAULT_V2_MODEL_OPTIONS)

    @rx.var
    def images_ready_count(self) -> int:
        count = 0
        for img in self.uploaded_images:
            if img != "":
                count += 1
        return count

    @rx.var
    def total_slots(self) -> int:
        return len(self.uploaded_images)

    @rx.var
    def is_quick_mode(self) -> bool:
        return self.ui_mode == "quick"

    @rx.var
    def preflight_all_ok(self) -> bool:
        return (
            self.preflight_model
            and self.preflight_api_key
            and self.preflight_feature
        )

    @rx.var
    def can_generate(self) -> bool:
        has_images = False
        for img in self.uploaded_images:
            if img != "":
                has_images = True
                break
        return self.preflight_all_ok and has_images and not self.generating

    def set_ui_mode(self, mode: str):
        self.ui_mode = mode

    def toggle_slot(self, index: int):
        if self.expanded_slot == index:
            self.expanded_slot = -1
        else:
            self.expanded_slot = index

    def add_slot(self):
        if len(self.uploaded_images) < 10:
            self.uploaded_images.append("")
            self.question_types.append(self.batch_question_type)
            self.image_prompts.append("")
            self.image_statuses.append("Awaiting")

    def remove_slot(self, index: int):
        if len(self.uploaded_images) > 1 and 0 <= index < len(self.uploaded_images):
            self.uploaded_images.pop(index)
            self.question_types.pop(index)
            self.image_prompts.pop(index)
            self.image_statuses.pop(index)
            if self.expanded_slot == index:
                self.expanded_slot = -1
            elif self.expanded_slot > index:
                self.expanded_slot -= 1

    def set_batch_question_type_v2(self, val: str):
        self.batch_question_type = val

    def set_batch_subject_v2(self, val: str):
        self.batch_subject = val

    def set_batch_assessment_type_v2(self, val: str):
        self.batch_assessment_type = val

    def set_batch_title_v2(self, val: str):
        self.batch_title = val

    def set_instructions_v2(self, val: str):
        self.special_instructions = val

    def set_slot_question_type(self, index: int, val: str):
        if 0 <= index < len(self.question_types):
            self.question_types[index] = val

    def set_slot_prompt(self, index: int, val: str):
        if 0 <= index < len(self.image_prompts):
            self.image_prompts[index] = val

    def set_active_model_v2(self, val: str):
        self.active_model = val

    def mock_generate(self):
        """Mock generate action — simulates starting generation."""
        self.generating = True
        self.progress = 0
        self.generation_stage = "Generating"
