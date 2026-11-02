"""Step definitions – Épico 4: Associação Pessoa x EPI (US-008, US-009)."""
from behave import given, then
from features.steps.shared_steps import mock_frame

try:
    from src.association.associator import PPEAssociator
except ImportError:
    PPEAssociator = None


def _make_person(person_id, bbox):
    """Cria objeto pessoa stub para testes."""
    from types import SimpleNamespace
    return SimpleNamespace(track_id=person_id, bbox=bbox, has_helmet=False, has_vest=False)


def _make_detection(class_name, bbox, person_id=None):
    """Cria objeto detecção stub para testes."""
    from types import SimpleNamespace
    return SimpleNamespace(class_name=class_name, bbox=bbox, person_id=person_id)


# ── US-008: Associar capacete a uma pessoa ────────────────────────────────
# When 'o sistema realiza a associação de EPIs' → shared_steps.py

@given('que um quadro contém uma pessoa com capacete sobre a cabeça')
def step_person_with_helmet_on_head(context):
    assert PPEAssociator is not None, \
        "Implemente src.association.associator.PPEAssociator"
    context.associator = PPEAssociator()
    # pessoa ocupando região central; capacete no terço superior da bbox da pessoa
    context.persons = [_make_person(1, bbox=(100, 100, 200, 400))]
    context.ppe_detections = [_make_detection('helmet', bbox=(110, 90, 190, 150))]

@given('que um quadro contém "{n}" pessoas próximas, onde apenas uma usa capacete')
def step_two_persons_one_helmet(context, n):
    assert PPEAssociator is not None, \
        "Implemente src.association.associator.PPEAssociator"
    context.associator = PPEAssociator()
    context.person_count = int(n)
    # pessoa 1 com capacete, pessoa 2 sem
    context.persons = [
        _make_person(1, bbox=(50,  100, 150, 400)),
        _make_person(2, bbox=(160, 100, 260, 400)),
    ]
    context.ppe_detections = [_make_detection('helmet', bbox=(60, 90, 140, 150))]

@then('o capacete é associado à pessoa cuja região da cabeça está imediatamente abaixo')
def step_helmet_associated_to_head(context):
    assoc = context.associations
    assert 1 in assoc, "Pessoa 1 deve ter associação com capacete"
    assert 'helmet' in assoc[1], \
        "Associação da pessoa 1 deve incluir capacete"

@then('o capacete é associado apenas à pessoa que o está utilizando')
def step_helmet_only_one_person(context):
    assoc = context.associations
    persons_with_helmet = [pid for pid, epis in assoc.items() if 'helmet' in epis]
    assert len(persons_with_helmet) == 1, (
        f"Exatamente 1 pessoa deve ter capacete associado, "
        f"mas {len(persons_with_helmet)} foram encontradas: {persons_with_helmet}"
    )

@then('a segunda pessoa é identificada como sem capacete')
def step_second_person_no_helmet(context):
    assoc = context.associations
    persons_without_helmet = [pid for pid, epis in assoc.items() if 'helmet' not in epis]
    assert 2 in persons_without_helmet, \
        "Pessoa 2 deve estar identificada como sem capacete"


# ── US-009: Associar colete a uma pessoa ──────────────────────────────────

@given('que um quadro contém uma pessoa com colete na região do tronco')
def step_person_with_vest_on_torso(context):
    assert PPEAssociator is not None, \
        "Implemente src.association.associator.PPEAssociator"
    context.associator = PPEAssociator()
    context.persons = [_make_person(1, bbox=(100, 100, 200, 400))]
    # colete na região do tronco (meio da bbox da pessoa)
    context.ppe_detections = [_make_detection('vest', bbox=(105, 180, 195, 320))]

@given('que um quadro contém "{n}" pessoas próximas, onde apenas uma usa colete')
def step_two_persons_one_vest(context, n):
    assert PPEAssociator is not None, \
        "Implemente src.association.associator.PPEAssociator"
    context.associator = PPEAssociator()
    context.person_count = int(n)
    context.persons = [
        _make_person(1, bbox=(50,  100, 150, 400)),
        _make_person(2, bbox=(160, 100, 260, 400)),
    ]
    context.ppe_detections = [_make_detection('vest', bbox=(55, 180, 145, 320))]

@then('o colete é associado à pessoa cuja região do tronco está sobreposta ao colete detectado')
def step_vest_associated_to_torso(context):
    assoc = context.associations
    assert 1 in assoc, "Pessoa 1 deve ter associação com colete"
    assert 'vest' in assoc[1], "Associação da pessoa 1 deve incluir colete"

@then('o colete é associado apenas à pessoa que o está utilizando')
def step_vest_only_one_person(context):
    assoc = context.associations
    persons_with_vest = [pid for pid, epis in assoc.items() if 'vest' in epis]
    assert len(persons_with_vest) == 1, (
        f"Exatamente 1 pessoa deve ter colete associado, "
        f"mas {len(persons_with_vest)} foram encontradas: {persons_with_vest}"
    )

@then('a segunda pessoa é identificada como sem colete')
def step_second_person_no_vest(context):
    assoc = context.associations
    persons_without_vest = [pid for pid, epis in assoc.items() if 'vest' not in epis]
    assert 2 in persons_without_vest, \
        "Pessoa 2 deve estar identificada como sem colete"
