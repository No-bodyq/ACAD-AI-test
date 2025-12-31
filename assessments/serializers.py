from rest_framework import serializers
from .models import Exam, Question, Submission, Answer


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ("__all__")


class ExamSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Exam
        fields = ("id", "title", "duration_minutes", "course", "metadata", "questions")


class AnswerSubmissionSerializer(serializers.Serializer):
    question = serializers.IntegerField()
    answer_text = serializers.CharField(allow_blank=True, required=False)
    selected_choice = serializers.CharField(allow_blank=True, required=False)


class SubmissionCreateSerializer(serializers.Serializer):
    exam = serializers.IntegerField()
    answers = AnswerSubmissionSerializer(many=True)

    def validate(self, data):
        exam_id = data.get("exam")
        answers = data.get("answers", [])

        try:
            exam = Exam.objects.get(pk=exam_id)
        except Exam.DoesNotExist:
            raise serializers.ValidationError({"exam": "Exam does not exist."})

        if not answers:
            raise serializers.ValidationError({"answers": "At least one answer is required."})

        # collect provided question references and check duplicates
        provided_refs = [a.get("question") for a in answers]
        if None in provided_refs:
            raise serializers.ValidationError({"answers": "Each answer must include a question id or order index."})
        if len(provided_refs) != len(set(provided_refs)):
            raise serializers.ValidationError({"answers": "Duplicate question references in answers are not allowed."})

        # fetch all questions for this exam to validate membership and allow order-based referencing
        all_qs = list(Question.objects.filter(exam=exam).order_by("order", "id"))
        if not all_qs:
            raise serializers.ValidationError({"exam": "Exam has no questions."})

        # build id and order maps
        id_map = {q.id: q for q in all_qs}
        order_map = {}
        if any(getattr(q, "order", None) is not None for q in all_qs):
            for q in all_qs:
                try:
                    order_map[int(q.order)] = q
                except Exception:
                    continue
        else:
            for idx, q in enumerate(all_qs, start=1):
                order_map[idx] = q

        # per-answer validation
        resolved_map = {}
        for idx, ans in enumerate(answers):
            qref = ans.get("question")
            question = None

            # try to interpret the provided reference as an int (either id or order)
            try:
                qnum = int(qref)
            except Exception:
                qnum = None

            if qnum is not None and qnum in order_map:
                question = order_map[qnum]
                # normalize the answer to use the canonical question id
                ans["question"] = question.id
            else:
                raise serializers.ValidationError({f"answers[{idx}]": f"Question reference '{qref}' is invalid for this exam. Provide its order index."})

            # validate content depending on question type
            selected_choice = ans.get("selected_choice", "")
            answer_text = ans.get("answer_text", "")

            choices_field = getattr(question, "choices", None)
            if choices_field:
                # normalize choices into keys
                keys = []
                if isinstance(choices_field, (list, tuple)):
                    for c in choices_field:
                        if isinstance(c, dict):
                            k = c.get("key") or c.get("id") or c.get("value")
                            if k is None:
                                # fallback to text or stringify
                                k = c.get("text") if isinstance(c.get("text"), str) else str(c)
                        else:
                            s = str(c)
                            if ":" in s:
                                k = s.split(":", 1)[0].strip()
                            else:
                                k = s.strip()
                        keys.append(str(k))
                else:
                    keys = [c.strip() for c in str(choices_field).split(",") if c.strip()]

                if not selected_choice:
                    raise serializers.ValidationError({f"answers[{idx}]": "selected_choice is required for choice questions."})
                if str(selected_choice) not in keys:
                    raise serializers.ValidationError({f"answers[{idx}]": f"selected_choice '{selected_choice}' is not valid for question {question.id}. choices: {keys}"})
            else:
                if not answer_text:
                    raise serializers.ValidationError({f"answers[{idx}]": "answer_text is required for open-ended questions."})

            resolved_map[question.id] = question

        # attach fetched instances for use in create() if needed
        data["exam_instance"] = exam
        data["question_map"] = resolved_map

        return data


class AnswerSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)

    class Meta:
        model = Answer
        fields = ("id", "question", "answer_text", "selected_choice", "points_awarded")


class SubmissionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    student = serializers.StringRelatedField()
    exam = ExamSerializer(read_only=True)

    class Meta:
        model = Submission
        fields = ("id", "student", "exam", "started_at", "submitted_at", "graded", "grade", "answers")
