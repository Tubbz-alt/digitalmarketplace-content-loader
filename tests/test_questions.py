# coding=utf-8
from collections import OrderedDict

import pytest

from werkzeug.datastructures import OrderedMultiDict
from markupsafe import Markup
from dmcontent.content_loader import ContentQuestion
from dmcontent.utils import TemplateField
from dmcontent import ContentTemplateError


class QuestionTest(object):
    default_context = {}

    def context(self, context=None):
        """
        Update the provided context (if any) with the default context for this test.
        Override default_context when testing question types that must have additional
        context injected in the 'filter' call.
        """
        return dict(context or {}, **self.default_context)

    def test_get_question(self):
        question = self.question()
        assert question.get_question('example') == question

    def test_get_question_unknown_id(self):
        question = self.question()
        assert question.get_question('other') is None

    def test_get_data_unknown_key(self):
        assert self.question().get_data({'other': 'other value'}) == {}

    def test_required_form_fields_optional_question(self):
        assert self.question(optional=True).required_form_fields == []

    def test_get_question_ids_by_unknown_type(self):
        assert self.question().get_question_ids(type='other') == []

    def test_label_name(self):
        assert self.question(name='name').label == 'name'

    def test_label_question(self):
        assert self.question(question='question').label == 'question'

    def test_label_name_and_question(self):
        assert self.question(name='name', question='question').label == 'name'

    def test_question_repr(self):
        assert 'data=' in repr(self.question())

    def test_question_filter_without_dependencies(self):
        question = self.question()
        assert question.filter(self.context()) is not None
        assert question.filter(self.context()) is not question

    def test_question_filter_with_dependencies_that_match(self):
        question = self.question(depends=[{"on": "lot", "being": ["lot-1"]}])
        assert question.filter(self.context({"lot": "lot-1"})) is not None
        assert question.filter(self.context({"lot": "lot-1"})) is not question

    def test_question_filter_with_dependencies_that_are_not_matched(self):
        question = self.question(depends=[{"on": "lot", "being": ["lot-1"]}])
        assert question.filter(self.context({"lot": "lot-2"})) is None

    def test_question_without_template_tags_are_unchanged(self):
        question = self.question(
            name=TemplateField("Name"),
            question=TemplateField("Question"),
            hint=TemplateField("Hint"),
            question_advice=TemplateField("Advice")
        ).filter(self.context())

        assert question.name == "Name"
        assert question.question == "Question"
        assert question.hint == "Hint"
        assert question.question_advice == "Advice"

    def test_question_fields_are_templated(self):
        question = self.question(
            name=TemplateField("Name {{ name }}"),
            question=TemplateField("Question {{ question }}"),
            hint=TemplateField("Hint {{ hint }}"),
            question_advice=TemplateField("Advice {{ advice }}")
        ).filter(self.context({
            "name": "zero",
            "question": "one",
            "hint": "two",
            "advice": "three"
        }))

        assert question.name == "Name zero"
        assert question.question == "Question one"
        assert question.hint == "Hint two"
        assert question.question_advice == "Advice three"

        assert question.get_source('name') == "Name {{ name }}"
        assert question.get_source('question') == "Question {{ question }}"

    def test_question_fields_are_templated_on_access_if_filter_wasnt_called(self):
        question = self.question(
            name=TemplateField("Name {{ name }}"),
            question=TemplateField("Question"),
        )

        with pytest.raises(ContentTemplateError):
            question.name

        assert question.question == "Question"

    def test_question_options_descriptions_render_template_fields(self):
        """If the question has an options field, check that all TEMPLATE_OPTIONS_FIELDS are correctly rendered from
        TemplateFields by passing in markup and ensuring they turn into Markup objects.
        Does not recurse through options.options.[...] fields, e.g. for CheckboxTree"""
        question = self.question()

        if hasattr(question, 'options'):
            options = question['options']
            for subfield in question.TEMPLATE_OPTIONS_FIELDS:
                for option in options:
                    if subfield in option:
                        assert type(option[subfield]) == Markup


