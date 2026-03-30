"""
Combined Questions Utility

Handles storage, organization, and packaging of QTI questions from multiple sources.
Adapted from Streamlit version - removed UI dependencies, kept core business logic.
"""

import logging
import zipfile
import uuid
import xml.etree.ElementTree as ET
from io import BytesIO
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re


INVALID_MEDIA_FILENAME_PATTERN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_media_filename(filename: str) -> Optional[str]:
    """
    Normalize media filename to basename-only and reject unsafe names.

    Returns:
        Sanitized basename if valid, otherwise None.
    """
    raw_name = str(filename).strip()
    if not raw_name:
        return None

    normalized = raw_name.replace("\\", "/")
    basename = normalized.rsplit("/", 1)[-1].strip()

    if not basename or basename in {".", ".."}:
        return None

    if INVALID_MEDIA_FILENAME_PATTERN.search(basename):
        return None

    # Avoid ambiguous trailing names that are invalid on common filesystems.
    if basename.endswith(".") or basename.endswith(" "):
        return None

    return basename


def store_questions(questions: List[str], media_files: Optional[Dict[str, bytes]] = None,
                   source_type: str = "text") -> Dict:
    """
    Store generated questions with proper organization.

    This function returns a dictionary structure for storing in Reflex state.
    Unlike Streamlit version, it doesn't modify session_state directly.

    Parameters:
        questions (list): List of XML question strings
        media_files (dict): Dictionary of media files {filename: file_content}
        source_type (str): Either "text" or "image" to indicate the source

    Returns:
        dict: Updated questions dictionary structure
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if source_type == "text":
        return {
            "questions": questions,
            "timestamp": timestamp
        }
    elif source_type == "image":
        return {
            "questions": questions,
            "media_files": media_files or {},
            "timestamp": timestamp
        }
    else:
        logging.warning(f"Unknown source_type: {source_type}. Defaulting to text format.")
        return {
            "questions": questions,
            "timestamp": timestamp
        }


def get_question_count_summary(all_questions: List[str]) -> Dict[str, int]:
    """
    Get a summary of question counts by type from provided questions list.

    Modified from Streamlit version - takes questions as parameter instead of
    reading from session_state.

    Parameters:
        all_questions (list): List of XML question strings

    Returns:
        dict: Dictionary with question types as keys and counts as values
    """
    question_types = {}

    # Extract question types from XML
    for xml in all_questions:
        try:
            root = ET.fromstring(xml)
            # Find interaction elements (QTI namespace)
            interactions = root.findall(".//{http://www.imsglobal.org/xsd/imsqti_v2p2}*")
            interaction_elem = next((elem for elem in interactions if 'Interaction' in elem.tag), None)

            if interaction_elem is not None:
                q_type = interaction_elem.tag.split('}')[-1]
                readable_type = q_type.replace('Interaction', '')
                question_types[readable_type] = question_types.get(readable_type, 0) + 1
        except ET.ParseError as e:
            logging.error(f"Error parsing question XML: {e}")
            continue
        except Exception as e:
            logging.error(f"Unexpected error processing question: {e}")
            continue

    return question_types


def create_package(test_title: str = "TeacherAIde Assessment",
                  questions: Optional[List[str]] = None,
                  media_files: Optional[Dict[str, bytes]] = None,
                  question_types: str = 'all',
                  templates_dir: str = "app/templates") -> Optional[bytes]:
    """
    Create a QTI v2.2 package with questions and media files.

    Modified from Streamlit version:
    - Removed session_state dependency
    - Takes all data as parameters
    - Returns bytes directly (no st.error calls)
    - Uses 'app/templates' as default templates_dir for Reflex

    Parameters:
        test_title (str): Title for the assessment
        questions (list): Optional - List of XML question strings to include directly
        media_files (dict): Optional - Dictionary of media files {filename: file_content}
        question_types (str): Which types to include ('text', 'image', or 'all')
        templates_dir (str): Directory containing QTI templates

    Returns:
        bytes: Package data or None if no questions available
    """
    package_bytes, _warnings = create_package_with_warnings(
        test_title=test_title,
        questions=questions,
        media_files=media_files,
        question_types=question_types,
        templates_dir=templates_dir,
    )
    return package_bytes


def create_package_with_warnings(test_title: str = "TeacherAIde Assessment",
                                 questions: Optional[List[str]] = None,
                                 media_files: Optional[Dict[str, bytes]] = None,
                                 question_types: str = 'all',
                                 templates_dir: str = "app/templates") -> Tuple[Optional[bytes], List[str]]:
    """
    Create a QTI package and return non-fatal packaging warnings.

    Returns:
        tuple: (package_bytes_or_none, warning_messages)
    """
    warnings: List[str] = []

    def add_warning(message: str):
        warnings.append(message)
        logging.warning(message)

    # Initialize questions and media files
    final_questions = [] if questions is None else list(questions)
    final_media_files = {} if media_files is None else dict(media_files)

    # Enforce basename-only media handling and reject unsafe filenames.
    sanitized_media_files: Dict[str, bytes] = {}
    for original_name, content in final_media_files.items():
        safe_name = sanitize_media_filename(original_name)
        if safe_name is None:
            add_warning(f"Skipped unsafe media filename during packaging: {original_name!r}.")
            continue
        if safe_name in sanitized_media_files:
            add_warning(
                (
                    "Skipped duplicate media filename after sanitization: "
                    f"{original_name!r} -> {safe_name!r}."
                )
            )
            continue
        sanitized_media_files[safe_name] = content

    # If no questions available, return None
    if not final_questions:
        add_warning("No questions available to create a package.")
        return None, warnings

    # Use the YAMLtoQTIConverter to access templates and helper methods
    try:
        from app.utils.yaml_converter import YAMLtoQTIConverter
        converter = YAMLtoQTIConverter(templates_dir=templates_dir)
    except ImportError as e:
        logging.error(f"Failed to import YAMLtoQTIConverter: {e}")
        warnings.append(f"Failed to import YAML converter: {str(e)}")
        return None, warnings
    except Exception as e:
        logging.error(f"Failed to initialize YAMLtoQTIConverter: {e}")
        warnings.append(f"Failed to initialize YAML converter: {str(e)}")
        return None, warnings

    # Create the package
    try:
        zip_buffer = BytesIO()
        
        # First pass: deduplicate question identifiers to avoid zip filename conflicts
        seen_ids = {}  # Maps original_id -> (new_id, count)
        deduplicated_questions = []
        
        for question in final_questions:
            root = ET.fromstring(question)
            original_id = root.get('identifier')
            
            if original_id in seen_ids:
                # Increment count and create unique identifier
                seen_ids[original_id] += 1
                new_id = f"{original_id}_{seen_ids[original_id]}"
                # Update the identifier in the XML
                root.set('identifier', new_id)
                question = ET.tostring(root, encoding='unicode')
                logging.info(f"Renamed duplicate identifier {original_id} to {new_id}")
            else:
                seen_ids[original_id] = 0
            
            deduplicated_questions.append(question)
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add manifest
            manifest_xml = converter.package_templates['manifest.xml'].format(
                manifest_id=f"MANIFEST-{uuid.uuid4()}",
                dependencies=converter._generate_dependencies(deduplicated_questions),
                resources=converter._generate_resources(deduplicated_questions)
            )
            zip_file.writestr('imsmanifest.xml', manifest_xml)

            # Add assessment test
            test_xml = converter.package_templates['assessment.xml'].format(
                test_id=f"test-{uuid.uuid4()}",
                test_title=test_title,
                item_refs=converter._generate_item_refs(deduplicated_questions)
            )
            zip_file.writestr('assessmentTest.xml', test_xml)

            # Add individual questions
            for question in deduplicated_questions:
                root = ET.fromstring(question)
                question_id = root.get('identifier')
                zip_file.writestr(f"{question_id}.xml", question)

            # Add media files if provided
            if sanitized_media_files:
                # Ensure media directory exists in the zip
                zip_file.writestr('media/.placeholder', '')

                for filename, content in sanitized_media_files.items():
                    # Make sure the content is bytes, not string
                    if isinstance(content, str):
                        content = content.encode('utf-8')

                    # Store the media file
                    try:
                        zip_file.writestr(f"media/{filename}", content)
                    except Exception as e:
                        add_warning(f"Failed to include media file {filename}: {str(e)}")

        zip_buffer.seek(0)
        return zip_buffer.getvalue(), warnings

    except Exception as e:
        logging.error(f"Error creating QTI package: {str(e)}")
        warnings.append(f"Error creating QTI package: {str(e)}")
        return None, warnings


def combine_questions_from_state(text_questions_data: Optional[Dict] = None,
                                 image_questions_data: Optional[Dict] = None,
                                 question_types: str = 'all') -> Tuple[List[str], Dict[str, bytes]]:
    """
    Helper function to combine questions from Reflex state data.

    This is a NEW function specific to Reflex to help merge text and image questions.

    Parameters:
        text_questions_data (dict): Text questions data structure from state
        image_questions_data (dict): Image questions data structure from state
        question_types (str): Which types to include ('text', 'image', or 'all')

    Returns:
        tuple: (combined_questions_list, combined_media_files_dict)
    """
    final_questions = []
    final_media_files = {}

    # Add text questions if requested
    if question_types in ['text', 'all'] and text_questions_data:
        text_qs = text_questions_data.get('questions', [])
        final_questions.extend(text_qs)

    # Add image questions and media if requested
    if question_types in ['image', 'all'] and image_questions_data:
        image_qs = image_questions_data.get('questions', [])
        final_questions.extend(image_qs)

        # Get media files
        media = image_questions_data.get('media_files', {})
        final_media_files.update(media)

    return final_questions, final_media_files
