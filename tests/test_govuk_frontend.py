import pytest

from dmcontent.questions import Question

from dmcontent.govuk_frontend import (
    from_question,
    govuk_character_count,
    govuk_input,
    govuk_checkboxes,
    govuk_radios,
    dm_list_input,
    govuk_fieldset,
    govuk_label,
    _params,
)


class TestTextInput:
    @pytest.fixture
    def question(self):
        return Question(
            {
                "id": "title",
                "name": "Title",
                "question": "What you want to call your requirements",
                "question_advice": "This will help you to refer to your requirements",
                "hint": "100 characters maximum",
                "type": "text",
            }
        )

    def test_govuk_input(self, question, snapshot):
        assert govuk_input(question) == snapshot

    def test_from_question(self, question, snapshot):
        form = from_question(question)

        assert form["macro_name"] == "govukInput"
        assert form["params"] == snapshot

    def test_from_question_with_is_page_heading_false(self, question, snapshot):
        form = from_question(question, is_page_heading=False)

        assert form["macro_name"] == "govukInput"
        assert form["params"] == snapshot

    def test_with_data(self, question, snapshot):
        data = {
            "title": "Find an individual specialist",
        }

        assert from_question(question, data) == snapshot

    def test_with_errors(self, question, snapshot):
        errors = {
            "title": {
                "input_name": "title",
                "href": "#input-title",
                "question": "What you want to call your requirements",
                "message": "Enter a title.",
            }
        }

        assert from_question(question, errors=errors) == snapshot


class TestRadios:
    @pytest.fixture
    def question(self):
        return Question(
            {
                "id": "yesOrNo",
                "name": "Yes or no",
                "question": "Yes or no?",
                "type": "radios",
                "options": [
                    {"label": "Yes", "value": "yes"},
                    {"label": "No", "value": "no"},
                ],
            }
        )

    def test_govuk_radios(self, question, snapshot):
        assert govuk_radios(question) == snapshot

    def test_govuk_radios_id_prefix(self, question):
        params = govuk_radios(question)

        assert "id" not in params
        assert params["idPrefix"] == "input-yesOrNo"

    def test_govuk_radios_options_with_descriptions(self, question):
        question.options = [
            {"label": "Yes", "value": "yes", "description": "Affirmative."},
            {"label": "No", "value": "no", "description": "Negative."},
        ]

        assert govuk_radios(question)["items"] == [
            {"text": "Yes", "value": "yes", "hint": {"text": "Affirmative."}},
            {"text": "No", "value": "no", "hint": {"text": "Negative."}},
        ]

    def test_from_question(self, question, snapshot):
        form = from_question(question)

        assert "fieldset" in form
        assert form["macro_name"] == "govukRadios"
        assert form["params"] == snapshot

    def test_from_question_with_is_page_heading_false(self, question, snapshot):
        fieldset = from_question(question)["fieldset"]

        assert "isPageHeading" not in fieldset or fieldset["isPageHeading"] is False
        assert fieldset == snapshot

    def test_from_question_with_data(self, question, snapshot):
        data = {"yesOrNo": "yes"}

        form = from_question(question, data)

        assert "value" not in form["params"]
        assert form["params"]["items"][0]["checked"] is True
        assert "checked" not in form["params"]["items"][1]
        assert form == snapshot

    def test_from_question_with_errors(self, question, snapshot):
        errors = {
            "yesOrNo": {
                "input_name": "title",
                "href": "#input-yesOrNo",
                "question": "Yes or no?",
                "message": "Select yes or no,",
            }
        }

        form = from_question(question, errors=errors)

        assert "errorMessage" in form["params"]
        assert form == snapshot


