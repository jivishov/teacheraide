#description: This file converts YAML formatted questions to QTI 2.2 XML format. The file supports multiple question types including Multiple Choice, True/False, Fill in the Blank, Matching, Ordering, and Essay questions.
# file name: yaml_converter.py

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET
from xml.dom import minidom
import yaml
from dataclasses import dataclass
import logging

@dataclass
class QuestionTemplate:
    """Template metadata for question types"""
    type: str
    xml_content: str

class YAMLtoQTIConverter:
    """Convert YAML formatted questions to QTI 2.2 XML"""
    def __init__(self, templates_dir: str = "app/templates"):
        """Initialize converter with templates"""
        self.ns = "http://www.imsglobal.org/xsd/imsqti_v2p2"
        self.templates_dir = Path(templates_dir)
        self.question_types_dir = self.templates_dir / "question_types"
        self.package_dir = self.templates_dir / "package"

        # Load metadata from YAML file
        metadata_path = self.templates_dir / "metadata.yaml"
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = yaml.safe_load(f)
        except FileNotFoundError:
            logging.warning(f"Metadata file not found at {metadata_path}")
            self.metadata = {}

        self.templates = self._load_templates()
        self.package_templates = self._load_package_templates()
        self.last_conversion_warnings: List[str] = []
        ET.register_namespace('', self.ns)

    def _load_templates(self) -> Dict[str, QuestionTemplate]:
        """Load question type templates"""
        templates = {}
        template_files = {
            'fib': 'fib.xml',
            'mcq': 'mcq.xml',
            'mrq': 'mrq.xml',
            'tf': 'tf.xml',
            'match': 'match.xml',
            'order': 'order.xml',
            'essay': 'essay.xml'
        }

        for qtype, filename in template_files.items():
            template_path = self.question_types_dir / filename
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    templates[qtype] = QuestionTemplate(
                        type=qtype,
                        xml_content=f.read()
                    )
            else:
                logging.warning(f"Template file {filename} not found in {self.question_types_dir}")

        return templates

    def _load_package_templates(self) -> Dict[str, str]:
        """Load package-level templates"""
        package_templates = {}
        template_files = ['manifest.xml', 'assessment.xml']

        for filename in template_files:
            template_path = self.package_dir / filename
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    package_templates[filename] = f.read()
            else:
                logging.warning(f"Package template {filename} not found in {self.package_dir}")

        return package_templates

    def create_qti_package(self, questions: List[str], test_title: str) -> bytes:
        """Create complete QTI package"""
        import zipfile
        from io import BytesIO
        import uuid

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add manifest
            manifest_xml = self.package_templates['manifest.xml'].format(
                manifest_id=f"MANIFEST-{uuid.uuid4()}",
                dependencies=self._generate_dependencies(questions),
                resources=self._generate_resources(questions)
            )
            zip_file.writestr('imsmanifest.xml', manifest_xml)

            # Add assessment test
            test_xml = self.package_templates['assessment.xml'].format(
                test_id=f"test-{uuid.uuid4()}",
                test_title=test_title,
                item_refs=self._generate_item_refs(questions)
            )
            zip_file.writestr('assessmentTest.xml', test_xml)

            # Add individual questions
            for question in questions:
                root = ET.fromstring(question)
                question_id = root.get('identifier')
                zip_file.writestr(f"{question_id}.xml", question)

        zip_buffer.seek(0)
        return zip_buffer.getvalue()

    def _generate_dependencies(self, questions: List[str]) -> str:
        """Generate dependency references for manifest"""
        dependencies = []
        for question in questions:
            root = ET.fromstring(question)
            identifier = root.get('identifier')
            dependencies.append(f'<dependency identifierref="{identifier}"/>')
        return '\n            '.join(dependencies)

    def _generate_resources(self, questions: List[str]) -> str:
        """Generate resource items for manifest"""
        resources = []
        for question in questions:
            root = ET.fromstring(question)
            identifier = root.get('identifier')
            resources.append(f'''
            <resource identifier="{identifier}" type="imsqti_item_xmlv2p2" href="{identifier}.xml">
                <file href="{identifier}.xml"/>
            </resource>''')
        return '\n'.join(resources)

    def _generate_item_refs(self, questions: List[str]) -> str:
        """Generate item references for assessment test"""
        refs = []
        for question in questions:
            root = ET.fromstring(question)
            identifier = root.get('identifier')
            refs.append(f'<assessmentItemRef identifier="{identifier}" href="{identifier}.xml"/>')
        return '\n            '.join(refs)

    def validate_question(self, question: Dict, question_type: str) -> bool:
        """Validate question format"""
        if not question_type:
            raise ValueError("Missing question type")

        if question_type not in self.templates:
            raise ValueError(f"Unsupported question type: {question_type}")

        # Basic validation for all questions
        if not self._validate_common(question):
            return False

        # Type-specific validation
        if question_type == 'fib':
            return self._validate_fib(question)
        elif question_type in ['mcq', 'mrq']:
            return self._validate_choices(question, question_type)
        elif question_type == 'tf':
            return self._validate_tf(question)
        elif question_type == 'match':
            return self._validate_match(question)
        elif question_type == 'order':
            return self._validate_order(question)
        elif question_type == 'essay':
            return self._validate_essay(question)

        return True

    def _escape_xml_chars(self, text: str) -> str:
        """Escape special XML characters in text content"""
        if not isinstance(text, str):
            text = str(text)

        # Replace XML special characters with their entities
        replacements = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&apos;'
        }

        for char, entity in replacements.items():
            text = text.replace(char, entity)

        return text

    def convert(self, yaml_str: str) -> List[str]:
        """Convert YAML string to list of QTI XML strings using custom parsing"""
        xml_questions, _warnings = self.convert_with_warnings(yaml_str)
        return xml_questions

    def convert_with_warnings(self, yaml_str: str) -> Tuple[List[str], List[str]]:
        """Convert YAML and return both XML output and non-fatal conversion warnings."""
        warnings: List[str] = []
        try:
            # Custom YAML parsing to handle LaTeX and other special characters
            questions = self._custom_yaml_parse(yaml_str)

            xml_questions = []
            for idx, question in enumerate(questions, start=1):
                try:
                    qtype = question.get('type')
                    if not qtype:
                        raise ValueError("Question missing type field")

                    # Get template and format XML
                    template = self.templates.get(qtype)
                    if not template:
                        raise ValueError(f"Template not found for type: {qtype}")

                    xml = self._format_question(question, template)
                    xml_questions.append(self._prettify(xml))

                except Exception as e:
                    identifier = question.get('identifier', f"unknown_{idx}")
                    warning = (
                        f"Question {idx} ({identifier}) skipped during YAML-to-QTI conversion: {str(e)}"
                    )
                    warnings.append(warning)
                    logging.warning(
                        "Skipped question %s (%s) during YAML-to-QTI conversion: %s",
                        idx,
                        identifier,
                        str(e),
                    )
                    continue

            self.last_conversion_warnings = warnings
            return xml_questions, warnings

        except Exception as e:
            self.last_conversion_warnings = []
            raise ValueError(f"Invalid YAML format: {str(e)}")

    def _custom_yaml_parse(self, yaml_str: str) -> List[Dict]:
        """Parse YAML content manually to handle LaTeX, HTML, and nested structures"""
        import re

        # Split into individual questions
        question_blocks = re.split(r'(?=^- type:)', yaml_str, flags=re.MULTILINE)
        questions = []

        for block in question_blocks:
            if not block.strip():
                continue

            # Process each question
            question_dict = {}
            lines = block.strip().split('\n')

            # Process header line (- type: xxx)
            if lines[0].startswith('- type:'):
                question_dict['type'] = lines[0].split(':', 1)[1].strip().strip('"\'')

            # Process remaining fields
            i = 1
            in_choices = False
            choices = []
            current_choice = None

            # For FIB questions
            in_fib_answers = False
            fib_answers = []
            current_fib_answer = []

            # For match-type questions
            in_match_sets = False
            match_sets = {'source': [], 'target': []}
            in_source = False
            in_target = False
            current_match_item = None

            # For correctPairs in match questions
            in_correct_pairs = False
            correct_pairs = []
            current_pair = []

            # For order type questions
            in_correct_sequence = False
            correct_sequence = []

            while i < len(lines):
                line = lines[i].rstrip()

                # Skip empty lines
                if not line.strip():
                    i += 1
                    continue

                # Handle match-type questions specifically
                if question_dict.get('type') == 'match':
                    # Detect matchSets section
                    if line.strip() == 'matchSets:':
                        in_match_sets = True
                        i += 1
                        continue

                    # Process matchSets subsections
                    if in_match_sets:
                        # Detect source section
                        if line.strip() == 'source:':
                            # If we're transitioning from target to source, save any pending target item
                            if in_target and current_match_item:
                                match_sets['target'].append(current_match_item)
                                current_match_item = None

                            in_source = True
                            in_target = False
                            i += 1
                            continue

                        # Detect target section
                        elif line.strip() == 'target:':
                            # If we're transitioning from source to target, save any pending source item
                            if in_source and current_match_item:
                                match_sets['source'].append(current_match_item)
                                current_match_item = None

                            in_source = False
                            in_target = True
                            i += 1
                            continue

                        # Process items in source or target
                        elif (in_source or in_target) and line.strip().startswith('- identifier:'):
                            # Store previous item if exists
                            if current_match_item:
                                if in_source:
                                    match_sets['source'].append(current_match_item)
                                else:
                                    match_sets['target'].append(current_match_item)

                            # Start new item
                            current_match_item = {'identifier': line.strip()[13:].strip().strip('"\'') }

                        # Process item fields
                        elif current_match_item and ':' in line and (in_source or in_target):
                            field, value = line.strip().split(':', 1)
                            field = field.strip()
                            value = value.strip().strip('"\'')

                            # Special handling for number fields
                            if field == 'matchMax':
                                try:
                                    value = int(value)
                                except ValueError:
                                    pass

                            current_match_item[field] = value

                        # Exit matchSets when we hit a new top-level field (not indented)
                        elif not line.startswith(' '):
                            # Add the last item
                            if current_match_item:
                                if in_source:
                                    match_sets['source'].append(current_match_item)
                                else:
                                    match_sets['target'].append(current_match_item)
                                current_match_item = None

                            # Store the full matchSets in the question dict
                            question_dict['matchSets'] = match_sets
                            in_match_sets = False
                            in_source = False
                            in_target = False
                            continue  # Process this line as a regular field

                    # Detect correctPairs section
                    elif line.strip() == 'correctPairs:':
                        in_correct_pairs = True
                        i += 1
                        continue

                    # Process correctPairs items
                    elif in_correct_pairs:
                        if line.strip().startswith('- - '):
                            # Start a new pair
                            current_pair = [line.strip()[4:].strip().strip('"\'')]
                        elif line.strip().startswith('  - ') and current_pair:
                            # Complete the pair and add it
                            current_pair.append(line.strip()[4:].strip().strip('"\''))
                            correct_pairs.append(current_pair)
                            current_pair = []
                        # Exit correctPairs when we hit a non-indented line
                        elif not line.startswith(' '):
                            question_dict['correctPairs'] = correct_pairs
                            in_correct_pairs = False
                            continue  # Process this line as a regular field

                # Handle FIB-type questions specifically
                elif question_dict.get('type') == 'fib':
                    # Detect correctAnswers section
                    if line.strip() == 'correctAnswers:':
                        in_fib_answers = True
                        fib_answers = []
                        current_fib_answer = []  # Initialize as empty list instead of None
                        i += 1
                        continue

                    # Process correctAnswers items
                    elif in_fib_answers:
                        # Handle a standalone "- -" that introduces a new answer group but doesn't contain an answer
                        if line.strip() == '- -':
                            # If we have answers for the current blank, add them to the list and start a new group
                            if current_fib_answer:
                                fib_answers.append(current_fib_answer)
                                current_fib_answer = []
                            i += 1
                            continue

                        # Handle "- - answer" format (first answer on same line as group marker)
                        elif line.strip().startswith('- - ') and len(line.strip()) > 4:
                            # If we have answers for the current blank, add them to the list
                            if current_fib_answer:
                                fib_answers.append(current_fib_answer)

                            # Start a new answer group with this answer
                            answer = line.strip()[4:].strip().strip('"\'')
                            current_fib_answer = [answer]

                        # Handle individual answers with "  - answer" format
                        elif line.strip().startswith('  - '):
                            # Extract the answer and add it to the current group
                            answer = line.strip()[4:].strip().strip('"\'')
                            current_fib_answer.append(answer)

                        # Exit correctAnswers when we hit a non-indented line
                        elif not line.startswith(' '):
                            # Add the last answer group if it exists
                            if current_fib_answer:
                                fib_answers.append(current_fib_answer)

                            question_dict['correctAnswers'] = fib_answers
                            in_fib_answers = False
                            current_fib_answer = []
                            continue  # Process this line as a regular field

                # Handle order-type questions specifically
                elif question_dict.get('type') == 'order':
                    # Detect correctSequence section
                    if line.strip() == 'correctSequence:':
                        in_correct_sequence = True
                        i += 1
                        continue

                    # Process correctSequence items
                    elif in_correct_sequence:
                        if line.strip().startswith('- '):
                            # Add item to sequence
                            item = line.strip()[2:].strip().strip('"\'')
                            correct_sequence.append(item)

                        # Exit correctSequence when we hit a non-indented line
                        elif not line.startswith(' '):
                            question_dict['correctSequence'] = correct_sequence
                            in_correct_sequence = False
                            continue  # Process this line as a regular field

                # Handle regular choices section (for mcq, mrq, etc.)
                if line.strip() == 'choices:':
                    in_choices = True
                    i += 1
                    continue

                # Process choice items
                if in_choices:
                    # New choice starts with "- identifier:"
                    if line.strip().startswith('- identifier:'):
                        # Store previous choice if exists
                        if current_choice:
                            choices.append(current_choice)

                        # Start new choice
                        current_choice = {'identifier': line.strip()[13:].strip().strip('"\'') }

                    # Process choice fields (text, correct)
                    elif current_choice and ':' in line:
                        field, value = line.strip().split(':', 1)
                        field = field.strip()
                        value = value.strip().strip('"\'')

                        # Special handling for text field which might have LaTeX
                        if field == 'text':
                            # If value starts with triple quotes, extract until end triple quotes
                            if value.startswith('"""') or value.startswith("'''"):
                                quote_type = value[:3]
                                if quote_type in value[3:]:
                                    # Single line with triple quotes
                                    end_quote = value.rindex(quote_type)
                                    value = value[3:end_quote]
                                else:
                                    # Multi-line triple quoted string
                                    text_parts = [value[3:]]
                                    j = i + 1
                                    while j < len(lines):
                                        if quote_type in lines[j]:
                                            end_quote = lines[j].rindex(quote_type)
                                            text_parts.append(lines[j][:end_quote])
                                            i = j
                                            break
                                        else:
                                            text_parts.append(lines[j])
                                        j += 1
                                    value = ' '.join(text_parts)

                            current_choice[field] = value
                        elif field == 'correct':
                            current_choice[field] = value.lower() == 'true'
                        else:
                            current_choice[field] = value

                    # Check if choices section ends
                    elif not line.startswith(' '):
                        # Add the current choice and end choices section
                        if current_choice:
                            choices.append(current_choice)
                            current_choice = None

                        question_dict['choices'] = choices
                        in_choices = False
                        continue  # Process this line again as a regular field

                # Process regular fields
                if ':' in line and not in_choices and not in_match_sets and not in_correct_pairs and not in_correct_sequence and not in_fib_answers:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()

                    # Strip quotes if present
                    if (value.startswith('"') and value.endswith('"')) or \
                    (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    elif (value.startswith('"""') and value.endswith('"""')) or \
                        (value.startswith("'''") and value.endswith("'''")):
                        value = value[3:-3]

                    # Convert boolean values
                    if value.lower() == 'true':
                        value = True
                    elif value.lower() == 'false':
                        value = False

                    question_dict[key] = value

                i += 1

            # Don't forget to add the last choice if still in choices section
            if in_choices and current_choice:
                choices.append(current_choice)
                question_dict['choices'] = choices

            # Handle final items for match questions
            if question_dict.get('type') == 'match':
                # Add the last match item if we're still in matchSets
                if in_match_sets and current_match_item:
                    if in_source:
                        match_sets['source'].append(current_match_item)
                    elif in_target:
                        match_sets['target'].append(current_match_item)
                    question_dict['matchSets'] = match_sets

                # Make sure we store correctPairs if we're at the end of the block
                if in_correct_pairs:
                    question_dict['correctPairs'] = correct_pairs

                # Generate default correctPairs if not present
                if 'matchSets' in question_dict and 'correctPairs' not in question_dict:
                    # Create default pairs by matching source with target by index order
                    # Only if both source and target exist with items
                    if ('source' in question_dict['matchSets'] and
                        'target' in question_dict['matchSets'] and
                        question_dict['matchSets']['source'] and
                        question_dict['matchSets']['target']):

                        generated_pairs = []
                        source_choices = question_dict['matchSets']['source']
                        target_choices = question_dict['matchSets']['target']

                        # Match up to the minimum number of choices available in either set
                        pair_count = min(len(source_choices), len(target_choices))
                        for i in range(pair_count):
                            source_id = source_choices[i].get('identifier')
                            target_id = target_choices[i].get('identifier')
                            if source_id and target_id:
                                generated_pairs.append([source_id, target_id])

                        question_dict['correctPairs'] = generated_pairs

            # Handle final items for order questions
            if question_dict.get('type') == 'order' and in_correct_sequence:
                question_dict['correctSequence'] = correct_sequence

            # Handle final items for FIB questions
            if question_dict.get('type') == 'fib' and in_fib_answers and current_fib_answer:
                fib_answers.append(current_fib_answer)
                question_dict['correctAnswers'] = fib_answers

            questions.append(question_dict)

        return questions

    def _format_question(self, question: Dict, template: QuestionTemplate) -> str:
        """Format question using appropriate template"""
        try:
            if template.type == 'fib':
                return self._format_fib(question, template.xml_content)
            elif template.type == 'mcq':
                return self._format_mcq(question, template.xml_content)
            elif template.type == 'mrq':
                return self._format_mrq(question, template.xml_content)
            elif template.type == 'tf':
                return self._format_tf(question, template.xml_content)
            elif template.type == 'match':
                return self._format_match(question, template.xml_content)
            elif template.type == 'order':
                return self._format_order(question, template.xml_content)
            elif template.type == 'essay':
                return self._format_essay(question, template.xml_content)
            else:
                raise ValueError(f"Formatting not implemented for type: {template.type}")

        except Exception as e:
            # Include question identifier in error message for better debugging
            identifier = question.get('identifier', 'unknown')
            raise ValueError(f"Error formatting question {identifier} of type {template.type}: {str(e)}")

    def _format_mcq(self, question: Dict, template: str) -> str:
        """Format Multiple Choice question according to QTI v2.2 specs with support for images"""
        # Create a mapping of choices by identifier
        choice_map = {choice['identifier']: self._escape_xml_chars(choice.get('text', ''))
                    for choice in question.get('choices', [])}

        # Get correct answer - ensure it's not wrapped in quotes
        correct_answer = None
        for choice in question.get('choices', []):
            if choice.get('correct'):
                correct_answer = choice.get('identifier')
                break

        if not correct_answer:
            correct_answer = "A"  # Default if not found

        # Process question text
        question_text = self._escape_xml_chars(question.get('question_text', ''))

        # Process question image
        question_image = ''
        if 'question_image' in question and question['question_image']:
            img_html = question['question_image']
            import re

            # Extract image source
            src_match = re.search(r'src=["\'](.*?)["\']', img_html)
            if src_match:
                img_src = src_match.group(1)

                # Create a proper QTI-compatible image tag
                question_image = f'<p><img src="{img_src}" alt="Question Image" width="400"/></p>'

        # Build the final XML
        xml = template.format(
            identifier=question.get('identifier', ''),
            title=self._escape_xml_chars(question.get('title', '')),
            question_text=question_text,
            question_image=question_image,
            prompt=self._escape_xml_chars(question.get('prompt', '')),
            correct_answer=correct_answer,  # Ensure this is just the ID, not quoted
            choice_a=choice_map.get('A', ''),
            choice_b=choice_map.get('B', ''),
            choice_c=choice_map.get('C', ''),
            choice_d=choice_map.get('D', ''),
            choice_a_image='',
            choice_b_image='',
            choice_c_image='',
            choice_d_image=''
        )

        return xml

    def _format_mrq(self, question: Dict, template: str) -> str:
        """Format Multiple Response question according to QTI v2.2 specs"""
        # Create a mapping of choices by identifier
        choice_map = {choice['identifier']: choice['text'] for choice in question['choices']}

        # Get correct answers
        correct_answers = '\n            '.join(
            f'<value>{choice["identifier"]}</value>'
            for choice in question['choices']
            if choice.get('correct', False)
        )

        return template.format(
            identifier=question['identifier'],
            title=question['title'],
            prompt=question['prompt'],
            correct_answers=correct_answers,
            choice_a=choice_map.get('A', ''),
            choice_b=choice_map.get('B', ''),
            choice_c=choice_map.get('C', ''),
            choice_d=choice_map.get('D', ''),
            shuffle=str(question.get('shuffle', True)).lower(),
            max_choices=str(question.get('maxChoices', 0))
        )

    def _format_tf(self, question: Dict, template: str) -> str:
        """Format True/False question"""
        correct = str(question.get('correct', True)).lower()
        return template.format(
            identifier=question['identifier'],
            title=question['title'],
            prompt=question['prompt'],
            correct_answer=correct
        )

    def _format_fib(self, question: Dict, template: str) -> str:
        """Format Fill in Blank question"""
        # Get correct answers
        correct_answers = question.get('correctAnswers', [])

        # Format response declarations
        response_declarations = ''
        for i, answer_set in enumerate(correct_answers, 1):
            values_xml = '\n                '.join(
                f'<value>{self._escape_xml_chars(ans)}</value>'
                for ans in answer_set
            )
            response_declarations += f'''
    <responseDeclaration identifier="RESPONSE{i}" cardinality="single" baseType="string">
        <correctResponse>
            {values_xml}
        </correctResponse>
    </responseDeclaration>'''

        # Build prompt_with_interactions by replacing each blank marker with interaction
        prompt_text = question['prompt']
        for i in range(len(correct_answers)):
            interaction = f'<textEntryInteraction responseIdentifier="RESPONSE{i+1}" expectedLength="20"/>'
            prompt_text = prompt_text.replace('_', interaction, 1)
        prompt_with_interactions = prompt_text

        return template.format(
            identifier=question['identifier'],
            title=question['title'],
            response_declarations=response_declarations,
            prompt_with_interactions=prompt_with_interactions,
        )

    def _format_match(self, question: Dict, template: str) -> str:
        """Format Matching question"""
        match_sets = question.get('matchSets', {})
        source = match_sets.get('source', [])
        target = match_sets.get('target', [])

        # Format source choices
        source_xml = '\n                    '.join(
            f'<simpleAssociableChoice identifier="{item["identifier"]}" matchMax="1">{self._escape_xml_chars(item["text"])}</simpleAssociableChoice>'
            for item in source
        )

        # Format target choices
        target_xml = '\n                    '.join(
            f'<simpleAssociableChoice identifier="{item["identifier"]}" matchMax="1">{self._escape_xml_chars(item["text"])}</simpleAssociableChoice>'
            for item in target
        )

        # Format correct pairs
        correct_pairs = '\n            '.join(
            f'<value>{pair[0]} {pair[1]}</value>'
            for pair in question.get('correctPairs', [])
        )

        return template.format(
            identifier=question['identifier'],
            title=question['title'],
            prompt=question['prompt'],
            source_choices=source_xml,
            target_choices=target_xml,
            correct_pairs=correct_pairs
        )

    def _format_order(self, question: Dict, template: str) -> str:
        """Format Order question"""
        choices = question.get('choices', [])
        correct_sequence = question.get('correctSequence', [])

        # Format choices
        choices_xml = '\n                '.join(
            f'<simpleChoice identifier="{choice["identifier"]}">{self._escape_xml_chars(choice["text"])}</simpleChoice>'
            for choice in choices
        )

        # Format correct sequence
        sequence_xml = '\n            '.join(
            f'<value>{item}</value>'
            for item in correct_sequence
        )

        return template.format(
            identifier=question['identifier'],
            title=question['title'],
            prompt=question['prompt'],
            choices=choices_xml,
            correct_sequence=sequence_xml
        )

    def _format_essay(self, question: Dict, template: str) -> str:
        """Format Essay question"""
        return template.format(
            identifier=question['identifier'],
            title=question['title'],
            prompt=question['prompt'],
            expected_length=str(question.get('expectedLength', 500)),
            expected_lines=str(question.get('expectedLines', 5))
        )

    def _prettify(self, xml_string: str) -> str:
        """Return a pretty-printed XML string"""
        try:
            parsed = minidom.parseString(xml_string)
            return parsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
        except Exception:
            return xml_string

    def _validate_common(self, question: Dict) -> bool:
        """Validate common fields for all questions"""
        required = ['identifier', 'title', 'prompt']
        return all(field in question for field in required)

    def _validate_fib(self, question: Dict) -> bool:
        """Validate Fill in Blank question"""
        return 'correctAnswers' in question

    def _validate_choices(self, question: Dict, qtype: str) -> bool:
        """Validate choice-based questions (MCQ/MRQ)"""
        if 'choices' not in question:
            return False
        choices = question['choices']
        if not isinstance(choices, list) or len(choices) < 2:
            return False
        # Check if at least one choice is correct
        return any(c.get('correct', False) for c in choices)

    def _validate_tf(self, question: Dict) -> bool:
        """Validate True/False question"""
        return 'correct' in question

    def _validate_match(self, question: Dict) -> bool:
        """Validate Matching question"""
        if 'matchSets' not in question:
            return False
        match_sets = question['matchSets']
        return 'source' in match_sets and 'target' in match_sets

    def _validate_order(self, question: Dict) -> bool:
        """Validate Order question"""
        return 'correctSequence' in question and 'choices' in question

    def _validate_essay(self, question: Dict) -> bool:
        """Validate Essay question"""
        return True  # Essay questions only need common fields