class TestText(QuestionTest):
    def question(self, **kwargs):
        data = {
            "id": "example",
            "type": "text"
        }
        data.update(kwargs)

        return ContentQuestion(data)

    def test_get_data(self):
        assert self.question().get_data({'example': 'value'}) == {'example': 'value'}

    def test_in(self):
        assert "compton" in self.question(compton=None)

    def test_not_in(self):
        assert "compton" not in self.question(carr=None)

    def test_get_data_with_assurance(self):
        assert self.question(assuranceApproach='2answers-type1').get_data(
            {'example': 'value1', 'example--assurance': 'assurance value'}
        ) == {'example': {'value': 'value1', 'assurance': 'assurance value'}}

    def test_get_data_with_assurance_unknown_key(self):
        assert self.question(assuranceApproach='2answers-type1').get_data({'other': 'value'}) == {'example': {}}

    def test_get_data_with_assurance_only(self):
        assert self.question(assuranceApproach='2answers-type1').get_data(
            {'example--assurance': 'assurance value'}
        ) == {'example': {'assurance': 'assurance value'}}

    def test_form_fields(self):
        assert self.question().form_fields == ['example']

    def test_required_form_fields(self):
        assert self.question().required_form_fields == ['example']

    def test_get_question_ids(self):
        assert self.question().get_question_ids() == ['example']

    def test_get_question_ids_by_type(self):
        assert self.question().get_question_ids(type='text') == ['example']


class TestBoolean(QuestionTest):
    def question(self, **kwargs):
        data = {
            "id": "example",
            "type": "boolean"
        }
        data.update(kwargs)

        return ContentQuestion(data)

    def test_followup_values(self):
        assert self.question(followup=OrderedDict(
            [("q2", [True, False]), ("q3", [True])])
        ).values_followup == {
            True: ["q2", "q3"],
            False: ["q2"]
        }


class TestPricing(QuestionTest):
    def question(self, **kwargs):
        data = {
            "id": "example",
            "type": "pricing",
            "fields": {
                "minimum_price": "priceMin",
                "maximum_price": "priceMax",
            }
        }
        data.update(kwargs)

        return ContentQuestion(data)

    def test_get_data(self):
        assert self.question().get_data(
            {'priceMin': '10', 'priceMax': '20'}
        ) == {'priceMin': '10', 'priceMax': '20'}

    def test_get_data_partial(self):
        assert self.question().get_data(
            {'priceMax': '20'}
        ) == {'priceMax': '20'}

    def test_form_fields(self):
        assert sorted(self.question().form_fields) == sorted(['priceMin', 'priceMax'])

    def test_required_form_fields(self):
        assert sorted(self.question().required_form_fields) == sorted(['priceMin', 'priceMax'])

    def test_required_form_fields_optional_fields(self):
        question = self.question(optional_fields=["minimum_price"])
        assert question.required_form_fields == ['priceMax']

    def test_get_question_ids(self):
        assert self.question().get_question_ids() == ['example']

    def test_get_question_ids_by_type(self):
        assert self.question().get_question_ids(type='pricing') == ['example']