class TestCheckboxes:
    @pytest.fixture
    def question(self):
        return Question(
            {
                "id": "oneAndAnother",
                "name": "One and another",
                "question": "Choose one and/or another",
                "type": "checkboxes",
                "options": [
                    {"label": "One", "value": "one"},
                    {"label": "Another", "value": "another"},
                ],
            }
        )

    def test_govuk_checkboxes(self, question, snapshot):
        assert govuk_checkboxes(question) == snapshot

    def test_govuk_checkboxes_id_prefix(self, question):
        params = govuk_checkboxes(question)

        assert "id" not in params
        assert params["idPrefix"] == "input-oneAndAnother"

    def test_govuk_checkbox_options_with_descriptions(self, question):
        question.options = [
            {"label": "One", "value": "one", "description": "This is the first thing."},
            {"label": "Another", "value": "another", "description": "This is another thing."},
        ]

        assert govuk_checkboxes(question)["items"] == [
            {"text": "One", "value": "one", "hint": {"text": "This is the first thing."}},
            {"text": "Another", "value": "another", "hint": {"text": "This is another thing."}},
        ]

    def test_from_question(self, question, snapshot):
        form = from_question(question)

        assert "fieldset" in form
        assert form["macro_name"] == "govukCheckboxes"
        assert form["params"] == snapshot

    def test_from_question_with_is_page_heading_false(self, question, snapshot):
        fieldset = from_question(question)["fieldset"]

        assert "isPageHeading" not in fieldset or fieldset["isPageHeading"] is False
        assert fieldset == snapshot

    def test_from_question_with_data(self, question, snapshot):
        data = {"oneAndAnother": "one"}

        form = from_question(question, data)

        assert "value" not in form["params"]
        assert form["params"]["items"][0]["checked"] is True

        data = {"oneAndAnother": ["one", "another"]}
        form = from_question(question, data)
        assert form["params"]["items"][0]["checked"] is True
        assert form["params"]["items"][1]["checked"] is True
        assert form == snapshot

    def test_from_question_with_errors(self, question, snapshot):
        errors = {
            "oneAndAnother": {
                "input_name": "title",
                "href": "#input-oneAndAnother",
                "question": "Select one and/or another.",
                "message": "Select one or another",
            }
        }

        form = from_question(question, errors=errors)

        assert "errorMessage" in form["params"]
        assert form == snapshot


class TestDmListInput:
    @pytest.fixture
    def question(self):
        return Question(
            {
                "id": "culturalFitCriteria",
                "name": "Title",
                "question": "Cultural fit criteria",
                "question_advice": (
                    '<p class="govuk-body">Cultural fit is about how well you and the specialist work together</p>'
                ),
                "hint": "Enter at least one criteria",
                "number_of_items": 5,
                "type": "list",
            }
        )

    def test_dm_list_input(self, question, snapshot):
        assert dm_list_input(question) == snapshot

    def test_from_question(self, question, snapshot):
        form = from_question(question)

        assert form["macro_name"] == "dmListInput"
        assert form["params"] == snapshot

    def test_from_question_with_is_page_heading_false(self, question, snapshot):
        form = from_question(question, is_page_heading=False)

        assert form["macro_name"] == "dmListInput"
        assert form["params"] == snapshot

    def test_with_data(self, question, snapshot):
        data = {
            "culturalFitCriteria": ["Must know how to make tea", "Must believe unicorns"],
        }

        assert from_question(question, data) == snapshot

    def test_with_errors(self, question, snapshot):
        errors = {
            "culturalFitCriteria": {
                "input_name": "culturalFitCriteria",
                "href": "#input-culturalFitCriteria",
                "question": "Cultural fit criteria",
                "message": "Enter at least one criterion.",
            }
        }

        assert from_question(question, errors=errors) == snapshot


class TestGovukCharacterCount:
    @pytest.fixture
    def question(self):
        return Question(
            {
                "id": "description",
                "name": "Description",
                "question": "Describe the specialist's role",
                "question_advice": "Describe the team the specialist will be working with on this project.",
                "type": "textbox_large",
                "hint": "Enter at least one word, and no more than 100",
                "max_length_in_words": 100
            }
        )

    @pytest.fixture
    def question_without_word_count(self):
        return Question(
            {
                "id": "description",
                "name": "Description",
                "question": "Describe the specialist's role",
                "question_advice": "Describe the team the specialist will be working with on this project.",
                "type": "textbox_large"
            }
        )

    def test_govuk_character_count(self, question, snapshot):
        assert govuk_character_count(question) == snapshot

    def test_from_question(self, question, snapshot):
        form = from_question(question)

        assert form["macro_name"] == "govukCharacterCount"
        assert form["params"] == snapshot

    def test_question_with_no_max_word_length_does_not_have_maxwords_in_params(self, question_without_word_count):
        assert "maxwords" not in govuk_character_count(question_without_word_count)

    def test_with_data(self, question, snapshot):
        data = {
            "description": "The specialist must know how to make tea and work well with unicorns.",
        }

        assert from_question(question, data) == snapshot

    def test_with_errors(self, question, snapshot):
        errors = {
            "description": {
                "input_name": "description",
                "href": "#input-description",
                "question": "Description",
                "message": "Enter a description of the specialist's role.",
            }
        }

        assert from_question(question, errors=errors) == snapshot


