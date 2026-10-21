import itertools

from quiniela_ai_studio.domain.interruption_statistics import (
    historical_interruption_recommendation,
    interruption_profile,
    possible_interruption_profiles,
    random_interruption_recommendation,
)


def column_from_transition_bits(bits):
    signs=['1']
    for changed in bits:
        signs.append(('X' if signs[-1]=='1' else '1') if changed else signs[-1])
    return ''.join(signs)


def test_manual_examples_count_thirteen_transitions_and_exact_partition():
    assert interruption_profile('11X21221XX121X')==(10,4,'4-4-2')
    assert interruption_profile('12X22X11221111')==(7,3,'3-2-1-1')


def test_dynamic_program_matches_exhaustive_reachability_for_restricted_base():
    base=('1X','X2','12','1X2','1','X2','12','1X','2','1X','12','X','1X2','12')
    exhaustive={interruption_profile(''.join(column)) for column in itertools.product(*base)}
    assert set(possible_interruption_profiles(base))==exhaustive


def test_random_is_seeded_and_historical_recommendation_uses_real_sample():
    base=('1X2',)*14
    first=random_interruption_recommendation(base,903,.55)
    second=random_interruption_recommendation(base,903,.55)
    assert first==second
    columns=('12X22X11221111','11X21221XX121X','1'*14)
    pairs,figures,examined,matched=historical_interruption_recommendation(columns,base,.5)
    assert examined==3 and matched>=2
    assert (7,'3-2-1-1') in figures
    assert any(total==7 and longest==3 for total,longest in pairs)