class TestMultiquestion(QuestionTest):
    def question(self, **kwargs):
        data = {
            "id": "example",
            "type": "multiquestion",
            "questions": [
                {
                    "id": "example2",
                    "type": "text",
                },
                {
                    "id": "example3",
                    "type": "number",
                }
            ]
        }
        data.update(kwargs)

        return ContentQuestion(data)

    def test_get_question_nested(self):
        question = self.question()
        assert question.get_question('example3') == question.questions[1]

    def test_get_data(self):
        assert self.question().get_data(
            {'example2': 'value2', 'example3': 'value3'}
        ) == {'example2': 'value2', 'example3': 'value3'}

    def test_get_data_ignores_own_key(self):
        assert self.question().get_data(
            {'example': 'value', 'example3': 'value3'}
        ) == {'example3': 'value3'}

    def test_form_fields(self):
        assert self.question().form_fields == ['example2', 'example3']

    def test_form_fields_optional_question(self):
        assert self.question(optional=True).form_fields == ['example2', 'example3']

    def test_required_form_fields(self):
        assert self.question().required_form_fields == ['example2', 'example3']

    def test_required_form_fields_optional_nested_question(self):
        question = self.question(questions=[
            {
                "id": "example2",
                "type": "text",
                "optional": False,
            },
            {
                "id": "example3",
                "type": "text",
                "optional": True,
            }
        ])
        assert question.required_form_fields == ['example2']

    def test_get_question_ids(self):
        assert self.question().get_question_ids() == ['example2', 'example3']

    def test_get_question_ids_by_type(self):
        assert self.question().get_question_ids(type='number') == ['example3']

    def test_nested_question_fields_are_templated(self):
        question = self.question(
            questions=[{
                "id": "example2",
                "type": "text",
                "question": TemplateField("Question {{ name }}")
            }]
        ).filter(self.context({
            "name": "one",
        }))

        assert question.get_question('example2').question == "Question one"

    def test_nested_question_followup_get_data(self):
        question = self.question(questions=[
            {
                "id": "lead",
                "type": "boolean",
                "followup": {"follow": [True]}
            },
            {
                "id": "follow",
                "type": "text",
            }
        ])

        assert question.get_data({'lead': False}) == {'lead': False, 'follow': None}
        assert question.get_data({'lead': True}) == {'lead': True}
        assert question.get_data({'lead': True, 'follow': 'a'}) == {'lead': True, 'follow': 'a'}
        assert question.get_data({'lead': False, 'follow': 'a'}) == {'lead': False, 'follow': None}

    def test_nested_checkboxes_question_followup_get_data(self):
        question = self.question(questions=[
            {
                "id": "lead",
                "type": "checkboxes",
                "options": [
                    {"label": "label1", "value": "yes"},
                    {"label": "label2", "value": "no"},
                    {"label": "label3", "value": "maybe not"},
                    {"label": "label4", "value": "maybe"},
                ],
                "followup": {"follow": ["yes", "maybe"]}
            },
            {
                "id": "follow",
                "type": "text",
            }
        ])

        assert question.get_data(OrderedMultiDict([
            ('lead', 'no'),
            ('lead', 'maybe not'),
        ])) == {'lead': ['no', 'maybe not'], 'follow': None}

        assert question.get_data(OrderedMultiDict([
            ('lead', 'yes'),
            ('lead', 'maybe not'),
        ])) == {'lead': ['yes', 'maybe not']}

        assert question.get_data(OrderedMultiDict([
            ('lead', 'yes'),
            ('lead', 'maybe not'),
            ('follow', 'a')
        ])) == {'lead': ['yes', 'maybe not'], 'follow': 'a'}

        assert question.get_data(OrderedMultiDict([
            ('lead', 'no'),
            ('lead', 'maybe not'),
            ('follow', 'a')
        ])) == {'lead': ['no', 'maybe not'], 'follow': None}