class TestGovukLabel:
    @pytest.fixture
    def question(self):
        return Question({"id": "question", "question": "Yes or no?"})

    def test_govuk_label(self, question):
        assert govuk_label(question) == {
            "classes": "govuk-label--l",
            "isPageHeading": True,
            "for": "input-question",
            "text": "Yes or no?",
        }

    def test_is_page_heading_false_removes_classes_and_ispageheading(self, question):
        assert govuk_label(question, is_page_heading=False) == {
            "for": "input-question",
            "text": "Yes or no?",
        }

    def test_optional_question_has_optional_in_label_text(self, question):
        question.optional = True

        assert govuk_label(question)["text"] == "Yes or no? (optional)"

    def test_not_optional_question_does_not_have_optional_in_label_text(self, question):
        question.optional = False

        assert govuk_label(question)["text"] == "Yes or no?"


class TestGovukFieldset:
    @pytest.fixture
    def question(self):
        return Question({"id": "question", "question": "Enter your criteria"})

    def test_govuk_fieldset(self, question):
        assert govuk_fieldset(question) == {
            "legend": {
                "text": "Enter your criteria",
                "isPageHeading": True,
                "classes": "govuk-fieldset__legend--l"
            }
        }

    def test_is_page_heading_false_removes_classes_and_ispageheading(self, question):
        assert govuk_fieldset(question, is_page_heading=False) == {
            "legend": {
                "text": "Enter your criteria"
            }
        }

    def test_optional_question_has_optional_in_legend_text(self, question):
        question.type = "list"
        question.optional = True

        assert govuk_fieldset(question)["legend"]["text"] == "Enter your criteria (optional)"

    def test_not_optional_question_does_not_have_optional_in_legend_text(self, question):
        question.type = "list"
        question.optional = False

        assert govuk_fieldset(question)["legend"]["text"] == "Enter your criteria"


class TestParams:
    @pytest.fixture
    def question(self):
        return Question({"id": "question", "question": "Yes or no?"})

    def test__params(self, question):
        assert _params(question) == {
            "id": "input-question",
            "name": "question",
        }

    def test_hint(self, question):
        question.hint = "Answer yes or no"

        assert _params(question)["hint"] == {
            "text": "Answer yes or no",
        }

    def test_value_is_present_if_question_answer_is_in_data(self, question):
        data = {"question": "Yes"}

        assert _params(question, data)["value"] == "Yes"

    def test_value_is_not_present_if_question_answer_is_not_in_data(self, question):
        data = {"another_question": "Maybe"}

        assert "value" not in _params(question, data)

    def test_value_is_not_present_if_question_answer_is_none(self, question):
        data = {"another_question": None}

        assert "value" not in _params(question, data)

    def test_error_message_is_present_if_question_error_is_in_errors(self, question):
        errors = {
            "question": {
                "input_name": "question",
                "href": "#input-question",
                "question": "Yes or no?",
                "message": "Answer yes or no.",
            }
        }

        assert _params(question, errors=errors)["errorMessage"] == {
            "text": "Answer yes or no."
        }

    def test_error_message_is_not_present_if_question_error_is_not_in_errors(
        self, question
    ):
        errors = {
            "another_question": {
                "input_name": "another-question",
                "href": "#input-another-question",
                "question": "Are you sure?",
                "message": "Enter whether you are sure or not.",
            }
        }

        assert "errorMessage" not in _params(question, errors=errors)

    def test_error_message_is_not_present_if_question_error_is_none(self, question):
        errors = {"another_question": None}

        assert "errorMessage" not in _params(question, errors=errors)

    def test_value_and_error_message(self, question):
        data = {"question": "Definitely"}
        errors = {
            "question": {
                "input_name": "question",
                "href": "#input-question",
                "question": "Yes or no?",
                "message": "Answer yes or no only.",
            }
        }

        params = _params(question, data, errors)
        assert params["value"] == "Definitely"
        assert params["errorMessage"]["text"] == "Answer yes or no only."