"""Operações explícitas: somente recursos iniciais confirmados, sem eval."""
import secrets

ATTRIBUTES = ('FOR', 'AGI', 'VIG', 'PRE', 'INT')
SOURCE_HASH = '35233f337911babbb8814687c7729cf6da3649fa58acd64f4ff82868baebdd42'
ARCHETYPES = [
    {'id': 'guerreiro', 'name': 'Guerreiro', 'role': 'Resistência e combate corpo a corpo', 'pv': 20, 'pe': 3, 'san': 12,
     'initial': 'Corpo Fortalecido', 'trails': ['Escudo', 'Lança', 'Espada', 'Armadura'], 'paragraph': 631},
    {'id': 'lutador', 'name': 'Lutador', 'role': 'Agilidade, reflexos e mobilidade', 'pv': 16, 'pe': 4, 'san': 12,
     'initial': 'Iniciativa aprimorada', 'trails': ['Perseverança', 'Foco', 'Coragem', 'Justiça'], 'paragraph': 676},
    {'id': 'sensitivo', 'name': 'Sensitivo', 'role': 'Percepção e ataques à distância', 'pv': 12, 'pe': 3, 'san': 12,
     'initial': 'Calma Sensitiva', 'trails': ['Tato', 'Visão', 'Audição', 'Olfato'], 'paragraph': 719},
    {'id': 'suporte', 'name': 'Suporte', 'role': 'Auxílio, cura e apoio moral', 'pv': 10, 'pe': 4, 'san': 15,
     'initial': 'Auxílio Positivo', 'trails': ['Clérigo', 'Druida', 'Bardo', 'Monge'], 'paragraph': 763},
]
CLASSES = [
    {'id': 'samurai', 'name': 'Samurai', 'skill': 'Luta'},
    {'id': 'esgrimista', 'name': 'Esgrimista', 'skill': 'Luta'},
    {'id': 'shinobi', 'name': 'Shinobi', 'skill': 'Furtividade'},
    {'id': 'atirador', 'name': 'Atirador', 'skill': 'Pontaria'},
    {'id': 'hunter', 'name': 'Hunter', 'skill': 'Atletismo'},
    {'id': 'pugilista', 'name': 'Pugilista', 'skill': 'Luta'},
    {'id': 'medico', 'name': 'Médico de Campo', 'skill': 'Medicina'},
]
PENDING = {
    'R06': 'Definir perícia principal, duplicatas e graus de treino.',
    'R08': 'Confirmar elegibilidade de respiração e arte sanguínea.',
    'R09': 'Definir limite racial e exigência de distribuir todos os pontos.',
}
DEFAULT_CATALOG = {'archetypes': ARCHETYPES, 'classes': CLASSES, 'races': [], 'skills': [], 'techniques': [],
                   'status': 'validation', 'level': 1, 'sourceDocument': 'Ao Cair da Noite.docx'}


def calculate(data, decisions=None):
    decisions = decisions or {}
    errors, warnings, pending, explanations = [], [], [], []
    attributes = data.get('attributes', {})
    values = [attributes.get(key) for key in ATTRIBUTES]
    valid = all(type(value) is int and 0 <= value <= 3 for value in values)
    if not valid:
        errors.append('Informe os cinco atributos base como inteiros de 0 a 3. Ausente não equivale a zero.')
    elif sum(values) > 9:
        errors.append('A distribuição base excede 9 pontos.')
    elif sum(values) < 9:
        warnings.append(f'Faltam {9 - sum(values)} pontos na distribuição base.')
        if decisions.get('R09', {}).get('spendAll', True):
            pending.append({'id': 'ATTR', 'message': 'Complete a distribuição de atributos antes da aprovação.'})
    for rule, message in PENDING.items():
        if rule not in decisions:
            pending.append({'id': rule, 'message': message})
    if not data.get('race'):
        pending.append({'id': 'RACE', 'message': 'Informe a raça para revisão.'})
    if data.get('race') and not decisions.get('RACE', {}).get('validated'):
        pending.append({'id': 'RACE', 'message': 'Raça e benefícios precisam de validação do mestre; nenhum bônus automático.'})
    if data.get('classId') not in {x['id'] for x in CLASSES}:
        pending.append({'id': 'CLASS', 'message': 'Escolha uma classe.'})
    if not data.get('name', '').strip():
        pending.append({'id': 'NAME', 'message': 'Informe o nome do personagem.'})
    archetype = next((x for x in ARCHETYPES if x['id'] == data.get('archetypeId')), None)
    maxima = {'pv': None, 'pe': None, 'san': None}
    if not archetype:
        pending.append({'id': 'ARCHETYPE', 'message': 'Escolha um arquétipo.'})
    elif valid:
        maxima = {'pv': archetype['pv'] + attributes['VIG'], 'pe': archetype['pe'] + attributes['PRE'], 'san': archetype['san']}
        for field, formula, inputs in [('pv', f"{archetype['pv']} + VIG", {'VIG': attributes['VIG']}),
                                       ('pe', f"{archetype['pe']} + PRE", {'PRE': attributes['PRE']}),
                                       ('san', str(archetype['san']), {})]:
            explanations.append({'field': field, 'value': maxima[field], 'formula': formula, 'inputs': inputs,
                'sourceDocument': 'Ao Cair da Noite.docx', 'sourceSection': archetype['name'],
                'paragraph': archetype['paragraph'], 'sourceSha256': SOURCE_HASH})
    if data.get('classId') == 'atirador' and data.get('techniqueKind') == 'respiracao':
        if not decisions.get('ATIRADOR', {}).get('allowRespiration'):
            pending.append({'id': 'ATIRADOR', 'message': 'Atirador não utiliza respiração; exige exceção explícita do mestre.'})
    if data.get('techniques') and not decisions.get('TECHNIQUES', {}).get('validated'):
        pending.append({'id': 'TECHNIQUES', 'message': 'Conferir requisitos e efeitos das técnicas registradas.'})
    warnings.append('Defesa, deslocamento e evolução ainda não são calculados. Recursos não incluem benefícios raciais não validados.')
    return {'maxima': maxima, 'errors': errors, 'warnings': warnings, 'pending': pending,
            'explanations': explanations, 'canApprove': not errors and not pending, 'level': 1}


def roll_attribute(value, faces=None):
    if type(value) is not int or not 0 <= value <= 3:
        raise ValueError('Atributo precisa ser um inteiro de 0 a 3.')
    count = 2 if value == 0 else value
    faces = faces if faces is not None else [secrets.randbelow(20) + 1 for _ in range(count)]
    if len(faces) != count or any(type(n) is not int or not 1 <= n <= 20 for n in faces):
        raise ValueError('Faces inválidas.')
    return {'faces': faces, 'result': min(faces) if value == 0 else max(faces),
            'mode': 'menor' if value == 0 else 'maior', 'source': 'Decisão do mestre • 08/10/2026' if value == 0 else 'Sistema de Dados/Estatísticas',
            'note': 'Resultado bruto; treinamento e vantagem/desvantagem ainda aguardam definição.'}