class TestDynamicListQuestion(QuestionTest):
    default_context = {'context': {'field': ['First Need', 'Second Need', 'Third Need', 'Fourth need']}}

    def question(self, **kwargs):
        data = {
            "id": "example",
            "type": "dynamic_list",
            "question": "Dynamic list",
            "dynamic_field": "context.field",
            "questions": [
                {
                    "id": "yesno",
                    "question": TemplateField("{{ item }}-yesno"),
                    "type": "boolean",
                    "followup": {"evidence": [True]}
                },
                {
                    "id": "evidence",
                    "question": TemplateField("{{ item }}-evidence"),
                    "type": "text",
                }
            ]
        }
        data.update(kwargs)

        return ContentQuestion(data)

    def test_get_data_unknown_key(self):
        assert self.question().get_data({'other': 'other value'}) == {'example': []}

    def test_question_filter_expected_context_missing(self):
        question = self.question()
        with pytest.raises(KeyError):
            # might be nice if this raised a more specific exception indicating what you'd done wrong
            question.filter({})

    def test_get_data_malformed_submission_no_context_applied(self):
        question = self.question()  # no context applied
        with pytest.raises(ValueError):
            question.get_data({'yesno': True, 'evidence': 'example evidence'})

    def test_get_data(self):
        # must "filter" to apply context as without it, borkedness
        question = self.question().filter(self.context())
        assert question.get_data({
            'yesno-0': True,
            'evidence-0': 'some evidence',
            'evidence-1': '',
            'yesno-2': False,
            'evidence-2': '',
            'yesno-3': False,
            'evidence-3': 'should be removed'
        }
        ) == {
            'example': [
                {
                    'yesno': True,
                    'evidence': 'some evidence'
                },
                {
                    # missing second example (index 1) on purpose
                },
                {
                    'yesno': False
                },
                {
                    'yesno': False
                }
            ]
        }

        assert question.get_data({
            'evidence-2': '',
            'evidence-1': '',
            'evidence-0': '',
            'evidence-3': ''
        }
        ) == {
            'example': [
                {},
                {},
                {},
                {}
            ]
        }

        assert question.get_data({
            'evidence-2': 'some evidence',
            'evidence-1': '',
            'evidence-0': '',
            'yesno-2': True,
            'evidence-3': ''
        }
        ) == {
            'example': [
                {},
                {},
                {
                    'yesno': True,
                    'evidence': 'some evidence'
                },
                {}
            ]
        }

    def test_unformat_data(self):
        # must "filter" to apply context as without it, borkedness
        question = self.question().filter(self.context())
        data = {
            "example": [
                {'yesno': True, 'evidence': 'my evidence'},
                {},
                {'yesno': False},
                {}
            ],
            "nonDynamicKey": 'data'
        }
        expected = {
            "yesno-0": True,
            "evidence-0": 'my evidence',
            "yesno-2": False,
            "nonDynamicKey": 'data'
        }

        assert question.unformat_data(data) == expected

    def test_get_error_messages_unknown_key(self):
        question = self.question().filter(self.context())
        assert question.get_error_messages({'example1': 'answer_required'}) == {}

    def test_get_error_messages(self):
        """
        Tests that for an 'answer_required' error, the content loader generates a suitable default,
        and that for any other error it produces a generic message, and that the errors
        come back in the right order.
        """
        question = self.question().filter(self.context())

        errors_and_messages = {
            'answer_required': 'You need to answer this question.',
            'some_unknown_error': 'There was a problem with the answer to this question.'
        }

        for error_key, expected_message in errors_and_messages.items():
            ordered_dict = question.get_error_messages({
                'example': [
                    {'field': 'yesno', 'index': 0, 'error': error_key},
                    {'field': 'evidence', 'index': 0, 'error': error_key},
                    {'index': 1, 'error': error_key}
                ]
            })

            errors = list(ordered_dict.items())
            assert errors == [
                ('yesno-0', {
                    'input_name': 'yesno-0',
                    'message': expected_message,
                    'question': u'First Need-yesno'
                }),
                ('evidence-0', {
                    'input_name': 'evidence-0',
                    'message': expected_message,
                    'question': u'First Need-evidence'
                }),
                ('example', {
                    'input_name': 'example',
                    'message': expected_message,
                    'question': 'Dynamic list'
                })
            ]


class TestCheckboxes(QuestionTest):
    def question(self, **kwargs):
        data = {
            "id": "example",
            "type": "checkboxes",
            "options": [
                {"label": "Wrong label", "value": "value", "description": TemplateField("some description"
                                                                                        " [markup](links)")},
                {"label": "Option label", "value": "value1"},
                {"label": "Wrong label", "value": "value2"},
            ]
        }
        data.update(kwargs)

        return ContentQuestion(data)

    def test_get_data(self):
        assert self.question().get_data(
            OrderedMultiDict([('example', 'value1'), ('example', 'value2')])
        ) == {'example': ['value1', 'value2']}

    def test_get_data_unknown_key(self):
        assert self.question().get_data({'other': 'other value'}) == {'example': None}

    def test_get_data_with_assurance(self):
        assert self.question(assuranceApproach='2answers-type1').get_data(
            OrderedMultiDict([('example', 'value1'), ('example', 'value2'), ('example--assurance', 'assurance value')])
        ) == {'example': {'value': ['value1', 'value2'], 'assurance': 'assurance value'}}

    def test_get_data_with_assurance_unknown_key(self):
        assert self.question(assuranceApproach='2answers-type1').get_data({'other': 'value'}) == {'example': {}}

    def test_get_data_with_assurance_only(self):
        assert self.question(assuranceApproach='2answers-type1').get_data(
            {'example--assurance': 'assurance value'}
        ) == {'example': {'assurance': 'assurance value'}}


class TestRadios(TestCheckboxes):
    def question(self, **kwargs):
        data = {
            "id": "example",
            "type": "radios",
            "options": [
                {"label": "Wrong label", "value": "value", "description": TemplateField("some description"
                                                                                        " [markup](links)")},
                {"label": "Option label", "value": "value1"},
                {"label": "Wrong label", "value": "value2"},
            ]
        }
        data.update(kwargs)

        return ContentQuestion(data)

    def test_get_data(self):
        assert self.question().get_data(
            OrderedMultiDict([('example', 'value1')])
        ) == {'example': 'value1'}

    def test_get_data_unknown_key(self):
        assert self.question().get_data({'other': 'other value'}) == {}

    def test_get_data_with_assurance(self):
        assert self.question(assuranceApproach='2answers-type1').get_data(
            OrderedMultiDict([('example', 'value1'), ('example--assurance', 'assurance value')])
        ) == {'example': {'value': 'value1', 'assurance': 'assurance value'}}


