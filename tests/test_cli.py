import pytest

from travelplanner.cli import main


def test_cli_route_with_interests_prints_plan(capsys):
    assert main(["--route", "tokyo:1,kyoto:1", "--age", "adult",
                 "--interests", "temple", "--data", "data/japan_travel_dataset.json"]) == 0
    output = capsys.readouterr().out
    assert "Japan Travel Planner" in output
    assert "Total value:" in output
    assert "Transfer: Tokyo -> Kyoto" in output


def test_cli_single_city_and_greedy(capsys):
    assert main(["--city", "tokyo", "--days", "1", "--age", "adult",
                 "--algorithm", "greedy"]) == 0
    assert "algorithm: Greedy" in capsys.readouterr().out


def test_cli_single_city_matches_equivalent_route(capsys):
    assert main(["--city", "tokyo", "--days", "2", "--age", "adult"]) == 0
    single_city = capsys.readouterr().out
    assert main(["--route", "tokyo:2", "--age", "adult"]) == 0
    route = capsys.readouterr().out
    assert single_city == route


def test_cli_reports_bad_input_with_exit_code_two(capsys):
    assert main(["--route", "not-a-city:1", "--age", "adult"]) == 2
    assert "Unknown city" in capsys.readouterr().err


def test_cli_requires_city_days_pair():
    with pytest.raises(SystemExit) as error:
        main(["--city", "tokyo", "--age", "adult"])
    assert error.value.code == 2
