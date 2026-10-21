import itertools

from quiniela_ai_studio.domain.streak_statistics import (
    count_profile,
    frequent_profiles,
    historical_figure_recommendations,
    possible_run_figures,
    possible_run_frequency_counts,
    possible_run_length_bounds,
    random_figure_recommendations,
    run_figure,
    run_lengths,
    streak_profile,
)


def test_variants_are_a_joint_count_of_x_and_two_and_ignore_pleno():
    column='1X22X'+'1'*9
    assert count_profile(column)==(4,2,2)


def test_variant_runs_join_x_and_two_and_count_only_maximal_runs():
    column='1XX2211'+'1'*7
    longest,counts=run_lengths(column,'V')
    assert longest==4
    assert counts[3]==1
    assert counts[1]==0
    assert streak_profile('1111'+'X2'*5)[:4]==(4,1,1,10)


def test_frequent_joint_profiles_are_reproducible_and_cover_requested_sample_mass():
    profiles,total=frequent_profiles([(1,0),(1,0),(2,1),(3,2)],.75)
    assert total==4
    assert profiles==((1,0), (2,1))


def test_possible_run_bounds_respect_forced_and_optional_base_signs():
    base=('1','1X','1','X')+('X',)*10
    assert possible_run_length_bounds(base,'1')==(1,3)
    mixed=('X','X2','1','2','XX2','1X2')+('1',)*8
    assert possible_run_length_bounds(mixed,'V')==(2,3)


def test_exact_run_count_and_figure_possibilities_respect_maximal_runs():
    assert possible_run_frequency_counts(('1X2',)*14,'1',2)==tuple(range(6))
    fixed=('11','1')+('X',)*12
    assert possible_run_frequency_counts(fixed,'1',2)==(1,)
    figures=possible_run_figures(('1X2',)*14,'1')
    assert '3-2-1' in figures[6]
    assert '2-2-2' in figures[6]
    assert run_figure('111X11XX1XXXXX','1')=='3-2-1'
    assert run_figure('X2X1X'+'1'*9,'V')=='3-1'



def test_attainable_run_frequencies_and_figures_match_exhaustive_small_base():
    base=('1X','X2','12','1X2','X')+('1',)*9
    columns=tuple(''.join(picks) for picks in itertools.product(*base))
    for sign in ('1','X','2','V'):
        for length in range(2,6):
            expected=sorted({run_lengths(column,sign)[1][length-1] for column in columns})
            assert list(possible_run_frequency_counts(base,sign,length))==expected
        figures={}
        for column in columns:
            figure=run_figure(column,sign)
            total=sum(int(part) for part in figure.split('-')) if figure else 0
            figures.setdefault(total,set()).add(figure)
        assert possible_run_figures(base,sign)=={
            total:tuple(sorted(values,key=lambda figure:tuple(-int(part) for part in figure.split('-')) if figure else ()))
            for total,values in sorted(figures.items())
        }


def test_historical_figure_recommendations_use_observed_attainable_partitions():
    base=('1X2',)*14
    allowed='X22'+'1'+'XX'+'1'+'2'+'1'+'X'+'1'*4
    other='X22X'+'1'+'2X2'+'1'*6
    selections,matched=historical_figure_recommendations((allowed,allowed,other),base,.65)
    assert selections['V']=={7:{'3-2-1-1'}}
    assert matched>=1


def test_random_figure_recommendations_repeat_the_same_seed():
    base=('1X2',)*14
    first=random_figure_recommendations(base,321,.55,80)
    second=random_figure_recommendations(base,321,.55,80)
    assert first==second
    selections,columns=first
    assert len(columns)==80
    assert all(total in possible_run_figures(base,sign) and figures
               for sign,options in selections.items() for total,figures in options.items())