class TestCheckboxTree(QuestionTest):
    def question(self, **kwargs):
        data = {
            "id": "example",
            "type": "checkbox_tree",
            "options": [
                {
                    "label": "Parent 1 Label",
                    "value": "value_1",
                    "options": [
                        {
                            "label": "Child 1.1 Label",
                            "value": "value_1_1",
                        },
                        {
                            "label": "Child 1.2 Label",
                            "value": "value_1_2",
                        },
                    ]
                },
                {
                    "label": "Parent 2 Label",
                    "value": "value_2",
                    "options": [
                        {
                            "label": "Child 2.1 Label",
                            "value": "value_2_1",
                        },
                    ]
                },
                {
                    "label": "Parent 3 Label",
                    "value": "value_3",
                },
            ]
        }
        data.update(kwargs)

        return ContentQuestion(data)

    def test_get_data(self):
        assert self.question().get_data(
            OrderedMultiDict([('example', 'value_1_1'), ('example', 'value_2_1')])
        ) == {'example': ['value_1_1', 'value_2_1']}

    def test_get_data_unknown_key(self):
        assert self.question().get_data({'other': 'other value'}) == {'example': None}


class QuestionSummaryTest(object):
    def test_value_missing(self):
        question = self.question().summary({})
        assert question.value == ''

    def test_answer_required_value_missing(self):
        question = self.question().summary({})
        assert question.answer_required

    def test_answer_required_optional_question(self):
        question = self.question(optional=True).summary({})
        assert not question.answer_required

    def test_is_empty_value_missing(self):
        question = self.question().summary({})
        assert question.is_empty

    def test_is_empty_optional_question(self):
        question = self.question(optional=True).summary({})
        assert question.is_empty


class TestDateSummary(QuestionSummaryTest):

    def question(self, **kwargs):
        data = {
            "id": "example",
            "type": "date"
        }
        data.update(kwargs)

        return ContentQuestion(data)

    def test_invalid_string(self):
        non_date_string = 'not-a-date-formatted-string'
        question = self.question().summary({'example': non_date_string})

        assert question.value == ''+non_date_string


class TestTextSummary(QuestionSummaryTest):
    def question(self, **kwargs):
        data = {
            "id": "example",
            "type": "text"
        }
        data.update(kwargs)

        return ContentQuestion(data)

    def test_value(self):
        question = self.question().summary({'example': 'textvalue'})
        assert question.value == 'textvalue'

    def test_value_empty(self):
        question = self.question().summary({'example': ''})
        assert question.value == ''

    def test_answer_required(self):
        question = self.question().summary({'example': 'value1'})
        assert not question.answer_required

    def test_is_empty(self):
        question = self.question().summary({'example': 'value1'})
        assert not question.is_empty


class TestRadiosSummary(TestTextSummary):
    def question(self, **kwargs):
        data = {
            "id": "example",
            "type": "radios",
            "options": [
                {"label": "Wrong label", "value": "value"},
                {"label": "Option label", "value": "value1"},
                {"label": "Other label", "value": "value2"},
            ]
        }
        data.update(kwargs)

        return ContentQuestion(data)

    def test_value_returns_matching_option_label(self):
        question = self.question().summary({'example': 'value1'})
        assert question.value == 'Option label'


class TestCheckboxesSummary(QuestionSummaryTest):
    def question(self, **kwargs):
        data = {
            "id": "example",
            "type": "checkboxes",
            "options": [
                {"label": "Wrong label", "value": "value"},
                {"label": "Option label", "value": "value1"},
                {"label": "Other label", "value": "value2"},
            ]
        }
        data.update(kwargs)

        return ContentQuestion(data)

    def test_value(self):
        question = self.question().summary({'example': ['value1', 'value2']})
        assert question.value == ['Option label', 'Other label']

    def test_value_with_assurance(self):
        question = self.question(assuranceApproach='2answers-type1').summary(
            {'example': {'assurance': 'assurance value', 'value': ['value1', 'value2']}}
        )
        assert question.value == ['Option label', 'Other label']

    def test_value_with_before_summary_value(self):
        question = self.question(before_summary_value=['value0']).summary({'example': ['value1', 'value2']})
        assert question.value == ['value0', 'Option label', 'Other label']

    def test_value_with_before_summary_value_if_empty(self):
        question = self.question(before_summary_value=['value0']).summary({})
        assert question.value == ['value0']


class TestCheckboxTreeSummary(QuestionSummaryTest):
    def question(self, **kwargs):
        data = {
            "id": "example",
            "type": "checkbox_tree",
            "options": [
                {
                    "label": "Option 1",
                    "value": "val1",
                    "options": [
                        {"label": "Option 1.1", "value": "val1.1"},
                        {"label": "Option 1.2", "value": "val1.2"},
                    ]
                },
                {
                    "label": "Option 2",
                    "value": "val2",
                    "options": [
                        {"label": "Option 2.1", "value": "val2.1"},
                        {"label": "Option 2.2", "value": "val2.2"},
                    ]
                },

                {"label": "Option 3", "value": "val3"},
                {"label": "Option 4", "value": "val4"},
            ]
        }
        data.update(kwargs)

        return ContentQuestion(data)

    def test_value(self):
        question = self.question().summary({'example': ['val1.1', 'val2.2', 'val4']})
        assert question.value == [
                {
                    "label": "Option 1",
                    "value": "val1",
                    "options": [
                        {"label": "Option 1.1", "value": "val1.1", "options": []},
                    ]
                },
                {
                    "label": "Option 2",
                    "value": "val2",
                    "options": [
                        {"label": "Option 2.2", "value": "val2.2", "options": []},
                    ]
                },

                {"label": "Option 4", "value": "val4", "options": []},
            ]

    def test_value_missing(self):
        question = self.question().summary({})
        assert question.value == []


class TestNumberSummary(QuestionSummaryTest):
    def question(self, **kwargs):
        data = {
            "id": "example",
            "type": "number",
        }
        data.update(kwargs)

        return ContentQuestion(data)

    def test_value(self):
        question = self.question().summary({'example': 23.41})
        assert question.value == 23.41

    def test_value_zero(self):
        question = self.question().summary({'example': 0})
        assert question.value == 0

    def test_value_without_unit(self):
        question = self.question().summary({'example': '12.20'})
        assert question.value == '12.20'

    def test_value_adds_unit_before(self):
        question = self.question(unit=u"£", unit_position="before").summary({'example': '12.20'})
        assert question.value == u'£12.20'

    def test_value_adds_unit_after(self):
        question = self.question(unit=u"£", unit_position="after").summary({'example': '12.20'})
        assert question.value == u'12.20£'

    def test_value_doesnt_add_unit_if_value_is_empty(self):
        question = self.question(unit=u"£", unit_position="after").summary({})
        assert question.value == u''

    def test_value_adds_unit_for_questions_with_assertion(self):
        question = self.question(unit=u"£", unit_position="after", assuranceApproach="2answers-type1").summary({
            'example': {'value': 15,  'assurance': 'Service provider assertion'}
        })
        assert question.value == u'15£'

    def test_answer_required(self):
        question = self.question().summary({'example': 0})
        assert not question.answer_required

    def test_is_empty(self):
        question = self.question().summary({'example': 0})
        assert not question.is_empty


class TestPricingSummary(QuestionSummaryTest):
    def question(self, **kwargs):
        data = {
            "id": "example",
            "type": "pricing",
            "fields": {
                "price": "price",
                "minimum_price": "priceMin",
                "maximum_price": "priceMax",
                "price_unit": "priceUnit",
                "price_interval": "priceInterval",
                "hours_for_price": "priceHours",
            }
        }
        data.update(kwargs)

        return ContentQuestion(data)

    def test_value(self):
        question = self.question().summary({'priceMin': '20.41', 'priceMax': '25.00'})
        assert question.value == u'£20.41 to £25.00'

    def test_value_without_price_min(self):
        question = self.question().summary({'priceMax': '25.00'})
        assert question.value == ''

    def test_value_price_field(self):
        question = self.question().summary({'price': '20.41'})
        assert question.value == u'£20.41'

    def test_value_without_price_max(self):
        question = self.question().summary({'priceMin': '20.41'})
        assert question.value == u'£20.41'

    def test_value_with_hours_for_price(self):
        question = self.question().summary({'priceMin': '20.41', 'priceHours': '8'})
        assert question.value == u'8 for £20.41'

    def test_value_with_unit(self):
        question = self.question().summary({'priceMin': '20.41', 'priceMax': '25.00', 'priceUnit': 'service'})
        assert question.value == u'£20.41 to £25.00 per service'

    def test_value_with_interval(self):
        question = self.question().summary({'priceMin': '20.41', 'priceMax': '25.00', 'priceInterval': 'day'})
        assert question.value == u'£20.41 to £25.00 per day'

    def test_value_with_unit_and_interval(self):
        question = self.question().summary(
            {'priceMin': '20.41', 'priceMax': '25.00', 'priceUnit': 'service', 'priceInterval': 'day'}
        )
        assert question.value == u'£20.41 to £25.00 per service per day'


class TestMultiquestionSummary(QuestionSummaryTest):
    def question(self, **kwargs):
        data = {
            "id": "example",
            "type": "multiquestion",
            "questions": [
                {
                    "id": "example2",
                    "type": "text",
                },
                {
                    "id": "example3",
                    "type": "number",
                }
            ]
        }
        data.update(kwargs)

        return ContentQuestion(data)

    def question_with_followups(self, **kwargs):
        data = {
            "id": "q1",
            "type": "multiquestion",
            "questions": [
                {"id": "q2", "type": "text"},
                {"id": "q3", "type": "boolean", "followup": {"q4": [True], "q5": [True]}},
                {"id": "q4", "type": "text", "optional": True},
                {"id": "q5", "type": "radios", "options": [{"label": "one"}, {"label": "two"}],
                 "followup": {"q6": ["one"], "q7": ["one"]}},
                {"id": "q6", "type": "text"},
                {"id": "q7", "type": "text", "optional": True}
            ]
        }
        data.update(kwargs)

        return ContentQuestion(data)

    def test_value(self):
        question = self.question().summary({'example2': 'value2', 'example3': 'value3'})
        assert question.value == question.questions

    def test_value_missing(self):
        question = self.question().summary({})
        assert question.value == []

    def test_answer_required(self):
        question = self.question().summary({'example2': 'value2', 'example3': 'value3'})
        assert not question.answer_required

    def test_is_empty(self):
        question = self.question().summary({'example': 'value2', 'example3': 'value3'})
        assert not question.is_empty

    def test_answer_required_partial(self):
        question = self.question().summary({'example3': 'value3'})
        assert question.answer_required

    def test_is_empty_partial(self):
        question = self.question().summary({'example2': 'value2'})
        assert not question.is_empty

    def test_answer_required_if_question_with_followups_not_answered(self):
        question = self.question_with_followups().summary({'q2': 'blah'})
        assert question.answer_required

    def test_answer_required_if_followup_not_answered(self):
        question = self.question_with_followups().summary({'q2': 'blah', 'q3': True})
        assert question.answer_required

    def test_answer_not_required_if_followups_not_required(self):
        question = self.question_with_followups().summary({'q2': 'blah', 'q3': False})
        assert not question.answer_required

    def test_answer_required_if_followups_to_followup_not_answered(self):
        question = self.question_with_followups().summary({'q2': 'blah', 'q3': True, 'q5': 'one'})
        assert question.answer_required

    def test_answer_not_required_if_followups_to_followup_not_required(self):
        question = self.question_with_followups().summary({'q2': 'blah', 'q3': True, 'q5': 'two'})
        assert not question.answer_required

    def test_answer_not_required_if_optional_followups_not_answered(self):
        question = self.question_with_followups().summary({'q2': 'blah', 'q3': True, 'q5': 'one', 'q6': 'blah'})
        assert not question.answer_required


class TestDynamicListSummary(QuestionSummaryTest):
    def question(self, **kwargs):
        data = {
            "id": "example",
            "type": "dynamic_list",
            "question": "Dynamic list",
            "dynamic_field": "context.field",
            "questions": [
                {
                    "id": "example2",
                    "question": TemplateField("{{ item }}-2"),
                    "type": "text",
                },
                {
                    "id": "example3",
                    "question": TemplateField("{{ item }}-3"),
                    "type": "number",
                }
            ]
        }
        data.update(kwargs)

        return ContentQuestion(data).filter({'context': {'field': ['First Need', 'Second Need', 'Third Need']}})

    def test_value_missing(self):
        question = self.question().summary({})
        assert question.value == []
